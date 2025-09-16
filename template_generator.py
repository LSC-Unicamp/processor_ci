"""
SystemVerilog Template Generator

This script generates SystemVerilog templates for processor cores.
It analyzes existing processor configurations and creates appropriate templates.

Main Functions:
--------------
- **generate_template**: Creates a SystemVerilog template for a processor
- **copy_hardware_template**: Copies a base template and renames it
- **get_top_module_file**: Retrieves the file path of a specific top module

Command-Line Interface:
-----------------------
- `-n`, `--name`: Name of the processor (required)
- `-c`, `--config`: Path to the processor configuration file
- `-o`, `--output`: Output directory for the template (default: 'rtl/')
- `-t`, `--template`: Base template file to use (default: 'rtl/template.sv')

Usage:
------
python template_generator.py -n processor_name -c config/processor.json
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any, List
from core.log import print_green, print_red, print_yellow
from core.ollama import generate_top_file


def get_top_module_file(modules: List[Dict[str, str]], top_module: str) -> str:
    """
    Retrieves the file path of the specified top module from a list of module dictionaries.

    Args:
        modules (List[Dict[str, str]]): A list of dictionaries where each dictionary
            contains the module name and its file path.
        top_module (str): The name of the top module to find.

    Returns:
        str: The file path of the top module if found, or an empty string otherwise.
    """
    for module in modules:
        if module.get('module') == top_module:
            return module.get('file', '')
    return ''


def copy_hardware_template(repo_name: str, template_path: str = 'rtl/template.sv', output_dir: str = 'rtl/') -> str:
    """
    Copies a hardware template file to a new destination, renaming it based on the repository name.

    Args:
        repo_name (str): The name of the repository to use in the destination file name.
        template_path (str): Path to the template file.
        output_dir (str): Output directory for the new template.

    Returns:
        str: Path to the created template file.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Destination file path
    dest = os.path.join(output_dir, f'{repo_name}.sv')

    if os.path.exists(dest):
        print_yellow(f'[WARN] Template file {dest} already exists')
        return dest

    if not os.path.exists(template_path):
        print_red(f'[ERROR] Template file {template_path} not found')
        # Create a basic template if the base template doesn't exist
        create_basic_template(dest, repo_name)
        return dest

    # Copy the template
    shutil.copy(template_path, dest)
    print_green(f'[LOG] Template copied to {dest}')
    
    return dest


def create_basic_template(dest_path: str, module_name: str) -> None:
    """
    Creates a basic SystemVerilog template when no base template is available.
    
    Args:
        dest_path (str): Destination path for the template.
        module_name (str): Name of the module.
    """
    basic_template = f'''/*
 * {module_name.upper()} Processor Core Template
 * 
 * This is a basic template for the {module_name} processor core.
 * Customize this template according to your processor's specifications.
 */

module {module_name} #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32
) (
    input  wire                    clk,
    input  wire                    rst_n,
    
    // Instruction Memory Interface
    output wire [ADDR_WIDTH-1:0]   imem_addr,
    input  wire [DATA_WIDTH-1:0]   imem_rdata,
    output wire                    imem_req,
    input  wire                    imem_gnt,
    input  wire                    imem_rvalid,
    
    // Data Memory Interface
    output wire [ADDR_WIDTH-1:0]   dmem_addr,
    output wire [DATA_WIDTH-1:0]   dmem_wdata,
    input  wire [DATA_WIDTH-1:0]   dmem_rdata,
    output wire                    dmem_we,
    output wire [3:0]              dmem_be,
    output wire                    dmem_req,
    input  wire                    dmem_gnt,
    input  wire                    dmem_rvalid,
    
    // Interrupt Interface
    input  wire                    irq,
    output wire                    irq_ack,
    
    // Debug Interface (optional)
    input  wire                    debug_req,
    output wire                    debug_ack
);

    // Internal signals
    reg [DATA_WIDTH-1:0] pc;
    reg [DATA_WIDTH-1:0] instruction;
    reg [DATA_WIDTH-1:0] registers [0:31];
    
    // State machine states
    typedef enum logic [2:0] {{
        FETCH,
        DECODE,
        EXECUTE,
        MEMORY,
        WRITEBACK
    }} state_t;
    
    state_t current_state, next_state;
    
    // Reset logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= FETCH;
            pc <= '0;
            // Initialize registers
            for (int i = 0; i < 32; i++) begin
                registers[i] <= '0;
            end
        end else begin
            current_state <= next_state;
        end
    end
    
    // State machine logic
    always_comb begin
        next_state = current_state;
        
        case (current_state)
            FETCH: begin
                // Implement instruction fetch logic
                next_state = DECODE;
            end
            
            DECODE: begin
                // Implement instruction decode logic
                next_state = EXECUTE;
            end
            
            EXECUTE: begin
                // Implement instruction execution logic
                next_state = MEMORY;
            end
            
            MEMORY: begin
                // Implement memory access logic
                next_state = WRITEBACK;
            end
            
            WRITEBACK: begin
                // Implement register writeback logic
                next_state = FETCH;
            end
            
            default: begin
                next_state = FETCH;
            end
        endcase
    end
    
    // Instruction memory interface
    assign imem_addr = pc;
    assign imem_req = (current_state == FETCH);
    
    // Data memory interface (placeholder)
    assign dmem_addr = '0;
    assign dmem_wdata = '0;
    assign dmem_we = '0;
    assign dmem_be = 4'b1111;
    assign dmem_req = '0;
    
    // Interrupt handling (placeholder)
    assign irq_ack = '0;
    
    // Debug interface (placeholder)
    assign debug_ack = debug_req;

endmodule
'''
    
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(basic_template)
    
    print_green(f'[LOG] Basic template created at {dest_path}')


