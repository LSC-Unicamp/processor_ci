# ProcessorCI

[![Pylint](https://github.com/LSC-Unicamp/processor-ci/actions/workflows/pylint.yml/badge.svg)](https://github.com/LSC-Unicamp/processor-ci/actions/workflows/pylint.yml)  
[![Python Code Format Check](https://github.com/LSC-Unicamp/processor-ci/actions/workflows/blue.yml/badge.svg)](https://github.com/LSC-Unicamp/processor-ci/actions/workflows/blue.yml)  

Bem-vindo ao ProcessorCI!

O **ProcessorCI** é um projeto que visa modernizar o processo de verificação de processadores, integrando técnicas consolidadas de verificação, integração contínua e uso de FPGAs.

## Sobre este módulo

Este repositório contém scripts utilitários para configurar processadores, realizar síntese, carregar em FPGAs, entre outras funções relacionadas ao ProcessorCI.

## Iniciando

### Instalação

1. **Clone o repositório**  
Clone o repositório para o seu ambiente de desenvolvimento local.

```bash
git clone https://github.com/LSC-Unicamp/processor-ci.git  
cd processor-ci  
```

2. **Configure um ambiente virtual e instale as dependências**  

```bash
python3 -m venv env
. env/bin/activate
pip install -r requirements.txt
```

**Obs**: Sempre que for utilizar o projeto, é necessário ativar o ambiente virtual com:

```bash
. env/bin/activate
```

### Adicionando um novo processador

O processo para adicionar um processador consiste em três etapas:

1. Gerar o arquivo de configuração (`config.json`).
2. Realizar a ligação dos módulos em Verilog.  
3. Integrar o arquivo de pipeline ao Jenkins.  

#### 1. Gerando as configurações  

Para gerar o pipeline do Jenkins, preencha um arquivo `json` com as características do processador e adicione uma nova entrada ao `config.json`. Exemplo:  

```json
"darkriscv": {
    "name": "darkriscv",
    "folder": "darkriscv",
    "sim_files": [],
    "files": ["rtl/darkriscv.v"],
    "include_dirs": ["rtl"],
    "repository": "https://github.com/darklife/darkriscv",
    "top_module": "darkriscv",
    "extra_flags": [],
    "language_version": "2005"
}
```

Para facilitar, o script `config_generator.py` pode gerar uma configuração inicial:  

```bash
python3 config_generator.py -u URL_DO_PROCESSADOR -c
```

Esse comando clonará o repositório, listará os arquivos e adicionará uma nova entrada no `config.json`. É possível alterar o caminho do arquivo de configuração usando a flag `-p`. Para desativar o uso de modelos baseados em IA, use a flag `-n`.

Após a geração, revise a configuração para garantir que esteja correta.

#### 2. Realizando a ligação  

O script criará um arquivo Verilog correspondente ao processador. Edite este arquivo para conectar o módulo principal do processador ao top module do ProcessorCI. Caso tenha preenchido manualmente o `config.json`, crie um arquivo baseado no template:

```bash
cp rtl/template.v rtl/<Nome-do-repositorio>.v
```

Exemplo de ligação:

```verilog
Controller #(
    ...
) Controller(
    ...
    .clk_core  (clk_core),
    .reset_core(reset_core),
    
    .core_memory_response  (core_memory_response),
    .core_read_memory      (memory_read),
    .core_write_memory     (memory_write),
    .core_address_memory   (address),
    .core_write_data_memory(core_write_data),
    .core_read_data_memory (core_read_data),

    //sync memory bus
    .core_read_data_memory_sync     (),
    .core_memory_read_response_sync (),
    .core_memory_write_response_sync(),

    // Data memory
    .core_memory_response_data  (),
    .core_read_memory_data      (1'b0),
    .core_write_memory_data     (1'b0),
    .core_address_memory_data   (32'h00000000),
    .core_write_data_memory_data(32'h00000000),
    .core_read_data_memory_data ()
);
Core #(
    .BOOT_ADDRESS(32'h00000000)
) Core(
    .clk            (clk_core),
    .reset          (reset_core),
    .memory_response(core_memory_response),
    .memory_read    (memory_read),
    .memory_write   (memory_write),
    .write_data     (core_write_data),
    .read_data      (core_read_data),
    .address        (address)
);
```

Mais detalhes na [documentação do Controller](https://lsc-unicamp.github.io/processor-ci-controller/).  

#### 3. Integrando ao Jenkins  

Após configurar, crie um novo item no Jenkins e copie o pipeline gerado para ele. Atualmente, não há integração automática com o Jenkins oficial. Caso deseje integrar um novo processador, abra uma *Issue* com o nome, URL e configuração.  

### Utilização  

Após configurar e integrar o processador à infraestrutura, é possível interagir com ele utilizando os scripts do projeto. As interações principais consistem na realização de síntese e carregamento (load) para diferentes FPGAs. Um exemplo de utilização seria:

```bash
cd processor_repository/
# Realiza a síntese
python3 /path_to_script/main.py -c /path_to_config/config.json -p Risco-5 -b digilent_nexys4_ddr
# Realiza o carregamento (load)
python3 /path_to_script/main.py -c /path_to_config/config.json -p Risco-5 -b digilent_nexys4_ddr -l
```

- `-c /path_to_config/config.json`: Caminho para o arquivo de configuração do processador.
- `-p Risco-5`: Nome do processador a ser sintetizado.
- `-b digilent_nexys4_ddr`: FPGA de destino para síntese e carregamento.
- `-l`: Realiza o carregamento do design na FPGA após a síntese.

## Opções de Utilização

Os scripts do ProcessorCI possuem diversas opções configuráveis por meio de flags. Abaixo estão descritas as principais flags e funcionalidades:

### Flags Disponíveis no script de configuração

- `-c`, `--generate-config`  
**Descrição:** Gera as configurações iniciais de um processador a partir da URL de seu repositório.  

**Exemplo de uso:**

```bash
python3 config_generator.py -c -u URL_DO_PROCESSADOR
```

**Detalhes:**

- Clona o repositório do processador.
- Analisa os arquivos do repositório para identificar módulos e testbenches.
- Gera um arquivo JSON com as configurações do processador.
- Pode adicionar a configuração gerada ao arquivo central (`config.json`) utilizando a flag `-a`.

- `-u`, `--processor-url`

**Descrição:** Especifica a URL do repositório do processador que será clonado.

**Exemplo de uso:**

```bash
python3 config_generator.py -c -u https://github.com/example/example-processor.git
```

- `-j`, `--generate-all-jenkinsfiles`

**Descrição:** Gera arquivos Jenkinsfile para todos os processadores listados no arquivo de configuração central.

**Exemplo de uso:**

```bash
python3 config_generator.py -j
```

**Detalhes:**

- Analisa o arquivo `config.json`.
- Cria um Jenkinsfile específico para cada processador suportado.

- `-g`, `--plot-graph`

**Descrição:** Gera gráficos de dependência dos módulos do processador.

**Exemplo de uso:**

```bash
python3 config_generator.py -c -u URL_DO_PROCESSADOR -g
```  

- `-a`, `--add-config`

**Descrição:** Adiciona a configuração gerada ao arquivo de configuração central (`config.json`).

**Exemplo de uso:**

```bash
python3 config_generator.py -c -u URL_DO_PROCESSADOR -a
```

- `-p`, `--path-config`

**Descrição:** Define o caminho para o arquivo de configuração central. O padrão é `config.json`.

**Exemplo de uso:**

```bash
python3 config_generator.py -c -u URL_DO_PROCESSADOR -p /caminho/para/config.json
```

- `-n`, `--no-llama`

**Descrição:** Desativa o uso do modelo *llama* para identificação automática do top module e outros parâmetros.

**Exemplo de uso:**

```bash
python3 config_generator.py -c -u URL_DO_PROCESSADOR -n
```

### Exemplos de Uso do script de configuração

1. **Gerar uma configuração inicial para um processador:**

```bash
python3 config_generator.py -c -u https://github.com/example/example-processor.git
```

2. **Adicionar a configuração gerada ao arquivo `config.json`:**

```bash
python3 config_generator.py -c -u https://github.com/example/example-processor.git -a
```

3. **Gerar gráficos de dependência dos módulos:**

```bash
python3 config_generator.py -c -u https://github.com/example/example-processor.git -g
```

4. **Criar arquivos Jenkinsfile para todos os processadores configurados:**

```bash
python3 config_generator.py -j
```

5. **Definir um caminho personalizado para o arquivo `config.json`:**

```bash
python3 config_generator.py -c -u https://github.com/example/example-processor.git -p /caminho/personalizado/config.json
```

### Flags Disponíveis no Script Principal

- `-c`, `--config`

**Descrição:** Especifica o caminho para o arquivo de configuração no formato JSON. Este arquivo contém os detalhes sobre os processadores e placas disponíveis para configuração.

**Exemplo de uso:**

```bash
python3 main.py -c config.json
```

- `-p`, `--processor`

**Descrição:** Especifica o nome do processador a ser utilizado. Este argumento é obrigatório.

**Exemplo de uso:**

```bash
python3 main.py -c config.json -p nome_do_processador
```

- `-b`, `--board`

**Descrição:** Especifica o nome da placa FPGA a ser utilizada. Este argumento é obrigatório.

**Exemplo de uso:**

```bash
python3 main.py -c config.json -p nome_do_processador -b nome_da_placa
```

- `-t`, `--toolchain`

**Descrição:** Especifica o caminho para o diretório das toolchains. Se não fornecido, o caminho padrão é `/eda`.

**Exemplo de uso:**

```bash
python3 main.py -c config.json -p nome_do_processador -b nome_da_placa -t /caminho/para/toolchain
```

- `-l`, `--load`

**Descrição:** Se especificado, o script irá carregar o bitstream gerado na FPGA após a construção.

**Exemplo de uso:**

```bash
python3 main.py -c config.json -p nome_do_processador -b nome_da_placa -l
```

### Exemplos de Uso

1. **Configurar um processador para uma placa específica:**

```bash
python3 main.py -c config.json -p nome_do_processador -b nome_da_placa
```

2. **Definir um caminho personalizado para as toolchains:**

```bash
python3 main.py -c config.json -p nome_do_processador -b nome_da_placa -t /caminho/personalizado/toolchain
```

3. **Carregar o bitstream na FPGA após a construção:**

```bash
python3 main.py -c config.json -p nome_do_processador -b nome_da_placa -l
```

4. **Usar o caminho padrão das toolchains (`/eda`):**

```bash
python3 main.py -c config.json -p nome_do_processador -b nome_da_placa
```

**Requisitos:**

- Um arquivo de configuração JSON válido é necessário, contendo os dados dos processadores e das placas.
- Certifique-se de que o caminho da toolchain e as configurações da placa estejam corretamente configurados no seu ambiente.

## Dúvidas e sugestões  

A documentação oficial está disponível em: [processorci.ic.unicamp.br](https://processorci.ic.unicamp.br/).  
Dúvidas e sugestões podem ser enviadas na seção de Issues no GitHub. Contribuições são bem-vindas, e todos os Pull Requests serão revisados e mesclados sempre que possível.  

## Contribuindo com o projeto  

**Contribuições**: Se você deseja contribuir com melhorias, veja como no arquivo [CONTRIBUTING.md](./CONTRIBUTING.md).  

## Licença  

Este projeto é licenciado sob a licença [MIT](./LICENSE), que garante total liberdade para uso.
