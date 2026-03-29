# =============================================================================
# main.py — Backend da Ferramenta de Detecção de Plágio
# =============================================================================
# Descrição:
#   API REST construída com FastAPI que recebe dois documentos (PDF, DOCX ou TXT),
#   extrai seus textos e calcula o grau de similaridade entre eles utilizando
#   a técnica TF-IDF combinada com similaridade de cosseno.
#
# Técnica utilizada:
#   TF-IDF (Term Frequency–Inverse Document Frequency) transforma os textos em
#   vetores numéricos que representam a importância de cada palavra no contexto
#   dos dois documentos. A similaridade de cosseno mede o ângulo entre esses
#   vetores: quanto mais próximos de 1.0, mais similares os textos são.
#
# Camadas da aplicação:
#   - Configurações: constantes e parâmetros globais
#   - Regra de Negócio: classificação do nível de similaridade
#   - Infraestrutura: validação e extração de texto dos arquivos
#   - Endpoints: rotas HTTP da API
# =============================================================================


# --- IMPORTAÇÕES ---

# FastAPI: framework web para construção da API REST
# UploadFile e File: tipos para receber arquivos via HTTP multipart/form-data
# HTTPException: utilizado para retornar erros HTTP com mensagens descritivas
from fastapi import FastAPI, UploadFile, File, HTTPException

# StaticFiles: permite servir arquivos estáticos (CSS, JS, imagens) pelo FastAPI
from fastapi.staticfiles import StaticFiles

# HTMLResponse: permite retornar HTML diretamente em um endpoint GET
from fastapi.responses import HTMLResponse

# uvicorn: servidor ASGI que executa a aplicação FastAPI de forma assíncrona
import uvicorn

# io: fornece a classe BytesIO, usada para tratar bytes em memória como se fossem
# um arquivo em disco — necessário para que PyPDF2 e python-docx leiam os uploads
import io

# nltk: biblioteca de Processamento de Linguagem Natural (PLN)
import nltk

# sent_tokenize: função do NLTK que divide um texto em uma lista de sentenças
from nltk.tokenize import sent_tokenize

# TfidfVectorizer: converte textos em matrizes TF-IDF (vetores numéricos)
from sklearn.feature_extraction.text import TfidfVectorizer

# cosine_similarity: calcula a similaridade de cosseno entre dois vetores TF-IDF
from sklearn.metrics.pairwise import cosine_similarity


# --- DOWNLOADS DO NLTK ---
# Os recursos abaixo são necessários para o funcionamento do NLTK.
# 'punkt' e 'punkt_tab': modelos de tokenização de sentenças para vários idiomas.
# 'stopwords': lista de palavras irrelevantes (artigos, preposições etc.)
#              que serão ignoradas durante a vetorização TF-IDF.
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')

from nltk.corpus import stopwords

# Carrega as stopwords em português uma única vez na inicialização,
# evitando recarregamentos desnecessários a cada requisição.
STOPWORDS_PT = stopwords.words('portuguese')


# =============================================================================
# CONFIGURAÇÕES GLOBAIS
# =============================================================================

# Conjunto de extensões de arquivo aceitas pela aplicação.
# Qualquer outro formato será rejeitado com erro HTTP 400.
EXTENSOES_PERMITIDAS = {'pdf', 'docx', 'txt'}

# Tamanho máximo permitido por arquivo: 5 megabytes.
# Arquivos maiores podem causar lentidão ou estouro de memória no servidor.
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5MB

# Limiar de similaridade utilizado na análise sentença a sentença.
# Sentenças do Texto B com similaridade TF-IDF acima deste valor em relação
# a qualquer sentença do Texto A são marcadas como suspeitas de plágio.
# Valor de 0.22 foi calibrado empiricamente durante os testes do sistema:
# abaixo disso gera muitos falsos positivos; acima, deixa passar trechos suspeitos.
THRESHOLD_SENTENCA = 0.22


# =============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# =============================================================================

# Cria a instância principal do FastAPI, que gerencia todas as rotas da API.
app = FastAPI()

# Registra a pasta "static" para servir arquivos estáticos (CSS, JS, imagens).
# Eles ficarão acessíveis via URL: http://127.0.0.1:8000/static/nome_do_arquivo
app.mount("/static", StaticFiles(directory="static"), name="static")


# =============================================================================
# CAMADA DE REGRA DE NEGÓCIO
# =============================================================================

def analisar_nivel_similaridade(percentual: float) -> str:
    """
    Classifica o grau de similaridade global entre dois documentos
    com base no percentual calculado pela similaridade de cosseno.

    Faixas de classificação (definidas com base na literatura de detecção de plágio):
      - Abaixo de 20%  → Texto provavelmente original
      - Entre 20% e 70% → Requer revisão manual do educador
      - Acima de 70%   → Alto risco de plágio

    Parâmetros:
        percentual (float): valor entre 0.0 e 100.0

    Retorno:
        str: descrição textual do nível de similaridade
    """
    if percentual < 20:
        return "Texto Original"
    elif percentual <= 70:
        return "Necessita de Revisão Manual"
    else:
        return "Provável Plágio Detectado"