def load_processor_config(config_path: str) -> Dict[str, Any]:
    """
    Load processor configuration from JSON file.
    
    Args:
        config_path (str): Path to the configuration file.
    
    Returns:
        Dict[str, Any]: Processor configuration.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print_green(f'[LOG] Configuration loaded from {config_path}')
        return config
    except FileNotFoundError:
        print_red(f'[ERROR] Configuration file {config_path} not found')
        return {}
    except json.JSONDecodeError as e:
        print_red(f'[ERROR] Invalid JSON in configuration file: {e}')
        return {}


def generate_enhanced_template(config: Dict[str, Any], output_path: str, use_ollama: bool = False, model: str = 'qwen2.5:32b') -> str:
    """
    Generate an enhanced template based on processor configuration.
    
    Args:
        config (Dict[str, Any]): Processor configuration.
        output_path (str): Path for the output template.
        use_ollama (bool): Whether to use OLLAMA for template generation.
        model (str): OLLAMA model to use.
    
    Returns:
        str: Path to the generated template.
    """
    processor_name = config.get('name', 'processor')
    top_module = config.get('top_module', processor_name)
    
    if use_ollama and top_module:
        # Try to get the top module file from the configuration
        modules = config.get('modules', [])
        if modules:
            top_module_file = get_top_module_file(modules, top_module)
            if top_module_file:
                try:
                    print_green('[LOG] Using OLLAMA to generate enhanced template')
                    generate_top_file(top_module_file, processor_name, model=model)
                    return output_path
                except Exception as e:
                    print_yellow(f'[WARN] OLLAMA template generation failed: {e}')
    
    # Fallback to basic template creation
    create_basic_template(output_path, processor_name)
    return output_path


def generate_template(
    name: str,
    config_path: str = None,
    output_dir: str = 'rtl/',
    template_path: str = 'rtl/template.sv',
    use_ollama: bool = False,
    model: str = 'qwen2.5:32b'
) -> str:
    """
    Main function to generate a processor template.
    
    Args:
        name (str): Name of the processor.
        config_path (str): Path to the processor configuration file.
        output_dir (str): Output directory for the template.
        template_path (str): Base template file to use.
        use_ollama (bool): Whether to use OLLAMA for enhanced template generation.
        model (str): OLLAMA model to use.
    
    Returns:
        str: Path to the generated template.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f'{name}.sv')
    
    # If we have a configuration file, try to generate enhanced template
    if config_path and os.path.exists(config_path):
        config = load_processor_config(config_path)
        if config:
            return generate_enhanced_template(config, output_path, use_ollama, model)
    
    # Fallback to basic template copy/creation
    if os.path.exists(template_path):
        return copy_hardware_template(name, template_path, output_dir)
    else:
        create_basic_template(output_path, name)
        return output_path


def generate_template_from_config_dir(config_dir: str, output_dir: str = 'rtl/') -> List[str]:
    """
    Generate templates for all processors in a configuration directory.
    
    Args:
        config_dir (str): Directory containing processor configuration files.
        output_dir (str): Output directory for templates.
    
    Returns:
        List[str]: List of generated template file paths.
    """
    if not os.path.exists(config_dir):
        print_red(f'[ERROR] Configuration directory {config_dir} not found')
        return []
    
    generated_templates = []
    
    for file in os.listdir(config_dir):
        if file.endswith('.json') and file != 'config.json':  # Skip central config file
            config_path = os.path.join(config_dir, file)
            processor_name = file.replace('.json', '')
            
            print_green(f'[LOG] Generating template for {processor_name}')
            
            template_path = generate_template(
                processor_name,
                config_path,
                output_dir
            )
            
            generated_templates.append(template_path)
            print_green(f'[LOG] Template generated: {template_path}')
    
    return generated_templates


def main() -> None:
    """Main entry point for the template generator."""
    parser = argparse.ArgumentParser(description='Generate SystemVerilog templates for processors')

    parser.add_argument(
        '-n', '--name', type=str,
        help='Name of the processor'
    )
    parser.add_argument(
        '-c', '--config', type=str,
        help='Path to the processor configuration file'
    )
    parser.add_argument(
        '-d', '--config-dir', type=str,
        help='Directory containing processor configuration files (generates templates for all)'
    )
    parser.add_argument(
        '-o', '--output', type=str, default='rtl/',
        help='Output directory for the template'
    )
    parser.add_argument(
        '-t', '--template', type=str, default='rtl/template.sv',
        help='Base template file to use'
    )
    parser.add_argument(
        '--use-ollama', action='store_true',
        help='Use OLLAMA for enhanced template generation'
    )
    parser.add_argument(
        '-m', '--model', type=str, default='qwen2.5:32b',
        help='OLLAMA model to use'
    )

    args = parser.parse_args()

    try:
        if args.config_dir:
            # Generate templates for all processors in directory
            templates = generate_template_from_config_dir(args.config_dir, args.output)
            print_green(f'[SUCCESS] Generated {len(templates)} templates')
            for template in templates:
                print(f'  - {template}')
                
        elif args.name:
            # Generate template for specific processor
            template_path = generate_template(
                args.name,
                args.config,
                args.output,
                args.template,
                args.use_ollama,
                args.model
            )
            print_green(f'[SUCCESS] Template generated: {template_path}')
            
        else:
            print_red('[ERROR] Either --name or --config-dir must be specified')
            parser.print_help()
            return 1
            
    except Exception as e:
        print_red(f'[ERROR] {e}')
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
