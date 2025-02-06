"""
This script contains utilities for interacting with a language model server to perform operations
on processor-related hardware description language (HDL) files. It provides functions for sending
prompts, parsing responses, and generating outputs relevant to processor verification and design.

Features:
- **Server Communication**: Interact with the specified language model server to process prompts.
- **File Filtering**: Identify and filter files relevant to processor functionality.
- **Top Module Detection**: Extract the processor's top module for further use in synthesis or
    simulation.
- **Verilog File Generation**: Automatically generate Verilog files to connect the processor with
  verification infrastructures.

Modules:
- **`send_prompt`**: Sends a prompt to the language model and returns the response.
- **`parse_filtered_files`**: Parses text to extract a list of filtered HDL files.
- **`remove_top_module`**: Extracts the name of the top module from the model's response.
- **`get_filtered_files_list`**: Filters processor-relevant files using model analysis.
- **`get_top_module`**: Identifies the processor's top module based on file data and dependencies.
- **`generate_top_file`**: Creates a Verilog file for processor and verification infrastructure
    integration.

Dependencies:
- `ollama`: A client library for interacting with the language model.
- Standard Python libraries: `os`, `re`, and `time`.

Configuration:
- `SERVER_URL`: Specifies the server's URL for the language model.

Usage:
1. Adjust the `SERVER_URL` to point to the correct language model server.
2. Use the provided functions to filter files, identify the top module, and generate necessary
    Verilog files.
3. Outputs can be used in HDL simulations, synthesis, and verification.

Note:
- Ensure the server is running and accessible.
- All file paths and directory structures must match the expected inputs for successful operations.
"""

import os
import re
import ast
import time
from ollama import Client

SERVER_URL = os.getenv('SERVER_URL', 'http://127.0.0.1:11434')

client = Client(host=SERVER_URL)


def send_prompt(prompt: str, model: str = 'qwen2.5:32b') -> tuple[bool, str]:
    """
    Sends a prompt to the specified server and receives the model's response.

    Args:
        prompt (str): The prompt to be sent to the model.
        model (str, optional): The model to use. Default is 'qwen2.5:32b'.

    Returns:
        tuple: A tuple containing a boolean value (indicating success)
               and the model's response as a string.
    """
    response = client.generate(prompt=prompt, model=model)

    if not response or 'response' not in response:
        return 0, ''

    return 1, response['response']


def parse_filtered_files(text: str) -> list:
    """
    Parses a text to extract a list of filtered files from specific keys.

    Searches for keys like `filtered_files`, `core_files`, or `relevant_files`,
    and extracts a list of files present in the associated list.
    Cleans up spaces and unnecessary characters before returning the results.

    Args:
        text (str): The text to be parsed to find the file list.

    Returns:
        list: A list containing the names of files.
              Returns an empty list if no files are found or parsing fails.
    """
    keys = ['filtered_files', 'core_files', 'relevant_files']

    for key in keys:
        match = re.search(rf'{key}\s*=\s*\[.*?\]', text, re.DOTALL)
        if match:
            try:
                # Safely evaluate the list portion after splitting by '='
                file_list_str = match.group(0).split('=', 1)[1].strip()
                files = ast.literal_eval(file_list_str)
                return [file.strip() for file in files]
            except (SyntaxError, ValueError):
                # Return an empty list if parsing fails
                return []

    return []


def extract_top_module(text: str) -> str:
    """
    Extracts the name of the top module from a given text.

    Parses the input to find the top module based on multiple formats:
    1. A line in the format: `top_module: <module_name>`.
    2. A list-style format: `top: ['<module_name>']`.
    3. Explicit statement: `Therefore, the answer is: <module_name>`.
    4. A valid standalone module name on the first line of the text.

    Args:
        text (str): The text to be parsed to find the top module.

    Returns:
        str: The name of the top module, or an empty string if not found.
    """
    patterns = [
        r'top_module:\s*(\S+)',  # Pattern 1
        r'top:\s*\[\'?([a-zA-Z_]\w*)\'?\]',  # Pattern 2
        r'Therefore, the answer is:\s*(\S+)',  # Pattern 3
    ]

    # Try each pattern in order
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    # Check the first line for a standalone module name (Pattern 4)
    first_line = text.strip().splitlines()[0] if text.strip() else ''
    if re.match(r'^[a-zA-Z_]\w*$', first_line):
        return first_line

    return ''


