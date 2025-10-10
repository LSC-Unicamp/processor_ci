import os

# Diretório onde estão os arquivos .sv
diretorio = "./"  # Modifique se necessário

# Trecho exato a ser substituído
trecho_antigo = """\
    output logic [31:0] core_addr,     // Endereço
    output logic [31:0] core_data,     // Dados de entrada (para escrita)
    input  logic [31:0] core_data,     // Dados de saída (para leitura)"""

# Novo trecho a ser inserido
trecho_novo = """\
    output logic [31:0] core_addr,     // Endereço
    output logic [31:0] core_data_out, // Dados de entrada (para escrita)
    input  logic [31:0] core_data_in,  // Dados de saída (para leitura)"""


def substituir_core_data():
    for root, dirs, files in os.walk(diretorio):
        for arquivo in files:
            if arquivo.endswith(".sv"):
                caminho = os.path.join(root, arquivo)
                with open(caminho, "r", encoding="utf-8") as f:
                    conteudo = f.read()

                if trecho_antigo in conteudo:
                    novo_conteudo = conteudo.replace(trecho_antigo, trecho_novo)
                    with open(caminho, "w", encoding="utf-8") as f:
                        f.write(novo_conteudo)
                    print(f"✔ Substituído trecho em: {caminho}")
                else:
                    print(f"✘ Trecho não encontrado em: {caminho}")


if __name__ == "__main__":
    substituir_core_data()
