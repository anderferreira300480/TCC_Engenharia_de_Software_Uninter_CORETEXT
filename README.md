CORETEXT: Auditoria de Integridade e Detecção de Paráfrases
O CORETEXT é uma ferramenta de apoio acadêmico desenvolvida para identificar similaridades semânticas e indícios de plágio em documentos de texto (PDF, DOCX e TXT). Diferente de ferramentas baseadas em busca literal, o CORETEXT utiliza técnicas de Processamento de Linguagem Natural (PLN) para mapear a carga intelectual das sentenças.



🚀 Funcionalidades
Análise Multiformato: Suporte para leitura de arquivos .pdf, .docx e .txt.

Similaridade Global: Cálculo de proximidade temática utilizando TF-IDF e Similaridade de Cosseno.

Auditoria Granular: Comparação sentença a sentença com marcação visual (grifos) em tempo real.

Interface Reativa: Dashboard desenvolvido com FastAPI e JavaScript para feedback instantâneo.

Modo Nova Análise: Reset de estado da aplicação sem necessidade de recarregar a página.



🛠️ Tecnologias Utilizadas
Linguagem: Python 3.10+

Framework Web: FastAPI (Uvicorn)

Inteligência Artificial: Scikit-Learn (TF-IDF, Cosine Similarity)

PLN: NLTK (Natural Language Toolkit)

Manipulação de Arquivos: PyPDF2 e Python-Docx



📋 Pré-requisitos
Antes de começar, você precisará ter instalado em sua máquina:

Python 3.10 ou superior

Gerenciador de pacotes pip



🔧 Instalação e Execução
Clone o repositório:

Bash
git clone https://github.com/seu-usuario/coretext.git
cd coretext
Crie um ambiente virtual (Recomendado):

Bash
python -m venv venv
# No Windows:
.\venv\Scripts\activate
Instale as dependências:

Bash
pip install fastapi uvicorn PyPDF2 python-docx scikit-learn nltk
Execute a aplicação:

Bash
cd src
python main.py
Acesse no navegador:
Abra http://127.0.0.1:8000

📖 Documentação da API
Uma vez que o servidor esteja rodando, você pode acessar a documentação automática interativa (Swagger UI) em:
http://127.0.0.1:8000/docs

⚖️ Licença
Este projeto foi desenvolvido para fins acadêmicos e está sob a licença MIT.