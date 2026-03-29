from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import io
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Downloads essenciais
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
from nltk.corpus import stopwords
STOPWORDS_PT = stopwords.words('portuguese')

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def extrair_texto(arquivo: UploadFile):
    conteudo = arquivo.file.read()
    ext = arquivo.filename.split('.')[-1].lower()
    texto = ""
    if ext == 'pdf':
        import PyPDF2
        leitor = PyPDF2.PdfReader(io.BytesIO(conteudo))
        texto = " ".join([p.extract_text() for p in leitor.pages])
    elif ext == 'docx':
        from docx import Document
        doc = Document(io.BytesIO(conteudo))
        texto = " ".join([p.text for p in doc.paragraphs])
    else:
        texto = conteudo.decode('utf-8', errors='ignore')
    return " ".join(texto.split())

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/analisar_documentos")
async def analisar_documentos(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    texto_a = extrair_texto(file1)
    texto_b = extrair_texto(file2)

    vec_g = TfidfVectorizer(stop_words=STOPWORDS_PT)
    tfidf_g = vec_g.fit_transform([texto_a, texto_b])
    percentual = round(float(cosine_similarity(tfidf_g[0:1], tfidf_g[1:2])[0][0]) * 100, 2)

    sent_a = sent_tokenize(texto_a)
    sent_b = sent_tokenize(texto_b)
    resultado_b = []

    if sent_a and sent_b:
        vec_s = TfidfVectorizer(stop_words=STOPWORDS_PT, ngram_range=(1,2))
        vec_s.fit(sent_a + sent_b)
        tfidf_a = vec_s.transform(sent_a)
        
        for s in sent_b:
            if len(s.strip()) < 10: 
                resultado_b.append(s)
                continue
            v_s = vec_s.transform([s])
            max_sim = float(cosine_similarity(v_s, tfidf_a).max())
            if max_sim > 0.22:
                resultado_b.append(f"<mark>{s}</mark>")
            else:
                resultado_b.append(s)

    return {
        "percentual": percentual,
        "texto_grifado_a": texto_a,
        "texto_grifado_b": " ".join(resultado_b)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)