def get_filtered_files_list(
    files: list[str],
    sim_files: list[str],
    modules: list[str],
    tree,
    repo_name: str,
    model: str = 'qwen2.5:32b',
) -> list[str]:
    """
    Generates a list of files relevant to a processor based on the provided data.

    This function uses a language model to analyze lists of files, modules,
    dependency trees, and repository data, filtering out irrelevant files such as
    those related to peripherals, memories, or debugging. It returns only the files
    directly related to the processor.

    Args:
        files (list): List of available files.
        sim_files (list): List of simulation and test-related files.
        modules (list): List of modules present in the processor.
        tree (list): Dependency structure of the modules.
        repo_name (str): Name of the project repository.
        model (str, optional): The model to use. Default is 'qwen2.5:32b'.

    Returns:
        list: A list containing the names of the files relevant to the processor.

    Raises:
        NameError: If an error occurs during the language model query.
    """
    prompt = f"""
    Processors are typically divided into multiple modules, such as an ALU module, a register bank, and others. 
    The provided data includes hardware description language (HDL) files for a processor and its peripherals. 
    Additionally, we have a list of the processor's modules (approximately, as some might be missing), their corresponding files, and their dependency tree. 
    The data is categorized into two types: sim_files and files. 

    - **sim_files**: Testbench and verification files (often containing terms like 'test', 'tb', or 'testbench' in their names).
    - **files**: Remaining HDL files, including some unnecessary ones like SoC, peripherals (memory, GPIO, UART, etc.), PLL, board and FPGA-specific files, debug files, among others.

    Your task:
    1. Identify and keep only the files directly relevant to the processor.
    2. Exclude files related to peripherals (e.g., `ram.v`, `gpio.vhd`), memory, PLL, board/FPGA configuration, and debug functionalities.
    3. Use the directory structure as a hint: directories named `rtl`, `core`, `src`, or matching the project name usually contain processor-related files. 
    Files named after the project name are often essential processor files.
    4. Note that every processor must have at least one relevant file.

    **Return format:**  
    Return the filtered list of files in the following Python list template:  
    `filtered_files: [<result>]`

    **Important:** Do not include any comments, explanations, or unrelated files in the output. Provide only the requested list.

    Input data:
    project_name: {repo_name},
    sim_files: [{sim_files}],
    files: [{files}],
    modules: [{modules}],
    tree: [{tree}]
    """

    ok, response = send_prompt(prompt, model)

    if not ok:
        raise NameError('\033[31mErro ao consultar modelo\033[0m')

    return parse_filtered_files(response)


