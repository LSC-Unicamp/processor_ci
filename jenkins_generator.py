"""
Jenkins Pipeline Generator

This script generates Jenkinsfiles for CI/CD pipelines targeting multiple FPGAs.
It reads processor configurations and creates appropriate Jenkins pipeline scripts.

Main Functions:
--------------
- **generate_jenkinsfile**: Creates a Jenkinsfile for a specific processor configuration
- **generate_all_pipelines**: Generates Jenkinsfiles for all processors in a configuration directory
- **create_pipeline_config**: Creates pipeline-specific configuration

Command-Line Interface:
-----------------------
- `-c`, `--config`: Path to a specific processor configuration file
- `-d`, `--config-dir`: Directory containing processor configuration files
- `-o`, `--output`: Output directory for Jenkinsfiles (default: 'jenkins_pipeline/')
- `-f`, `--fpgas`: Comma-separated list of target FPGAs
- `-s`, `--script-path`: Path to the main synthesis script

Usage:
------
# Generate Jenkinsfile for specific processor:
python jenkins_generator.py -c config/processor.json

# Generate Jenkinsfiles for all processors:
python jenkins_generator.py -d config/

# Generate with custom FPGA targets:
python jenkins_generator.py -d config/ -f "digilent_arty_a7_100t,xilinx_vc709"
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from core.config import load_config
from core.jenkins import generate_jenkinsfile
from core.log import print_green, print_red, print_yellow


# Default constants
DEFAULT_BASE_DIR = 'jenkins_pipeline/'
DEFAULT_FPGAS = [
    'digilent_arty_a7_100t',
    # Add more FPGAs as needed
    # 'colorlight_i9',
    # 'digilent_nexys4_ddr',
    # 'gowin_tangnano_20k',
    # 'xilinx_vc709',
]
DEFAULT_MAIN_SCRIPT_PATH = '/eda/processor_ci/main.py'


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


def create_pipeline_config(processor_config: Dict[str, Any], fpgas: List[str], script_path: str) -> Dict[str, Any]:
    """
    Create pipeline-specific configuration from processor configuration.
    
    Args:
        processor_config (Dict[str, Any]): Processor configuration.
        fpgas (List[str]): List of target FPGAs.
        script_path (str): Path to the main synthesis script.
    
    Returns:
        Dict[str, Any]: Pipeline configuration.
    """
    return {
        'processor': processor_config,
        'fpgas': fpgas,
        'script_path': script_path,
        'pipeline_name': f"{processor_config.get('name', 'processor')}_pipeline",
        'language_version': processor_config.get('language_version', '2005'),
        'extra_flags': processor_config.get('extra_flags', [])
    }


def generate_single_jenkinsfile(
    config_path: str,
    fpgas: List[str],
    script_path: str,
    output_dir: str
) -> str:
    """
    Generate a Jenkinsfile for a single processor configuration.
    
    Args:
        config_path (str): Path to the processor configuration file.
        fpgas (List[str]): List of target FPGAs.
        script_path (str): Path to the main synthesis script.
        output_dir (str): Output directory for the Jenkinsfile.
    
    Returns:
        str: Path to the generated Jenkinsfile.
    """
    config = load_processor_config(config_path)
    if not config:
        raise ValueError(f"Could not load configuration from {config_path}")
    
    processor_name = config.get('name', 'processor')
    language_version = config.get('language_version', '2005')
    extra_flags = config.get('extra_flags', [])
    
    print_green(f'[LOG] Generating Jenkinsfile for {processor_name}')
    
    # Generate the Jenkinsfile
    jenkinsfile_content = generate_jenkinsfile(
        config,
        fpgas,
        script_path,
        language_version,
        extra_flags
    )
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Write Jenkinsfile
    output_path = os.path.join(output_dir, f'{processor_name}.Jenkinsfile')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(jenkinsfile_content)
    
    print_green(f'[LOG] Jenkinsfile generated: {output_path}')
    return output_path


def generate_all_pipelines(
    config_dir: str,
    fpgas: List[str],
    script_path: str,
    output_dir: str
) -> List[str]:
    """
    Generate Jenkinsfiles for all processors in a configuration directory.
    
    Args:
        config_dir (str): Directory containing processor configuration files.
        fpgas (List[str]): List of target FPGAs.
        script_path (str): Path to the main synthesis script.
        output_dir (str): Output directory for Jenkinsfiles.
    
    Returns:
        List[str]: List of generated Jenkinsfile paths.
    """
    if not os.path.exists(config_dir):
        print_red(f'[ERROR] Configuration directory {config_dir} not found')
        raise FileNotFoundError(f'Configuration directory {config_dir} not found')

    files = os.listdir(config_dir)
    if not files:
        print_red(f'[ERROR] Configuration directory {config_dir} is empty')
        raise FileNotFoundError('Configuration directory is empty')

    generated_jenkinsfiles = []

    for file in files:
        if not file.endswith('.json'):
            print_yellow(f'[WARN] Skipping non-JSON file: {file}')
            continue
            
        # Skip central config file
        if file == 'config.json':
            print_yellow('[INFO] Skipping central config file')
            continue

        config_path = os.path.join(config_dir, file)
        processor_name = file.replace('.json', '')
        
        try:
            print_green(f'[LOG] Processing {processor_name}')
            
            jenkinsfile_path = generate_single_jenkinsfile(
                config_path,
                fpgas,
                script_path,
                output_dir
            )
            
            generated_jenkinsfiles.append(jenkinsfile_path)
            
        except Exception as e:
            print_red(f'[ERROR] Failed to generate Jenkinsfile for {processor_name}: {e}')
            continue

    print_green(f'[SUCCESS] Generated {len(generated_jenkinsfiles)} Jenkinsfiles')
    return generated_jenkinsfiles


def validate_fpga_list(fpga_string: str) -> List[str]:
    """
    Validate and parse FPGA list from command line argument.
    
    Args:
        fpga_string (str): Comma-separated list of FPGAs.
    
    Returns:
        List[str]: List of FPGA names.
    """
    fpgas = [fpga.strip() for fpga in fpga_string.split(',')]
    fpgas = [fpga for fpga in fpgas if fpga]  # Remove empty strings
    
    if not fpgas:
        print_yellow('[WARN] No FPGAs specified, using defaults')
        return DEFAULT_FPGAS
    
    print_green(f'[LOG] Target FPGAs: {fpgas}')
    return fpgas


def create_pipeline_summary(generated_files: List[str], output_dir: str) -> str:
    """
    Create a summary file listing all generated Jenkinsfiles.
    
    Args:
        generated_files (List[str]): List of generated Jenkinsfile paths.
        output_dir (str): Output directory.
    
    Returns:
        str: Path to the summary file.
    """
    summary_path = os.path.join(output_dir, 'pipeline_summary.txt')
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("Generated Jenkins Pipelines Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total pipelines generated: {len(generated_files)}\n\n")
        
        for i, jenkinsfile in enumerate(generated_files, 1):
            f.write(f"{i}. {os.path.basename(jenkinsfile)}\n")
            f.write(f"   Path: {jenkinsfile}\n\n")
    
    print_green(f'[LOG] Pipeline summary created: {summary_path}')
    return summary_path


def main() -> int:
    """Main entry point for the Jenkins generator."""
    parser = argparse.ArgumentParser(description='Generate Jenkins pipelines for processor CI')

    # Input options
    parser.add_argument(
        '-c', '--config', type=str,
        help='Path to a specific processor configuration file'
    )
    parser.add_argument(
        '-d', '--config-dir', type=str,
        help='Directory containing processor configuration files'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output', type=str, default=DEFAULT_BASE_DIR,
        help=f'Output directory for Jenkinsfiles (default: {DEFAULT_BASE_DIR})'
    )
    
    # Pipeline configuration
    parser.add_argument(
        '-f', '--fpgas', type=str,
        help='Comma-separated list of target FPGAs (e.g., "digilent_arty_a7_100t,xilinx_vc709")'
    )
    parser.add_argument(
        '-s', '--script-path', type=str, default=DEFAULT_MAIN_SCRIPT_PATH,
        help=f'Path to the main synthesis script (default: {DEFAULT_MAIN_SCRIPT_PATH})'
    )
    
    # Additional options
    parser.add_argument(
        '--summary', action='store_true',
        help='Create a summary file listing all generated pipelines'
    )

    args = parser.parse_args()

    try:
        # Validate FPGA list
        fpgas = validate_fpga_list(args.fpgas) if args.fpgas else DEFAULT_FPGAS
        
        generated_files = []

        if args.config:
            # Generate Jenkinsfile for specific processor
            if not os.path.exists(args.config):
                print_red(f'[ERROR] Configuration file {args.config} not found')
                return 1
                
            jenkinsfile_path = generate_single_jenkinsfile(
                args.config,
                fpgas,
                args.script_path,
                args.output
            )
            generated_files = [jenkinsfile_path]
            
        elif args.config_dir:
            # Generate Jenkinsfiles for all processors in directory
            generated_files = generate_all_pipelines(
                args.config_dir,
                fpgas,
                args.script_path,
                args.output
            )
            
        else:
            print_red('[ERROR] Either --config or --config-dir must be specified')
            parser.print_help()
            return 1

        # Create summary if requested
        if args.summary and generated_files:
            create_pipeline_summary(generated_files, args.output)

        # Print results
        if generated_files:
            print_green('\n[SUCCESS] Jenkins pipeline generation completed!')
            print_green(f'Generated {len(generated_files)} Jenkinsfile(s):')
            for jenkinsfile in generated_files:
                print(f'  - {jenkinsfile}')
        else:
            print_yellow('[WARN] No Jenkinsfiles were generated')
            
    except Exception as e:
        print_red(f'[ERROR] {e}')
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
