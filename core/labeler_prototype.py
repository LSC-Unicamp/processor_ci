"""A prototype script to find LICENSE files in a directory and identify their types."""
import subprocess
import re
import json
import argparse
import os
import logging
from config import load_config

EXTENSIONS = ['v', 'sv', 'vhdl', 'vhd']


def find_license_files(directory: str) -> list[str]:
    """Find all LICENSE files in the given directory.

    Args:
        directory (str): The directory to search for LICENSE files.

    Returns:
        list: A list of LICENSE file paths.
    """
    logging.basicConfig(
        level=logging.WARNING, format='%(levelname)s: %(message)s'
    )

    try:
        result = subprocess.run(
            ['find', directory, '-type', 'f', '-iname', '*LICENSE*'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        if result.stderr:
            logging.warning('Error: %s', result.stderr)
            return []
        return (
            result.stdout.strip().split('\n') if result.stdout.strip() else []
        )
    except subprocess.CalledProcessError as e:
        logging.warning('Error executing find command: %s', e)
        return []
    except FileNotFoundError as e:
        logging.warning('Find command not found: %s', e)
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
        'BSD 2-Clause': (
            r'(?i)Redistribution and use in source and binary forms, with or without modification, '
            r'are permitted provided that the following conditions are met:\s*'
            r'1\.\s*Redistributions of source code must retain the above copyright notice, '
            r'this list of conditions and the following disclaimer\.\s*'
            r'2\.\s*Redistributions in binary form must reproduce the above copyright notice, '
            r'this list of conditions and the following disclaimer in the documentation '
            r'and/or other materials provided with the distribution\.\s*'
            r'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"'
        ),
        'BSD 3-Clause': (
            r'(?i)neither the name of the copyright holder nor the names of its\s+contributors '
            r'may be used to endorse or promote products derived from\s+this '
            r'software without specific prior written permission\.'
        ),
        'ISC': (
            r'(?i)Permission to use, copy, modify, and distribute this software for any '
            r'purpose(?:\n|\s)*with or without fee is hereby granted, provided that the above '
            r'copyright notice(?:\n|\s)*and this permission notice appear in all copies\.(?:\n|\s)*'
            r'THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES(?:\n|\s)*'
            r'INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS '
            r'FOR A PARTICULAR PURPOSE\.'
        ),
        # Other licenses...
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

    logging.basicConfig(
        level=logging.WARNING, format='%(levelname)s: %(message)s'
    )

    print(f'Trying to read file: {top_file}')

    encodings = ['utf-8', 'latin-1', 'utf-16', 'utf-8-sig']

    for encoding in encodings:
        try:
            with open(top_file, 'r', encoding=encoding) as file:
                content = file.read()
            break
        except (
            UnicodeDecodeError,
            FileNotFoundError,
            PermissionError,
            OSError,
        ) as e:
            logging.warning(
                'Error reading file %s with encoding %s: %s',
                top_file,
                encoding,
                e,
            )
            content = None

    if content is None:
        return None

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


def has_cpu_cache(repository):
    """
    Analyzes a Verilog-based CPU directory to determine if it includes cache.

    Args:
        repository(str): Path to the directory containing the CPU Verilog files

    Returns:
        Boolean: True if the CPU has a cache, False otherwise
    """

    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s',
    )

    # Check if the directory exists
    if not os.path.isdir(repository):
        logging.warning(
            "[!] Error: Directory '%s' does not exist.", repository
        )
        return False

    # Verilog cache-related file names
    cache_files = {
        'icache',
        'dcache',
        'cache',
        'l1_cache',
        'l2_cache',
        'cache_controller',
    }

    # Verilog cache-related keywords
    cache_keywords = [
        r'\b(cache_hit|cache_miss|tag|dirty|valid)\b',
        r'\b(LRU|FIFO|replacement_policy)\b',
        r'\b(write_back|write_through)\b',
    ]

    has_cache = False

    # Walk through all Verilog and SystemVerilog files in the directory
    for root, _, files in os.walk(repository):
        for file in files:
            if file.endswith(
                ('.v', '.sv')
            ):  # Checks Verilog and SystemVerilog files
                file_path = os.path.join(root, file)

                # Check for cache-related filenames
                if any(name in file.lower() for name in cache_files):
                    print(f'Possible cache file: {file}')
                    has_cache = True

                # Scan for cache-related Verilog and SystemVerilog signals
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for keyword in cache_keywords:
                        if re.search(keyword, content):
                            print(f'Cache-related signals in {file}')
                            has_cache = True
                            break  # Stop scanning this file if we already found cache indicators

    return has_cache


def generate_labels_file(
    processor_name, license_types, cpu_bits, cache, output_dir
):
    """Generate a JSON file with labels for the processor.

    Args:
        processor_name (str): The name of the processor.
        license_types (list{str}): List of license types.
        cpu_bits (int): CPU bit architecture.
        cache (bool): True if the CPU has cache, False otherwise.
        output_dir (str): The folder where the JSON file will be saved.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s',
    )

    # Ensure the output folder exists
    os.makedirs(output_dir, exist_ok=True)

    # Define the output file path using the processor name
    output_file = os.path.join(output_dir, f'{processor_name}.json')

    # Ensure the JSON file exists
    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump({}, json_file, indent=4)

    # Load existing JSON data
    try:
        with open(output_file, 'r', encoding='utf-8') as json_file:
            existing_data = json.load(json_file)
    except (json.JSONDecodeError, OSError) as e:
        logging.warning('Error reading existing JSON file: %s', e)
        existing_data = {}

    # Update the JSON data directly without "cores" section
    existing_data[processor_name] = {
        'license_types': list(set(license_types)),  # Deduplicate license types
        'bits': cpu_bits,
        'cache': cache,
    }

    # Write updated results back to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, indent=4)
        print(f'Results saved to {output_file}')
    except OSError as e:
        logging.warning('Error writing to JSON file: %s', e)


def main(directory, config_file, output_dir):
    """Main function to find LICENSE files and identify their types.

    Args:
        directory (str): The directory to search for LICENSE files.
        config_file (str): The configuration JSON file path.
        output_folder (str): The output folder path.
    """
    logging.basicConfig(
        level=logging.WARNING, format='%(levelname)s: %(message)s'
    )

    license_files = find_license_files(directory)
    if not license_files:
        logging.warning('No LICENSE files found.')
        return

    processor_name = os.path.basename(os.path.normpath(directory))
    license_types = []

    for license_file in license_files:
        try:
            with open(license_file, 'r', encoding='utf-8') as file:
                content = file.read()
                license_type = identify_license_type(content)
                license_types.append(license_type)
        except OSError as e:
            logging.warning('Error reading file %s: %s', license_file, e)
            license_types.append('Error')
    config = load_config(config_file)

    top_module = config['cores'][processor_name]['top_module']

    try:
        for files in config['cores'][processor_name]['files']:
            files = os.path.join(directory, files)
            with open(files, 'r', encoding='latin-1') as f:
                content = f.read()
                if top_module in content:
                    top_file = files
                    break
                top_file = None

        if top_file is None:
            logging.warning('Top module not found in the core files.')
            return

        cpu_bits = determine_cpu_bits(top_file)

        if cpu_bits is None:
            for files in config['cores'][processor_name]['files']:
                files = os.path.join(directory, files)
                cpu_bits = determine_cpu_bits(files)
                if cpu_bits is not None:
                    break

    except KeyError as e:
        logging.warning('Error processing configuration: %s', e)
        return

    cache = has_cpu_cache(directory)

    generate_labels_file(
        processor_name, license_types, cpu_bits, cache, output_dir
    )


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
        default='labels',
        help='The output folder path.',
    )
    args = parser.parse_args()
    dir_to_search = args.dir
    config_json = args.config
    output_folder = args.output
    main(dir_to_search, config_json, output_folder)
