let arquivoA = null;
let arquivoB = null;

window.acionarInput = (num) => document.getElementById(`file-input-${num}`).click();

window.prepararArquivo = (input, num) => {
    const file = input.files[0];
    if (!file) return;
    num === 1 ? arquivoA = file : arquivoB = file;
    document.getElementById(num === 1 ? 'output-a' : 'output-b').innerHTML = 
        `<strong>Arquivo:</strong> ${file.name}<br><small>Pronto para análise.</small>`;
};

window.resetarSistema = function() {
    arquivoA = null;
    arquivoB = null;
    document.getElementById('file-input-1').value = "";
    document.getElementById('file-input-2').value = "";
    document.getElementById('progress-bar').style.strokeDashoffset = 326.7;
    document.getElementById('percent-text').innerText = "0%";
    document.getElementById('output-a').innerHTML = "Aguardando...";
    document.getElementById('output-b').innerHTML = "Aguardando...";
    document.getElementById('veredito-container').style.display = 'none';
    const btn = document.getElementById('btn-start');
    btn.disabled = false;
    btn.innerText = "Iniciar Análise";
};

window.iniciarAnalise = async () => {
    const btn = document.getElementById('btn-start');
    const progressBar = document.getElementById('progress-bar');
    const percentText = document.getElementById('percent-text');
    const card = document.getElementById('veredito-container');

    if (!arquivoA || !arquivoB) return alert("Selecione os dois arquivos.");

    btn.disabled = true;
    btn.innerText = "Analisando...";
    card.style.display = 'none';

    const formData = new FormData();
    formData.append('file1', arquivoA);
    formData.append('file2', arquivoB);

    try {
        const response = await fetch('/analisar_documentos', { method: 'POST', body: formData });
        const dados = await response.json();
        
        let visual = 0;
        const final = Math.floor(dados.percentual);

        const animacao = setInterval(() => {
            if (final === 0) {
                clearInterval(animacao);
                percentText.innerText = "0%";
                finalizarAnalise(dados, card, btn);
                return;
            }
            visual++;
            const offset = 326.7 - (visual / 100) * 326.7;
            progressBar.style.strokeDashoffset = offset;
            percentText.innerText = visual + "%";

            if (visual >= final) {
                clearInterval(animacao);
                finalizarAnalise(dados, card, btn);
            }
        }, 10);
    } catch (e) {
        alert("Erro no servidor.");
        btn.disabled = false;
        btn.innerText = "Iniciar Análise";
    }
};

function finalizarAnalise(dados, card, btn) {
    btn.disabled = false;
    btn.innerText = "Concluído";
    document.getElementById('output-a').innerHTML = dados.texto_grifado_a;
    document.getElementById('output-b').innerHTML = dados.texto_grifado_b;
    exibirVeredito(dados.percentual, card);
}

function exibirVeredito(valor, card) {
    const status = document.getElementById('veredito-status');
    const msg = document.getElementById('veredito-mensagem');
    card.classList.remove('status-baixo', 'status-medio', 'status-alto');
    card.style.display = 'block';

    if (valor >= 70) {
        card.classList.add('status-alto');
        status.innerText = "ALTO RISCO DE PLÁGIO";
        msg.innerText = `Similaridade crítica (${valor}%). Conteúdo com evidências de cópia direta.`;
    } else if (valor >= 21) {
        card.classList.add('status-medio');
        status.innerText = "PARÁFRASE IDENTIFICADA";
        msg.innerText = `Similaridade moderada (${valor}%). Requer revisão técnica pelo avaliador para validar citações.`;
    } else {
        card.classList.add('status-baixo');
        status.innerText = "TEXTO ORIGINAL";
        msg.innerText = `Baixa similaridade (${valor}%). Texto dentro dos padrões de originalidade.`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-start').addEventListener('click', iniciarAnalise);
});