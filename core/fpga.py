"""
This module provides utility functions for generating build scripts, managing toolchain
configurations, and executing build and flash processes for various FPGA development boards.

Main Features:
1. **Macro Management**:
   - Dynamically retrieves macro definitions specific to the target board.

2. **Prefix Command Determination**:
   - Selects appropriate commands for handling Verilog and VHDL files based on the
    board and file type.

3. **Build Script Generation**:
   - Creates a complete build script by combining base configuration templates and
    specific file paths.

4. **Build Process Execution**:
   - Automates the FPGA build process using Makefiles and specified build scripts.

5. **Flashing the FPGA**:
   - Handles the process of flashing the generated bitstream to the target FPGA board.

Functions:
- `get_macros(board: str) -> str`: Returns macro definitions for a specified board.
- `get_prefix(board: str, vhdl: bool) -> str`: Determines the appropriate prefix command
    for file processing.
- `make_build_file(config: dict, board: str, toolchain_path: str) -> str`: Generates a
    build script for the target board.
- `build(build_script_path: str, board: str, toolchain_path: str) -> None`: Executes
    the build process using Makefiles.
- `flash(board: str, toolchain_path: str) -> None`: Flashes the generated bitstream
    to the target board.

Usage:
- Ensure that the toolchain path and configuration files are properly set up.
- Use `make_build_file` to generate a build script for the target FPGA.
- Execute `build` to compile the design and `flash` to program the FPGA.

Dependencies:
- Python's standard `os` and `subprocess` modules are used for file operations and
    command execution.
- The environment must have the necessary FPGA toolchain and Makefiles for the
    specified boards.
"""

import os
import subprocess
from core.board_defines import DEFINES_BY_BOARD


CURRENT_DIR = os.getcwd()

VIVADO_BOARDS = [
    'xilinx_vc709',
    'digilent_arty_a7_100t',
    'digilent_nexys4_ddr',
    'opensdrlab_kintex7',
]

YOSYS_BOARDS = [
    'colorlight_i9',
]

GOWIN_BOARDS = [
    'tangnano_20k',
    'tangnano_9k',
]


def write_defines(board_name, filename='processor_ci_defines.vh'):
    if board_name not in DEFINES_BY_BOARD:
        raise ValueError(f"Board '{board_name}' not found.")

    with open(filename, 'w') as f:
        f.write(DEFINES_BY_BOARD[board_name])
    print(f"File '{filename}' generated for board: '{board_name}'.")


def get_vivado_prefix(vhdl: bool, sverilog: bool) -> str:
    """
    Determines the file prefix command for Vivado based on the file type.

    Args:
        vhdl (bool): Whether the file is a VHDL file.
        sverilog (bool): Whether the file is a SystemVerilog file.

    Returns:
        str: The prefix command to use.
    """
    if vhdl:
        return 'read_vhdl -vhdl2008'
    if sverilog:
        return 'read_verilog -sv'
    return 'read_verilog'


def get_yosys_prefix(vhdl: bool, sverilog: bool) -> str:
    """
    Determines the file prefix command for Yosys based on the file type.

    Args:
        vhdl (bool): Whether the file is a VHDL file.
        sverilog (bool): Whether the file is a SystemVerilog file.

    Returns:
        str: The prefix command to use.
    """
    if vhdl:
        return 'yosys ghdl -a'
    if sverilog:
        return 'yosys read_systemverilog -defer -I./'
    return 'yosys read_verilog'


def get_gowin_prefix() -> str:
    """
    Determines the file prefix command for Gowin based on the file type.

    Args:
        vhdl (bool): Whether the file is a VHDL file.
        sverilog (bool): Whether the file is a SystemVerilog file.

    Returns:
        str: The prefix command to use.
    """
    return 'add_file'


def get_quartus_prefix(vhdl: bool, sverilog: bool) -> str:
    """
    Determines the file prefix command for Quartus based on the file type.

    Args:
        vhdl (bool): Whether the file is a VHDL file.
        sverilog (bool): Whether the file is a SystemVerilog file.

    Returns:
        str: The prefix command to use.
    """
    if vhdl:
        return 'vcom'
    if sverilog:
        return 'vlog'
    return 'vlog'


def get_prefix(board: str, vhdl: bool, sverilog: bool) -> str:
    """
    Determines the file prefix command based on the target board and file type.

    Args:
        board (str): The name of the board.
        vhdl (bool): Whether the file is a VHDL file.
        sverilog (bool): Whether the file is a SystemVerilog file.

    Returns:
        str: The prefix command to use.
    """
    if board in VIVADO_BOARDS:
        return get_vivado_prefix(vhdl, sverilog)

    if board in YOSYS_BOARDS:
        return get_yosys_prefix(vhdl, sverilog)

    if board in GOWIN_BOARDS:
        return get_gowin_prefix()

    return get_quartus_prefix(vhdl, sverilog)


