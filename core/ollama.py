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
    Parses a text to extract a list of filtered files.

    Uses a regular expression to locate and capture a list of files present
    in a string formatted as `filtered_files: [<file list>]`.
    Cleans up spaces and unnecessary characters before returning the results.

    Args:
        text (str): The text to be parsed to find the filtered file list.

    Returns:
        list: A list containing the names of filtered files.
              Returns an empty list if no files are found.
    """
    match = re.search(r'filtered_files:\s*\[\s*(.*?)\s*\]', text, re.DOTALL)

    if match:
        file_list_str = match.group(1)
        file_list = [
            file.strip().strip("'") for file in file_list_str.split(',')
        ]
        return file_list

    return []


def remove_top_module(text: str) -> str:
    """
    Extracts the name of the top module from a given text.

    Uses a regular expression to locate and capture a line following the format
    `top_module: <module_name>`. If found, it returns the module name.

    Args:
        text (str): The text to be parsed to find the top module.

    Returns:
        str: The name of the top module extracted from the text.
             Returns an empty string if no top module is found.
    """
    match = re.search(r'top_module:\s*(\S+)', text)

    if match:
        top_module = match.group(1)
        return top_module

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

    Returns:
        list: A list containing the names of the files relevant to the processor.

    Raises:
        NameError: If an error occurs during the language model query.
    """
    prompt = f"""
    Processors are generally divided into one or more modules; for example, I can have a module for the ALU, one for the register bank, etc. 
    The files below are the hardware description language files for a processor and its peripherals. 
    Additionally, we have a list of modules present in the processor (approximately, some modules might be missing) and which files they are in, 
    along with their dependency tree. The provided data has two categories: sim_files and files. 
    The sim_files are testbench and verification files (usually containing terms like tests, tb, testbench, among others in the name), 
    while the files are the remaining files, including unnecessary ones such as SoC, peripherals (memory, GPIO, UART, etc.). 
    Based on this, keep only the files that you deem relevant to a processor and return them in a Python list. 
    Remember to ignore memory files such as ram.v or ram.vhdl, peripheral files, caches files, pll files, bus files, board and FPGA files, debug files, among others. 
    Keep only the processor-related files. Return files in template: filtered_files: [<result>].

    TIP: generally directories with names like rtl, core, src, project_name, etc., usually have the processor files. Files with the project name are often processor files.
    All processors have at least one useful file

    Return only the list of files in the requested template, excluding any additional files and comments.

    project_name: {repo_name},
    sim_files: [{sim_files}],
    files: [{files}],
    modules: [{modules}]
    tree: [{tree}]
    """

    ok, response = send_prompt(prompt, model)

    if not ok:
        raise NameError('Erro ao consultar modelo')

    print(response)

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

    Returns:
        str: The name of the processor's top module.

    Raises:
        NameError: If an error occurs during the language model query.
    """
    prompt = f"""
    Processors are generally divided into one or more modules; for example, I can have a module for the ALU, one for the register bank, etc. 
    The files below are the hardware description language files for a processor and its peripherals. 
    Additionally, we have a list of modules present in the processor (approximately, some modules might be missing), and which files they are in, along with their dependency tree. 
    The provided data has two categories: sim_files and files. The sim_files are testbench and verification files (usually containing terms like tests, tb, testbench, among others in the name), 
    while the files are the remaining files, including unnecessary ones such as SoC and peripherals (memory, GPIO, UART, etc.). Based on this, find the processor's top module—remember, the processor's, not the SoC's.
    Return the top module in the following template: top_module: <result>.

    project_name: {repo_name},
    sim_files: [{sim_files}],
    files: [{files}],
    modules: [{modules}]
    tree: [{tree}]
    """

    ok, response = send_prompt(prompt, model)

    if not ok:
        raise NameError('Erro ao consultar modelo')

    # print(response)

    return remove_top_module(response)


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

    with open('rtl/Risco-5.v', 'r', encoding='utf-8') as example_file:
        example = example_file.read()

    template_file.close()
    top_module_file_.close()
    example_file.close()

    prompt = f"""
    In the context of processor verification, we use a hardware infrastructure to verify the processor. 
    Both the processor and the infrastructure are hardware described in hardware description language (HDL), in our case Verilog. 
    The processor connects to this infrastructure through a Verilog module that instantiates the infrastructure and the processor, 
    making the necessary connections and adaptations. Below is an example of such a connection. Based on this example, 
    the provided template, and the processor's top module, make the necessary connections and adaptations. 
    Pay attention to details such as whether the processor has two memories or only one, if it always has the read signal enabled and only sends the write signal, 
    among others. After this process, return the complete Verilog file based on the template.
    
    example file: 
    {example}

    template file: 
    {template}

    processor top file:
    {top_module_content}

    """

    ok, response = send_prompt(prompt, model)

    if not ok:
        raise NameError('Erro ao consultar modelo')

    if os.path.exists(f'rtl/{processor_name}.v'):
        processor_name = f'{processor_name}_{time.time()}'

    with open(f'rtl/{processor_name}.v', 'w', encoding='utf-8') as final_file:
        final_file.write(response)
        final_file.close()
