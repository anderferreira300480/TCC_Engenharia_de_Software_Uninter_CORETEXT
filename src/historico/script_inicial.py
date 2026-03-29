import difflib
import os

def comparar_arquivos(nome_arquivo1, nome_arquivo2):
    """"
    __file__ é uma variável oculta do Python que guarda o caminho de onde o script comparador.py está. 
    O dirname pega apenas a pasta (no caso, a pasta src).
    """
    base_path = os.path.dirname(__file__)   
    """
    O .. significa "voltar uma pasta". Então, saímos de src e entramos em data. 
    Isso garante que o código funcione no seu Windows ou em um servidor Linux sem você precisar mudar uma vírgula. 
    O os.join coloca as barras (/ ou \) corretas dependendo do sistema operacional.
    """
    data_path = os.path.join(base_path, '..', 'data') 
    """
    Aqui montamos o "endereço completo" de cada arquivo na pasta data.
    """
    path1 = os.path.join(data_path, nome_arquivo1)
    path2 = os.path.join(data_path, nome_arquivo2)

    """
    O try/except serve para "tentar" executar o código, mas caso dê algum erro (como o arquivo não existir), 
    o programa não quebra e mostra uma mensagem amigável ao usuário.
    """
    try:
        """
        Abrimos os dois arquivos em modo de leitura ('r') e com codificação UTF-8, as f1 e f2 são os "apelidos" para os arquivos abertos.
        O with garante que os arquivos serão fechados corretamente após a leitura, mesmo que ocorra um erro durante o processo.
        """
        with open(path1, 'r', encoding='utf-8') as f1, \
             open(path2, 'r', encoding='utf-8') as f2:
            
            """
            Lemos o conteúdo dos arquivos e armazenamos nas variáveis texto1 e texto2.
            """
            texto1 = f1.read()
            texto2 = f2.read()
            
            # Cálculo de similaridade
            """
            A classe SequenceMatcher do módulo difflib compara duas sequências (neste caso, strings) e calcula uma medida de similaridade entre elas.
            O parêmetro None indica que não estamos fornecendo uma função de junk (caracteres a serem ignorados). 
            O método ratio() retorna um valor entre 0 e 1, que representa a similaridade entre as duas sequências. Multiplicamos por 100 para obter uma porcentagem.
            """
            matcher = difflib.SequenceMatcher(None, texto1, texto2)
            percentual = matcher.ratio() * 100
            
            print(f"Comparando: [{nome_arquivo1}] vs [{nome_arquivo2}]")
            print(f"Resultado: {percentual:.2f}% de similaridade")
            print("-" * 40)
            
            return percentual # Retornamos o valor para uso futuro
            
            """
            Se o arquivo não existir, o programa não "quebra" com uma mensagem vermelha feia; 
            ele avisa educadamente o que aconteceu. Isso é essencial para a experiência do usuário.     
            """
    except FileNotFoundError:
        print(f"Erro: Arquivos não encontrados na pasta /data. Verifique os nomes.")

""" 
Bloco de código que só será executado se este script for rodado diretamente (não importado como módulo).
Esta linha diz: "Só execute o teste se eu rodar este arquivo diretamente". 
Se amanhã você importar essa função dentro da sua API, ela não vai sair rodando os testes sozinha. 
É uma proteção de código profissional.
"""
if __name__ == "__main__":
    print("\n" + "="*40)
    print("INICIANDO TESTES DE VALIDAÇÃO DO TCC")
    print("="*40 + "\n")

    # TESTE A: Identidade (Arquivos iguais)
    comparar_arquivos('arquivo1.txt', 'arquivo1.txt')

    # TESTE B: Similaridade Alta (Texto 1 vs Texto 2)
    # Esperado: > 80% (pois mudamos poucas palavras)
    comparar_arquivos('arquivo1.txt', 'arquivo2.txt')

    # TESTE C: Similaridade Baixa (Texto 1 vs Texto 3)
    # Esperado: < 15% (assuntos totalmente diferentes)
    comparar_arquivos('arquivo1.txt', 'arquivo3.txt')

    print("="*40)
    print("FIM DOS TESTES")
    print("="*40)