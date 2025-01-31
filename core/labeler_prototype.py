"""A prototype script to find LICENSE files in a directory and identify their types."""
import subprocess
import re
import json
import argparse
import os
from config import load_config

EXTENSIONS = ['v', 'sv', 'vhdl', 'vhd']


def find_license_files(directory: str) -> list[str]:
    """Find all LICENSE files in the given directory.

    Args:
        directory (str): The directory to search for LICENSE files.

    Returns:
        list: A list of LICENSE file paths.
    """
    try:
        result = subprocess.run(
            ['find', directory, '-type', 'f', '-iname', '*LICENSE*'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        if result.stderr:
            print(f'Error: {result.stderr}')
            return []
        return (
            result.stdout.strip().split('\n') if result.stdout.strip() else []
        )
    except subprocess.CalledProcessError as e:
        print(f'Error executing find command: {e}')
        return []
    except FileNotFoundError as e:
        print(f'Find command not found: {e}')
        return []


def identify_license_type(license_content):
    """Identify the type of license based on the content of the LICENSE file.

    Args:
        license_content (str): The content of the LICENSE file.

    Returns:
        str: The type of license.
    """
    license_patterns = {
        # Permissive Licenses
        'MIT': r'(?i)permission is hereby granted, free of charge, to any person obtaining a copy',
        'Apache 2.0': r'(?i)licensed under the Apache License, Version 2\.0',
        'BSD 3-Clause': (
            r'(?i)neither the name of the copyright holder nor the names of its\s+contributors '
            r'may be used to endorse or promote products derived from\s+this '
            r'software without specific prior written permission\.'
        ),
        'Zlib': (
            r'(?i)This software is provided \'as-is\', without any express or implied warranty'
        ),
        'Unlicense': (
            r'(?i)This is free and unencumbered software released into the public domain'
        ),
        # CERN Open Hardware Licenses
        'CERN Open Hardware Licence v2 - Permissive': r'(?i)The CERN-OHL-P is copyright CERN 2020.',
        'CERN Open Hardware Licence v2 - Weakly Reciprocal': (
            r'(?i)The CERN-OHL-W is copyright CERN 2020.'
        ),
        'CERN Open Hardware Licence v2 - Strongly Reciprocal': (
            r'(?i)The CERN-OHL-S is copyright CERN 2020.'
        ),
        # Copyleft Licenses
        'GPLv2': r'(?i)GNU GENERAL PUBLIC LICENSE\s*Version 2',
        'GPLv3': r'(?i)GNU GENERAL PUBLIC LICENSE\s*Version 3',
        'LGPLv2.1': r'(?i)Lesser General Public License\s*Version 2\.1',
        'LGPLv3': r'(?i)Lesser General Public License\s*Version 3',
        'MPL 2.0': r'(?i)Mozilla Public License\s*Version 2\.0',
        'Eclipse Public License': r'(?i)Eclipse Public License - v [0-9]\.[0-9]',
        # Creative Commons Licenses
        'CC0': r'(?i)Creative Commons Zero',
        'Creative Commons Attribution (CC BY)': (
            r'(?i)This work is licensed under a Creative Commons Attribution'
        ),
        'Creative Commons Attribution-ShareAlike (CC BY-SA)': (
            r'(?i)This work is licensed under a Creative Commons Attribution-ShareAlike'
        ),
        'Creative Commons Attribution-NoDerivatives (CC BY-ND)': (
            r'(?i)This work is licensed under a Creative Commons Attribution-NoDerivatives'
        ),
        'Creative Commons Attribution-NonCommercial (CC BY-NC)': (
            r'(?i)This work is licensed under a Creative Commons Attribution-NonCommercial'
        ),
        'Creative Commons Attribution-NonCommercial-ShareAlike (CC BY-NC-SA)': (
            r'(?i)This work is licensed under a Creative Commons '
            r'Attribution-NonCommercial-ShareAlike'
        ),
        'Creative Commons Attribution-NonCommercial-NoDerivatives (CC BY-NC-ND)': (
            r'(?i)This work is licensed under a Creative Commons '
            r'Attribution-NonCommercial-NoDerivatives'
        ),
        # Public Domain
        'Public Domain': r'(?i)dedicated to the public domain',
        # Proprietary Licenses
        'Proprietary': r'(?i)\ball rights reserved\b.*?(license|copyright|terms)',
        # Academic and Other Specialized Licenses
        'Artistic License': r'(?i)This package is licensed under the Artistic License',
        'Academic Free License': r'(?i)Academic Free License',
    }

    for license_name, pattern in license_patterns.items():
        if re.search(pattern, license_content):
            return license_name
    return 'Custom License'


def determine_cpu_bits(top_file):
    """
    Analyzes a hardware description file to determine the CPU data width.

    Args:
        top_file (str): Path to file with top module definition.

    Returns:
        str: The CPU data width (32 or 64) if found, None otherwise.
    """
    try:
        with open(top_file, 'r', encoding='utf-8') as file:
            content = file.read()

        count_32 = 0
        count_64 = 0
        # Count occurrences of [31:0] and [63:0] for Verilog/SystemVerilog
        if top_file.endswith('.v') or top_file.endswith('.sv'):
            count_32 = len(re.findall(r'\[31:0\]', content))
            count_64 = len(re.findall(r'\[63:0\]', content))
        # Count occurrences of (31 downto 0) and (63 downto 0) for VHDL
        elif top_file.endswith('.vhdl') or top_file.endswith('.vhd'):
            count_32 = len(re.findall(r'\(31 downto 0\)', content))
            count_64 = len(re.findall(r'\(63 downto 0\)', content))

        # Return the result based on the counts
        if count_32 == 0 and count_64 == 0:
            return None
        return '32' if count_32 > count_64 else '64'

    except FileNotFoundError as e:
        subprocess.run(
            ['echo', f'File not found: {top_file}: {e}'],
            stderr=subprocess.PIPE,
            check=True,
        )
        return None
    except PermissionError as e:
        subprocess.run(
            ['echo', f'Permission denied: {top_file}: {e}'],
            stderr=subprocess.PIPE,
            check=True,
        )
        return None
    except OSError as e:
        subprocess.run(
            ['echo', f'Error reading file {top_file}: {e}'],
            stderr=subprocess.PIPE,
            check=True,
        )
        return None


def generate_labels_file(processor_name, license_types, cpu_bits, output_file):
    """Generate a JSON file with labels for the processor cores.

    Args:
        directory (str): The directory to search for LICENSE files.
        config_file (str): The configuration JSON file path.
        output_file (str): The output JSON file path.
    """
    # Load existing JSON data if the file exists
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as json_file:
                existing_data = json.load(json_file)
        except (json.JSONDecodeError, OSError) as e:
            print(f'Error reading existing JSON file: {e}')
            existing_data = {}
    else:
        existing_data = {}

    # Check if "cores" exists
    if 'cores' not in existing_data:
        # Overwrite the file completely if "cores" is missing
        output_data = {
            'cores': {
                processor_name: {
                    'license_types': list(
                        set(license_types)
                    ),  # Deduplicate license types
                    'bits': cpu_bits,
                }
            }
        }
    else:
        # Update only the cores section without overwriting other data
        existing_data['cores'][processor_name] = {
            'license_types': list(
                set(license_types)
            ),  # Deduplicate license types
            'bits': cpu_bits,
        }
        output_data = existing_data

    # Write updated results back to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(output_data, json_file, indent=4)
        print(f'Results saved to {output_file}')
    except OSError as e:
        print(f'Error writing to JSON file: {e}')


def main(directory, config_file, output_file):
    """Main function to find LICENSE files and identify their types.

    Args:
        directory (str): The directory to search for LICENSE files.
        config_file (str): The configuration JSON file path.
        output_file (str): The output JSON file path.
    """
    license_files = find_license_files(directory)
    if not license_files:
        print('No LICENSE files found.')
        return

    # Extract the processor name from the directory
    processor_name = os.path.basename(os.path.normpath(directory))
    license_types = []

    for license_file in license_files:
        try:
            with open(license_file, 'r', encoding='utf-8') as file:
                content = file.read()
                license_type = identify_license_type(content)
                license_types.append(license_type)
        except OSError as e:
            print(f'Error reading file {license_file}: {e}')
            license_types.append('Error')

    config = load_config(config_file)

    top_module = config['cores'][processor_name]['top_module']

    for files in config['cores'][processor_name]['files']:
        files = os.path.join(directory, files)
        with open(files, 'r', encoding='latin-1') as f:
            content = f.read()
            if top_module in content:
                top_file = files
                break
            top_file = None

    if top_file is None:
        print('Top module not found in the core files.')
        return

    cpu_bits = determine_cpu_bits(top_file)

    if cpu_bits is None:
        for files in config['cores'][processor_name]['files']:
            files = os.path.join(directory, files)
            cpu_bits = determine_cpu_bits(files)
            if cpu_bits is not None:
                break

    generate_labels_file(processor_name, license_types, cpu_bits, output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Find LICENSE files in a directory and identify their types.'
    )
    parser.add_argument(
        '-d',
        '--dir',
        help='The directory to search for LICENSE files.',
        required=True,
    )
    parser.add_argument(
        '-c',
        '--config',
        default='config.json',
        help='The configuration file path.',
    )
    parser.add_argument(
        '-o',
        '--output',
        default='labels.json',
        help='The output JSON file path.',
    )
    args = parser.parse_args()
    dir_to_search = args.dir
    config_json = args.config
    output_json = args.output
    main(dir_to_search, config_json, output_json)
