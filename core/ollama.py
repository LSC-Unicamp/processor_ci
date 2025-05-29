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


def extract_code_block(llm_response: str) -> str:
    """
    Extracts the first code block delimited by triple backticks (```) from the LLM response.

    Args:
        llm_response (str): Full text response from the LLM.

    Returns:
        str: Content inside the first ``` ``` code block found, without backticks.
             Returns empty string if no code block is found.
    """
    pattern = re.compile(r'```(?:\n)?(.*?)(?:\n)?```', re.DOTALL)
    match = pattern.search(llm_response)
    if match:
        return match.group(1).strip()
    return ''


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


def extract_bus_interface(llm_response: str) -> str:
    """
    Extracts the bus interface type from the LLM response.

    Expected format in response:
        bus_interface: <wishbone | axi4 | axi4_lite | ahb | avalon | custom>

    Args:
        llm_response (str): Full text response from the LLM.

    Returns:
        str: The identified bus interface name in lowercase (e.g., "axi4", "wishbone", "custom").
             Returns empty string if no valid format is found.
    """
    pattern = re.compile(
        r'bus_interface:\s*(wishbone|axi4|axi4_lite|ahb|avalon|custom)',
        re.IGNORECASE,
    )
    match = pattern.search(llm_response)
    if match:
        return match.group(1).lower()
    return ''


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
    Processors are typically divided into multiple modules, such as an ALU, register file, control unit, cache, among others. Below are the processor data, including:

    - project_name: {repo_name}  
    - sim_files: {sim_files}  
    - files: {files}  
    - modules: {modules}  

    Your task is to return **only the files directly related to the processor**. Exclude files related to peripherals, SoC, FPGA, wrappers, or specific implementations. Follow these rules:

    - Directories named `rtl`, `core`, `src`, or containing the project name usually include processor files.
    - Files named after the project are often essential.
    - Do not include files listed in `sim_files`.
    - Every processor must have at least one relevant file.

    Expected output format (no comments or explanations):  
    filtered_files = [<list_of_files>]
    """

    print(f'\033[32m[INFO] Consultando modelo: {model}\033[0m')

    ok, response = send_prompt(prompt, model)

    if not ok:
        raise NameError('\033[31mErro ao consultar modelo\033[0m')

    print(f'\033[32m[INFO] Resposta do modelo: {response}\033[0m')

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
    Processors are made of modules like ALU, register file, control unit, and cache. You are given HDL files and related data for a processor project, including:

    - project_name: {repo_name}  
    - sim_files: {sim_files}  
    - files: {files}  
    - modules: {modules}   

    Task:  
    Find the top module of the processor core (not the SoC). This is the main module that connects core components like ALU, registers, and cache.

    Rules:  
    - Use module names, file names, and dependencies to identify the top processor module.  
    - Ignore testbenches, SoC modules, peripherals (e.g., memory, UART, GPIO), and debug modules.  
    - Exclude wrappers like 'top' if they include peripherals or other non-core elements.  
    - The top module name might match the project name or be something like 'core', but this is only a hint, not a requirement.

    Output format:  
    Return only this, with no comments:  
    top_module: <result>
    """

    print(f'\033[32m[INFO] Consultando modelo: {model}\033[0m')

    ok, response = send_prompt(prompt, model)

    if not ok:
        raise NameError('\033[31mErro ao consultar modelo\033[0m')

    print(f'\033[32m[INFO] Resposta do modelo: {response}\033[0m')

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
    with open('rtl/template.sv', 'r', encoding='utf-8') as template_file:
        template = template_file.read()

    with open(
        f'temp/{processor_name}/{top_module_file}', 'r', encoding='utf-8'
    ) as top_module_file_:
        top_module_content = top_module_file_.read()

    with open('rtl/tinyriscv.sv', 'r', encoding='utf-8') as example_file:
        example = example_file.read()

    template_file.close()
    top_module_file_.close()
    example_file.close()

    prompt = f"""
    The file below is the top module of a processor.
    Based on the module’s inputs, outputs, and parameters, please generate an instantiation of this processor module.

    - Top module content:
    {top_module_content}

    Requirements:
    - Provide only the instantiation code.
    - Use this format:
    ```
    instancia #(...) u\_dut ( ... );

    ```
    - Include all ports and parameters exactly as declared in the module.
    - Do not add any comments, explanations, or extra text.
    """

    print(f'\033[32m[INFO] Consultando modelo: {model}\033[0m')

    ok, response = send_prompt(prompt, model)

    print(f'\033[32m[INFO] Resposta do modelo: {response}\033[0m')
    top_model = extract_code_block(response)

    if not top_model:
        raise NameError('\033[31mErro ao extrair bloco de código\033[0m')

    prompt = f"""
    Given the processor instantiation below, determine whether it follows a known bus interface standard (e.g., Wishbone, AXI4, AXI4-Lite, AHB, Avalon) or if it uses a fully custom interface.

    Instantiation:

    {top_model}

    Task:
    - Identify if the instantiation matches any standard bus interface.
    - If it does, specify which one.
    - If not, state that it uses a custom interface.

    Output format (only this, no comments or explanations):
    ```
    bus\_interface: \<wishbone | axi4 | axi4\_lite | ahb | avalon | custom>
    ```
    """

    print(f'\033[32m[INFO] Consultando modelo: {model}\033[0m')
    ok, response = send_prompt(prompt, model)
    if not ok:
        raise NameError('\033[31mErro ao consultar modelo\033[0m')
    print(f'\033[32m[INFO] Resposta do modelo: {response}\033[0m')

    bus_interface = re.search(r'bus_interface:\s*(\w+)', response)
    bus_interface = bus_interface.group(1).strip()

    print(
        f'\033[32m[INFO] Interface de barramento identificada: {bus_interface}\033[0m'
    )

    # criar pasta rlt_{model} se não existir

    if not os.path.exists(f'models_rtls/rtl_{model}'):
        os.makedirs(f'models_rtls/rtl_{model}')

    if os.path.exists(f'models_rtls/rtl_{model}/{processor_name}.sv'):
        processor_name = f'{processor_name}_{time.time()}'

    template = template.replace('endmodule', '')

    with open(
        f'models_rtls/rtl_{model}/{processor_name}.sv', 'w', encoding='utf-8'
    ) as final_file:
        final_file.write(f'// Generated by {model}\n')
        final_file.write(f'// Processor: {processor_name}\n')
        final_file.write(f'// Bus Interface: {bus_interface}\n\n')
        final_file.write(template)
        final_file.write(top_model)
        final_file.write('\n\nendmodule\n')
        final_file.close()
