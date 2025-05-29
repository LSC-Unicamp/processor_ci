import os
import re

# Diretório onde estão os arquivos .sv
diretorio = './'  # Modifique conforme necessário

# Expressão regular para localizar o trecho entre '// Clock inflaestructure' e 'endmodule'
padrao_clock_reset = re.compile(
    r'// Clock inflaestructure.*?endmodule', re.DOTALL
)


def substituir_clock_reset():
    for root, dirs, files in os.walk(diretorio):
        for arquivo in files:
            if arquivo.endswith('.sv'):
                caminho = os.path.join(root, arquivo)
                with open(caminho, 'r', encoding='utf-8') as f:
                    conteudo = f.read()

                if re.search(padrao_clock_reset, conteudo):
                    novo_conteudo = re.sub(
                        padrao_clock_reset, 'endmodule', conteudo
                    )
                    with open(caminho, 'w', encoding='utf-8') as f:
                        f.write(novo_conteudo)
                    print(f'✔ Substituído trecho clock/reset em: {caminho}')
                else:
                    print(f'✘ Trecho não encontrado em: {caminho}')


if __name__ == '__main__':
    substituir_clock_reset()
