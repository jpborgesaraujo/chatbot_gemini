const chat = document.querySelector("#chat");
const input = document.querySelector("#input");
const botaoEnviar = document.querySelector("#botao-enviar");

function criarBolha(classe, texto) {
    const bolha = document.createElement("p");
    bolha.className = `chat__bolha ${classe}`;
    bolha.textContent = texto;
    chat.appendChild(bolha);
    chat.scrollTop = chat.scrollHeight;
    return bolha;
}

async function enviarMensagem() {
    const mensagem = input.value.trim();
    if (!mensagem) return;

    input.value = "";
    criarBolha("chat__bolha--usuario", mensagem);
    const respostaBot = criarBolha("chat__bolha--bot", "Analisando...");
    botaoEnviar.disabled = true;

    try {
        const resposta = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ msg: mensagem }),
        });
        const texto = await resposta.text();
        respostaBot.textContent = resposta.ok
            ? texto
            : `Erro (${resposta.status}): ${texto}`;
    } catch (erro) {
        respostaBot.textContent = "Não foi possível conectar ao servidor.";
    } finally {
        botaoEnviar.disabled = false;
        input.focus();
        chat.scrollTop = chat.scrollHeight;
    }
}

botaoEnviar.addEventListener("click", enviarMensagem);
input.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") {
        evento.preventDefault();
        enviarMensagem();
    }
});
