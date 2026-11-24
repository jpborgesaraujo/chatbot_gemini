from flask import Flask, render_template, request
from google import genai
from google.genai import errors, types
from dotenv import load_dotenv
import os
from helper import carrega, salva
from time import sleep
from pathlib import Path
from selecionar_persona import selecionar_persona

load_dotenv()

CHAVE_API_GOOGLE = os.getenv("GEMINI_API_KEY")
MODELO_ESCOLHIDO = "gemini-4-hydrogen"
MODELO_ALTERNATIVO = "gemini-3.5-flash-lite"
MAXIMO_TENTATIVAS = 2
INTERVALO_REPETICAO_SEGUNDOS = 50

app = Flask(__name__, template_folder=".")
app.secret_key = 'alura'

contexto = carrega(Path(__file__).resolve().parent / "dados" / "musimart")

def bot(prompt):
    if not CHAVE_API_GOOGLE:
        raise RuntimeError("Defina GEMINI_API_KEY no arquivo .env.")
    if contexto is None:
        raise RuntimeError("Não foi possível carregar o contexto do e-commerce.")

    cliente = genai.Client(api_key=CHAVE_API_GOOGLE)
    
    personalidade = selecionar_persona(prompt)
    prompt_do_sistema = f"""
# PERSONA
{personalidade}

Você é um chatbot de atendimento a clientes de um e-commerce.
Você não deve responder perguntas que não sejam dados do ecommerce informado!
Você deve utilizar apenas dados que estejam dentro do contexto.

# CONTEXTO
{contexto}
"""
    configuracao = types.GenerateContentConfig(
        system_instruction=prompt_do_sistema,
        temperature=0.1,
        max_output_tokens=8192,
    )
    modelos = (MODELO_ESCOLHIDO, MODELO_ALTERNATIVO)
    modelos_tentados = modelos[:MAXIMO_TENTATIVAS]
    for tentativa, modelo in enumerate(modelos_tentados):
        try:
            resposta = cliente.models.generate_content(
                model=modelo,
                contents=prompt,
                config=configuracao,
            )
            break
        except errors.ServerError as erro:
            if erro.code != 503 or tentativa + 1 >= len(modelos_tentados):
                raise
            proximo_modelo = modelos_tentados[tentativa + 1]
            app.logger.warning(
                "Modelo %s indisponível; aguardando %s segundos antes de tentar %s.",
                modelo,
                INTERVALO_REPETICAO_SEGUNDOS,
                proximo_modelo,
            )
            sleep(INTERVALO_REPETICAO_SEGUNDOS)
    if not resposta.text:
        raise RuntimeError("O Gemini não retornou uma resposta de texto.")
    return resposta.text


@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json(silent=True)
    prompt = dados.get("msg") if isinstance(dados, dict) else None
    if not isinstance(prompt, str) or not prompt.strip():
        return "Envie uma mensagem válida no campo 'msg'.", 400

    try:
        return bot(prompt)
    except RuntimeError as erro:
        return str(erro), 503
    except errors.APIError as erro:
        app.logger.exception("Falha ao consultar a API do Gemini.")
        if erro.code == 503:
            return "O Gemini está com alta demanda. Tente novamente em alguns instantes.", 503
        if erro.code == 429:
            return "Limite de solicitações do Gemini atingido. Aguarde e tente novamente.", 429
        return f"Falha ao consultar o Gemini (HTTP {erro.code}).", 502

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)

