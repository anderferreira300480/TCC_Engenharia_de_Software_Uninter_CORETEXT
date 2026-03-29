import difflib
import os

# --- CAMADA 1: REGRA DE NEGÓCIO (CORE) ---
# Esta função é "pura": ela não sabe que existem arquivos ou pastas.
def calcular_similaridade(texto_a, texto_b):
    matcher = difflib.SequenceMatcher(None, texto_a, texto_b)
    return matcher.ratio() * 100

def analisar_nivel_similaridade(percentual):
    if percentual < 20:
        return "Texto Original"
    elif percentual <= 70:
        return "Necessita de Revisão Manual"
    else:    
        return "Provável Plágio Detectado"
                 
                 
# --- CAMADA 2: INFRAESTRUTURA (ADAPTADOR PARA ARQUIVOS LOCAIS) ---
# Esta função cuida da "sujeira" de abrir pastas e tratar erros de disco.
def comparar_arquivos_locais(nome_arquivo1, nome_arquivo2):
    base_path = os.path.dirname(__file__)
    data_path = os.path.join(base_path, '..', 'data')
    
    path1 = os.path.join(data_path, nome_arquivo1)
    path2 = os.path.join(data_path, nome_arquivo2)

    try:
        with open(path1, 'r', encoding='utf-8') as f1, \
             open(path2, 'r', encoding='utf-8') as f2:
            
            # Chamamos a função pura para fazer o cálculo
            resultado = calcular_similaridade(f1.read(), f2.read())
            
            print(f"Comparando: [{nome_arquivo1}] vs [{nome_arquivo2}]")
            print(f"Resultado: {resultado:.2f}%")
            print("-" * 30)
            return resultado
            
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado.")
        return None

# --- BLOCO DE EXECUÇÃO ---
if __name__ == "__main__":
    print("\nVALIDAÇÃO COM ARQUITETURA SEPARADA\n")
    comparar_arquivos_locais('arquivo1.txt', 'arquivo2.txt')


def gerar_texto_grifado(texto_a, texto_b):
    matcher = difflib.SequenceMatcher(None, texto_a, texto_b)
    resultado_a = []
    
    # get_opcodes retorna instruções: 'equal' (igual), 'replace' (diferente), etc.
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        trecho = texto_a[i1:i2]
        if tag == 'equal':
            # Se for igual ao outro texto, grifamos
            resultado_a.append(f"<mark>{trecho}</mark>")
        else:
            # Se for diferente, mantemos o texto original sem grifo
            resultado_a.append(trecho)
            
    return "".join(resultado_a)    