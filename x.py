import os

# Diretório onde estão os arquivos .sv
diretorio = "./"  # Modifique se necessário

# Trecho original (sem vírgula inicial)
trecho_antigo = """\
    output logic        data_mem_cyc;
    output logic        data_mem_stb;
    output logic        data_mem_we;
    output logic [31:0] data_mem_addr;
    output logic [31:0] data_mem_data_out;
    input  logic [31:0] data_mem_data_in;
    input  logic        data_mem_ack;"""

# Trecho novo (com vírgula inicial e final sem ponto e vírgula)
trecho_novo = """\
,
    output logic        data_mem_cyc,
    output logic        data_mem_stb,
    output logic        data_mem_we,
    output logic [31:0] data_mem_addr,
    output logic [31:0] data_mem_data_out,
    input  logic [31:0] data_mem_data_in,
    input  logic        data_mem_ack"""

def substituir_data_mem_portas():
    for root, _, arquivos in os.walk(diretorio):
        for nome_arquivo in arquivos:
            if nome_arquivo.endswith(".sv"):
                caminho = os.path.join(root, nome_arquivo)
                with open(caminho, "r", encoding="utf-8") as f:
                    conteudo = f.read()

                if trecho_antigo in conteudo:
                    novo_conteudo = conteudo.replace(trecho_antigo, trecho_novo)
                    with open(caminho, "w", encoding="utf-8") as f:
                        f.write(novo_conteudo)
                    print(f"✔ Substituição feita em: {caminho}")
                else:
                    print(f"✘ Trecho não encontrado em: {caminho}")

if __name__ == "__main__":
    substituir_data_mem_portas()