# =============================================================================
# CAMADA DE INFRAESTRUTURA
# =============================================================================

def validar_arquivo(arquivo: UploadFile) -> None:
    """
    Valida se o arquivo enviado pelo usuário atende aos critérios da aplicação.

    Verificações realizadas:
      1. Extensão: deve ser PDF, DOCX ou TXT.
      2. Tamanho: não deve ultrapassar TAMANHO_MAXIMO_BYTES (5MB).

    Parâmetros:
        arquivo (UploadFile): objeto do arquivo recebido via requisição HTTP.

    Lança:
        HTTPException (400): se a extensão for inválida ou o arquivo for grande demais.
    """
    # Extrai a extensão do nome do arquivo e converte para minúsculas
    # para garantir comparação case-insensitive (ex: ".PDF" == ".pdf")
    ext = arquivo.filename.split('.')[-1].lower()

    if ext not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato '.{ext}' não suportado. Use PDF, DOCX ou TXT."
        )

    # arquivo.size pode ser None em alguns clientes HTTP; verificamos antes de comparar
    if arquivo.size and arquivo.size > TAMANHO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=400,
            detail="Arquivo muito grande. O tamanho máximo permitido é 5MB."
        )


async def extrair_texto(arquivo: UploadFile) -> str:
    """
    Lê o conteúdo do arquivo enviado e extrai seu texto bruto,
    de acordo com o formato (PDF, DOCX ou TXT).

    O uso de 'async/await' garante que a leitura do arquivo não bloqueie
    o servidor enquanto processa outras requisições simultaneamente.

    Parâmetros:
        arquivo (UploadFile): objeto do arquivo recebido via requisição HTTP.

    Retorno:
        str: texto extraído, com espaços múltiplos normalizados.
    """
    # Lê os bytes do arquivo de forma assíncrona (não bloqueante)
    conteudo = await arquivo.read()

    # Identifica o formato pelo sufixo do nome do arquivo
    ext = arquivo.filename.split('.')[-1].lower()
    texto = ""

    if ext == 'pdf':
        # PyPDF2 precisa de um objeto "file-like" para leitura.
        # BytesIO transforma os bytes brutos em um objeto que simula um arquivo em disco.
        import PyPDF2
        leitor = PyPDF2.PdfReader(io.BytesIO(conteudo))

        # Itera por todas as páginas e extrai o texto de cada uma.
        # O filtro "if p.extract_text()" ignora páginas sem texto (ex: imagens escaneadas).
        texto = " ".join([
            p.extract_text() for p in leitor.pages if p.extract_text()
        ])

    elif ext == 'docx':
        # python-docx também requer um objeto "file-like"
        from docx import Document
        doc = Document(io.BytesIO(conteudo))

        # Itera pelos parágrafos do documento e ignora os que estão vazios
        texto = " ".join([p.text for p in doc.paragraphs if p.text.strip()])

    else:
        # Para arquivos TXT, decodifica os bytes para string UTF-8.
        # errors='ignore' descarta caracteres inválidos sem lançar exceção.
        texto = conteudo.decode('utf-8', errors='ignore')

    # Normaliza o texto: substitui múltiplos espaços/quebras de linha por um único espaço.
    # Isso garante que a tokenização de sentenças funcione corretamente.
    return " ".join(texto.split())


