"""
This script is designed to manage the configuration, build, and optional loading of FPGA bitstreams
based on specified processor and board configurations. It integrates functionality for handling
toolchains, generating build files, and flashing bitstreams onto the FPGA.

Modules and Features:
- **Configuration Loading**: Reads a JSON configuration file to extract processor data.
- **Build File Generation**: Creates a build file for the specified processor and board.
- **Build and Flash**: Supports building and flashing bitstreams onto the FPGA.

Functions:
- **`main`**: Executes the primary flow, including loading configuration, generating the build file,
  and optionally flashing the FPGA.

Command-Line Interface:
- The script supports command-line arguments to customize behavior. Use `-h` or `--help` to
    display the CLI usage.

Arguments:
- **`-c`/`--config`** (required): Path to the configuration file.
- **`-p`/`--processor`** (required): Name of the processor to use.
- **`-b`/`--board`** (required): Name of the board to target.
- **`-t`/`--toolchain`** (optional): Path to the toolchains (default: `/eda`).
- **`-l`/`--load`** (optional): Load the bitstream onto the FPGA after building.

Usage Example:
```bash
python script.py -c config.json -p processor_name -b board_name -t /path/to/toolchain -l
```
Requirements:

- The configuration file should be in JSON format and contain details about the
    processors and boards.
- Ensure the toolchain path and board are correctly set up in the environment.
"""

import argparse
from core.config import load_config
from core.fpga import make_build_file, flash, build


def main(
    config_path: str,
    processor_name: str,
    board_name: str,
    toolchain_path: str,
    load: bool = False,
) -> None:
    """Main function to handle FPGA design setup, build, and optional flashing.
    Args:
        config_path (str): Path to the configuration file in JSON format.
        processor_name (str): Name of the processor to use.
        board_name (str): Name of the target FPGA board.
        toolchain_path (str): Path to the toolchain directory.
        load (bool, optional): If `True`, flash the generated bitstream to the FPGA.
                            Defaults to `False`.

    Steps:
    1. Loads the configuration file to extract processor and board data.
    2. Generates a build file for the specified processor and board.
    3. Builds the design and optionally flashes the FPGA.

    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        KeyError: If the processor or board data is missing in the configuration file.
    """
    # Carrega o arquivo de configuração
    processor_data = load_config(config_path, processor_name)

    # Exibe os argumentos recebidos e os dados do processador

    build_file_path = make_build_file(
        processor_data, board_name, toolchain_path
    )

    if load:
        flash(board_name, toolchain_path)
    else:
        build(build_file_path, board_name, toolchain_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Script para configurar o design com base no processador e placa.'
    )

    # Definição dos argumentos obrigatórios
    parser.add_argument(
        '-c',
        '--config',
        type=str,
        required=True,
        help='Caminho do diretorio de configuração do script.',
    )
    parser.add_argument(
        '-p',
        '--processor',
        type=str,
        required=True,
        help='Nome do processador a ser utilizado.',
    )
    parser.add_argument(
        '-b',
        '--board',
        type=str,
        required=True,
        help='Nome da placa a ser utilizada.',
    )

    # Parâmetro opcional para o caminho das toolchains
    parser.add_argument(
        '-t',
        '--toolchain',
        type=str,
        default='/eda',
        required=False,
        help='Caminho para as toolchains (padrão: /eda).',
    )

    # Parâmetro opcional para carregar o bitstream
    parser.add_argument(
        '-l',
        '--load',
        action='store_true',
        help='Carregar o bitstream na FPGA.',
    )

    # Parse dos argumentos
    args = parser.parse_args()

    # Chama a função principal com os argumentos
    main(
        args.config,
        args.processor,
        args.board,
        args.toolchain,
        args.load,
    )
