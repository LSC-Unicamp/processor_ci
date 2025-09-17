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
        if module['module'] == top_module:
            return module['file']
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
    processor_name = config['name']
    top_module = config['top_module']
    
    if use_ollama and top_module:
        # Try to get the top module file from the configuration
        modules = config['files']
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
    copy_hardware_template(processor_name)
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
    return copy_hardware_template(name, template_path, output_dir)


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
        '-n', 
        '--name', 
        type=str,
        help='Name of the processor'
    )
    parser.add_argument(
        '-c', 
        '--config', 
        type=str,
        help='Path to the processor configuration file'
    )
    parser.add_argument(
        '-d', 
        '--config-dir', 
        type=str,
        help='Directory containing processor configuration files (generates templates for all)'
    )
    parser.add_argument(
        '-o', 
        '--output', 
        type=str, 
        default='rtl/',
        help='Output directory for the template'
    )
    parser.add_argument(
        '-t', 
        '--template', 
        type=str, 
        default='rtl/template.sv',
        help='Base template file to use'
    )
    parser.add_argument(
        '-u',
        '--use-ollama', 
        action='store_true',
        help='Use OLLAMA for enhanced template generation'
    )
    parser.add_argument(
        '-m', 
        '--model', 
        type=str, 
        default='qwen2.5:32b',
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