def make_build_file(config: dict, board: str, toolchain_path: str) -> str:
    """
    Generates a build script for the specified board and configuration.

    Args:
        config (dict): Configuration dictionary with file details.
        board (str): The name of the board.
        toolchain_path (str): Path to the toolchain directory.

    Returns:
        str: The path to the generated build script.

    Raises:
        FileNotFoundError: If the base configuration file does not exist.
        ValueError: If the base configuration file cannot be read.
    """
    if toolchain_path[-1] == '/':
        toolchain_path = toolchain_path[:-1]

    base_config_path = (
        f'{toolchain_path}/processor_ci/build_scripts/{board}.tcl'
    )

    if not os.path.exists(base_config_path):
        raise FileNotFoundError(
            f'The configuration file {base_config_path} was not found.'
        )

    base_config = None

    with open(base_config_path, 'r', encoding='utf-8') as file:
        base_config = file.read()

    if not base_config:
        raise ValueError(
            f'Unable to read the configuration file {base_config_path}.'
        )

    final_config_path = CURRENT_DIR + f'/build_{board}.tcl'

    exist_sv_file = False
    include_dirs_str = ' '.join(
        f'-I{CURRENT_DIR}/{d}' for d in config['include_dirs']
    )

    include_dirs_str_vivado = ''

    write_defines(board, 'processor_ci_defines.vh')

    with open(final_config_path, 'w', encoding='utf-8') as file:
        prefix = get_prefix(board, False, True)
        file.write(
            prefix
            + f' {toolchain_path}/processor_ci/rtl/{config["folder"]}.sv\n'
        )

        for i in config['files']:
            is_sv_file = i.endswith('.sv')
            prefix = get_prefix(
                board, vhdl=i.endswith('.vhd'), sverilog=is_sv_file
            )
            exist_sv_file = exist_sv_file or is_sv_file
            if is_sv_file and board in YOSYS_BOARDS:
                file.write(
                    prefix + f' {include_dirs_str} {CURRENT_DIR}/' + i + '\n'
                )
            else:
                file.write(prefix + f' {CURRENT_DIR}/' + i + '\n')

        if board in VIVADO_BOARDS and config['include_dirs'] != []:
            include_dirs_str_vivado = 'set_property include_dirs [list '
            for i in config['include_dirs']:
                include_dirs_str_vivado += f'"{CURRENT_DIR}/{i}" '
            include_dirs_str_vivado += '] [get_filesets sources_1]\n'
            file.write(include_dirs_str_vivado)

        file.write(base_config)

    print(f'Final configuration file generated at {final_config_path}')

    return final_config_path


def build(build_script_path: str, board: str, toolchain_path: str) -> None:
    """
    Executes the build process using the specified build script and makefile.

    Args:
        build_script_path (str): Path to the build script.
        board (str): The name of the board.
        toolchain_path (str): Path to the toolchain directory.

    Returns:
        None

    Raises:
        subprocess.CalledProcessError: If the build process fails.
    """
    if toolchain_path[-1] == '/':
        toolchain_path = toolchain_path[:-1]

    makefile_path = f'{toolchain_path}/processor_ci/makefiles/{board}.mk'

    # Set the BUILD_SCRIPT variable before running the make command
    with subprocess.Popen(
        [
            'make',
            '-f',
            makefile_path,
            f'BUILD_SCRIPT={build_script_path}',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        # Capture the output and errors
        stdout, stderr = process.communicate()

        # Check the status of the execution
        if process.returncode == 0:
            print('Makefile executed successfully.')
            print('Makefile output:')
            print(stdout)
        else:
            print('Error executing Makefile.')
            print(stderr)
            raise subprocess.CalledProcessError(process.returncode, 'make')


def flash(board: str, toolchain_path: str) -> None:
    """
    Flashes the generated bitstream to the target board.

    Args:
        board (str): The name of the board.
        toolchain_path (str): Path to the toolchain directory.

    Returns:
        None

    Raises:
        subprocess.CalledProcessError: If the flashing process fails.
    """
    if toolchain_path[-1] == '/':
        toolchain_path = toolchain_path[:-1]

    makefile_path = f'{toolchain_path}/processor_ci/makefiles/{board}.mk'

    with subprocess.Popen(
        ['make', '-f', makefile_path, 'load'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        # Capture the output and errors
        stdout, stderr = process.communicate()

        # Check the status of the execution
        if process.returncode == 0:
            print('Makefile executed successfully.')
            print('Makefile output:')
            print(stdout)
        else:
            print('Error executing Makefile.')
            print(stderr)
            raise subprocess.CalledProcessError(process.returncode, 'make')