# =============================================================================
# ENDPOINTS DA API
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """
    Rota raiz da aplicação (GET /).
    Lê e retorna o arquivo HTML principal da interface do usuário.
    O FastAPI serve o conteúdo como HTML puro graças ao HTMLResponse.
    """
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/analisar_documentos")
async def analisar_documentos(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...)
):
    """
    Endpoint principal (POST /analisar_documentos).
    Recebe dois arquivos, extrai seus textos e calcula a similaridade entre eles.

    Fluxo de processamento:
      1. Valida os arquivos recebidos (extensão e tamanho)
      2. Extrai o texto de cada arquivo
      3. Calcula a similaridade global com TF-IDF + cosseno
      4. Identifica e grifa sentenças suspeitas do Texto B

    Parâmetros (via multipart/form-data):
        file1 (UploadFile): primeiro documento a ser comparado.
        file2 (UploadFile): segundo documento a ser comparado.

    Retorno (JSON):
        percentual      (float): índice de similaridade global (0 a 100).
        nivel           (str):   classificação textual do risco de plágio.
        texto_grifado_a (str):   texto completo do Documento A (sem grifos).
        texto_grifado_b (str):   texto do Documento B com sentenças suspeitas
                                 envolvidas em tags <mark>.

    Lança:
        HTTPException (400): entrada inválida (arquivo vazio, formato errado, etc.)
        HTTPException (500): erro inesperado durante o processamento.
    """
    try:
        # --- ETAPA 1: VALIDAÇÃO ---
        # Verifica extensão e tamanho de ambos os arquivos antes de qualquer processamento
        validar_arquivo(file1)
        validar_arquivo(file2)

        # --- ETAPA 2: EXTRAÇÃO DE TEXTO ---
        texto_a = await extrair_texto(file1)
        texto_b = await extrair_texto(file2)

        # Rejeita arquivos que não contenham texto legível (ex: PDFs apenas com imagens)
        if not texto_a.strip():
            raise HTTPException(status_code=400, detail="O arquivo 1 não contém texto legível.")
        if not texto_b.strip():
            raise HTTPException(status_code=400, detail="O arquivo 2 não contém texto legível.")

        # --- ETAPA 3: SIMILARIDADE GLOBAL ---
        # Cria um vetorizador TF-IDF ignorando stopwords em português.
        # fit_transform ajusta o vocabulário e transforma os dois textos em vetores numéricos.
        vec_g = TfidfVectorizer(stop_words=STOPWORDS_PT)
        tfidf_g = vec_g.fit_transform([texto_a, texto_b])

        # Calcula a similaridade de cosseno entre os dois vetores.
        # O resultado é um valor entre 0.0 (totalmente diferente) e 1.0 (idêntico),
        # multiplicado por 100 para obter o percentual.
        percentual = round(
            float(cosine_similarity(tfidf_g[0:1], tfidf_g[1:2])[0][0]) * 100, 2
        )

        # --- ETAPA 4: ANÁLISE SENTENÇA A SENTENÇA ---
        # Divide cada texto em uma lista de sentenças usando o tokenizador do NLTK.
        # O parâmetro language='portuguese' melhora a precisão da segmentação.
        sent_a = sent_tokenize(texto_a, language='portuguese')
        sent_b = sent_tokenize(texto_b, language='portuguese')

        # Lista que acumulará as sentenças do Texto B, grifadas ou não
        resultado_b = []

        if sent_a and sent_b:
            # Cria um segundo vetorizador com bigramas (ngram_range=(1,2)):
            # considera pares de palavras consecutivas, o que melhora a detecção
            # de trechos reescritos com pequenas alterações de ordem.
            vec_s = TfidfVectorizer(stop_words=STOPWORDS_PT, ngram_range=(1, 2))

            # Treina o vocabulário com todas as sentenças de ambos os documentos
            # para garantir que o espaço vetorial seja compartilhado entre eles.
            vec_s.fit(sent_a + sent_b)

            # Transforma todas as sentenças do Texto A em vetores TF-IDF de uma vez,
            # gerando uma matriz onde cada linha representa uma sentença.
            tfidf_a = vec_s.transform(sent_a)

            # Analisa cada sentença do Texto B individualmente
            for sentenca in sent_b:
                # Ignora sentenças muito curtas (ruídos, títulos de seção, etc.)
                # que poderiam gerar falsos positivos na comparação
                if len(sentenca.strip()) < 10:
                    resultado_b.append(sentenca)
                    continue

                # Transforma a sentença atual do Texto B em vetor TF-IDF
                v_s = vec_s.transform([sentenca])

                # Calcula a similaridade entre esta sentença e TODAS as sentenças do Texto A,
                # e pega apenas o valor máximo (sentença mais similar encontrada no Texto A)
                max_sim = float(cosine_similarity(v_s, tfidf_a).max())

                # Se a similaridade máxima superar o limiar definido,
                # a sentença é marcada com a tag HTML <mark> (destaque visual no frontend)
                if max_sim > THRESHOLD_SENTENCA:
                    resultado_b.append(f"<mark>{sentenca}</mark>")
                else:
                    resultado_b.append(sentenca)

        # --- RETORNO ---
        # Consolida o resultado e retorna como JSON para o frontend
        return {
            "percentual": percentual,                        # Ex: 85.34
            "nivel": analisar_nivel_similaridade(percentual), # Ex: "Provável Plágio Detectado"
            "texto_grifado_a": texto_a,                      # Texto A sem marcações
            "texto_grifado_b": " ".join(resultado_b)         # Texto B com <mark> nas suspeitas
        }

    except HTTPException:
        # Re-lança erros HTTP já tratados (validação, arquivo vazio, etc.)
        # sem encapsulá-los no tratamento genérico abaixo
        raise

    except Exception as e:
        # Captura qualquer erro inesperado (ex: arquivo corrompido, falha de biblioteca)
        # e retorna uma mensagem genérica com o detalhe do erro para facilitar o diagnóstico
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar os arquivos: {str(e)}")


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    # Inicia o servidor Uvicorn localmente na porta 8000.
    # Acesse a aplicação em: http://127.0.0.1:8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
