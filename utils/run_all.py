"""
Este script lê uma lista de URLs de um arquivo, executa um comando com cada URL usando proxychains,
e gera configurações através do script `config_generator.py`. Para cada URL, o comando é executado
com um tempo limite de 3 minutos (180 segundos).

O script faz o seguinte:
1. Lê as URLs de um arquivo chamado 'arquivos.txt'.
2. Para cada URL, executa um comando utilizando `proxychains` com o script `config_generator.py`.
3. Cada comando é executado com um tempo limite de 180 segundos.
4. Em caso de erro de execução ou tempo limite, o script imprime mensagens apropriadas.

Argumentos:
    Não há argumentos de linha de comando. O arquivo de entrada `arquivos.txt` deve estar presente
    no diretório de execução.

Exceções:
    - `subprocess.TimeoutExpired`: Se o comando não for concluído dentro do tempo limite.
    - `subprocess.CalledProcessError`: Se ocorrer um erro ao executar o comando.

Nota:
    O arquivo de entrada `arquivos.txt` deve conter uma URL por linha.
"""

import time
import subprocess

# Caminho para o arquivo que contém a lista de URLs
MODEL_PATH = "models.txt"
FILE_PATH = "processadores3.txt"

# Abrir o arquivo e ler as URLs
with open(FILE_PATH, "r", encoding="utf-8") as file:
    urls = file.readlines()

# Abrir o arquivo e ler o nome dos modelos
with open(MODEL_PATH, "r", encoding="utf-8") as file:
    models = file.readlines()

# Remover qualquer espaço ou quebra de linha ao final de cada URL
urls = [url.strip() for url in urls]

# Remover qualquer espaço ou quebra de linha ao final de cada modelo
models = [model.strip() for model in models]

# Comando base
command_base = [
    "proxychains",
    "python",
    "config_generator.py",
    "-u",
    "",
    "-c",
    "-a",
    "-p",
    "",
    "-m",
    "",
    #'-n',
]

# Timeout de 3 minutos (180 segundos)
TIMEOUT_SECONDS = 720

urls_falharam = []
urls_sucesso = []

relatorio = []

# Para cada URL na lista, executar o comando com timeout
for model in models:
    tempo_inicio = time.time()
    command_base[8] = f"{model}.json"
    command_base[10] = model

    print(f"Modelo: {model}\n\n")

    for url in urls:
        # Montar o comando com a URL
        command_base[4] = url  # Substituir a URL no comando
        print(f"Executando: {' '.join(command_base)}")

        try:
            # Executar o comando com timeout
            subprocess.run(command_base, timeout=TIMEOUT_SECONDS, check=True)
            urls_sucesso.append(url)
        except subprocess.TimeoutExpired:
            print(
                f"Comando para {url} atingiu o tempo limite de {TIMEOUT_SECONDS} segundos."
            )
            urls_falharam.append(url)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar o comando para {url}: {e}")

    tempo_fim = time.time()
    print(f"Tempo total de execução: {tempo_fim - tempo_inicio} segundos")

    relatorio.append(
        f"Modelo: {model}\nTempo total de execução: {tempo_fim - tempo_inicio} segundos\n\n"
    )

print("\n")

print(f"URLs que falharam: {urls_falharam}")
print(f"URLs que tiveram sucesso: {urls_sucesso}")

with open("relatorio.txt", "w", encoding="utf-8") as file:
    file.writelines(relatorio)

print("Relatório salvo em 'relatorio.txt'")