def get_top_module(
    files: list[str],
    sim_files: list[str],
    modules: list[str],
    tree,
    repo_name: str,
    model: str = 'qwen2.5:32b',
) -> str:
    """
    Identifies the processor's top module within a set of files.

    Uses a language model to analyze files, modules, dependency trees,
    and repository data to determine the processor's top module, ignoring
    other elements such as SoCs or peripherals.

    Args:
        files (list): List of available files.
        sim_files (list): List of simulation and test-related files.
        modules (list): List of modules present in the processor.
        tree (list): Dependency structure of the modules.
        repo_name (str): Name of the project repository.
        model (str, optional): The model to use. Default is 'qwen2.5:32b'.

    Returns:
        str: The name of the processor's top module.

    Raises:
        NameError: If an error occurs during the language model query.
    """
    prompt = f"""
    Processors are typically divided into multiple modules, such as an ALU module, a register bank, and others. 
    The provided data includes hardware description language (HDL) files for a processor and its peripherals. 
    Additionally, a list of modules present in the processor (approximately, as some might be missing) is provided, along with the files they belong to and their dependency tree.

    The data is categorized as follows:
    - **sim_files**: Testbench and verification files (commonly containing terms like 'test', 'tb', or 'testbench' in their names).
    - **files**: All other files, including unnecessary ones such as SoC files, peripheral-related files (e.g., memory, GPIO, UART), and others.

    Your task:
    1. Identify the **processor's top module**—specifically the processor's, not the SoC's.
    2. Use the list of modules, file names, and dependency tree as clues to locate the top module.
    3. Exclude:
    - Modules related to SoC, peripherals (e.g., memory, GPIO, UART), or debugging infrastructure.
    - Modules named `top` or equivalent generic wrappers if they merely instantiate the processor along with additional components (e.g., peripherals, SoC, or infrastructure).
    4. Focus on identifying the actual top module for the **processor core**, which serves as the main entry point and integrates core components like the ALU, registers, and caches.

    **Return format:**  
    Provide the name of the top module in the following template:  
    `top_module: <result>`

    **Important:** Do not include any comments, explanations, or unrelated information—return only the requested result.

    Input data:
    project_name: {repo_name},
    sim_files: [{sim_files}],
    files: [{files}],
    modules: [{modules}],
    tree: [{tree}]
    """

    ok, response = send_prompt(prompt, model)

    if not ok:
        raise NameError('\033[31mErro ao consultar modelo\033[0m')

    return extract_top_module(response)


def generate_top_file(
    top_module_file: str, processor_name: str, model: str = 'qwen2.5:32b'
) -> None:
    """
    Generates a Verilog file connecting a processor to a verification infrastructure.

    This function creates a Verilog module based on a template, the processor's
    top module file, and a provided example. It establishes the necessary connections
    between the processor and the verification infrastructure.

    Args:
        top_module_file (str): Path to the file containing the processor's top module.
        processor_name (str): Name of the processor.

    Returns:
        None: The result is saved in a Verilog file.

    Raises:
        NameError: If an error occurs during the language model query.
    """
    with open('rtl/template.v', 'r', encoding='utf-8') as template_file:
        template = template_file.read()

    with open(
        f'temp/{processor_name}/{top_module_file}', 'r', encoding='utf-8'
    ) as top_module_file_:
        top_module_content = top_module_file_.read()

    with open('rtl/tinyriscv.v', 'r', encoding='utf-8') as example_file:
        example = example_file.read()

    template_file.close()
    top_module_file_.close()
    example_file.close()

    prompt = f"""
    In the context of processor verification, a hardware infrastructure is used to verify the processor. 
    Both the processor and the verification infrastructure are described in hardware description language (HDL), specifically Verilog in this case. 
    The processor connects to this infrastructure via a Verilog module that instantiates both the processor and the infrastructure, 
    handling all necessary connections and adaptations.

    Your task:
    1. Use the provided **example** as a reference for how the connections and adaptations are typically implemented.
    2. Use the **template** as the base for your Verilog file.
    3. Analyze the **processor's top module** and make the necessary connections and adaptations.  
    - Pay close attention to processor-specific details, such as:
        - Whether the processor uses one or two memories.
        - How signals are handled (e.g., if the read signal is always enabled and only the write signal is controlled).
        - Any unique requirements of the processor or infrastructure.

    **Output format:**  
    Return the complete and updated Verilog file based on the **template**, with all necessary connections and adaptations made.

    **Input data:**  
    - Example file:
    {example}

    - Template file:
    {template}

    - Processor top module content:
    {top_module_content}
    """

    ok, response = send_prompt(prompt, model)

    if not ok:
        raise NameError('\033[31mErro ao consultar modelo\033[0m')

    # criar pasta rlt_{model} se não existir

    if not os.path.exists(f'models_rtls/rtl_{model}'):
        os.makedirs(f'models_rtls/rtl_{model}')

    if os.path.exists(f'models_rtls/rtl_{model}/{processor_name}.v'):
        processor_name = f'{processor_name}_{time.time()}'

    with open(
        f'models_rtls/rtl_{model}/{processor_name}.v', 'w', encoding='utf-8'
    ) as final_file:
        final_file.write(response)
        final_file.close()
