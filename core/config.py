"""
This module provides utilities for handling configuration files
in JSON format, including operations to load, save, and fetch specific data,
such as processor information.

Main functions:
- load_config: Loads a JSON configuration file.
- save_config: Saves a dictionary to a JSON configuration file.
- get_processor_data: Retrieves processor information from the configuration file.
"""

import os
import json


def create_default_config(config_path: str, processor_name: str) -> None:
    """Creates a default configuration file with an empty dictionary.

    Args:
        config_path (str): Path to the JSON configuration file.

    Returns:
        None

    Raises:
        IOError: If there is an issue writing to the file.
    """
    full_config_path = os.path.join(config_path, f'{processor_name}.json')

    with open(full_config_path, 'w', encoding='utf-8') as file:
        json.dump({}, file, indent=4)


def load_config(config_path: str, processor_name: str) -> dict:
    """Loads a JSON configuration file and returns its content.

    Args:
        config_path (str): Path to the JSON configuration file.

    Returns:
        dict: Content of the JSON file as a dictionary.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
        json.JSONDecodeError: If the file is not a valid JSON.
    """
    if not os.path.exists(config_path):
        os.makedirs(config_path, exist_ok=True)
        raise FileNotFoundError(
            f'The configuration folder {config_path} was not found.'
        )
        # create_default_config(config_path)

    full_config_path = os.path.join(config_path, f'{processor_name}.json')

    if not os.path.exists(full_config_path):
        create_default_config(config_path, processor_name)
        raise FileNotFoundError(
            f'The configuration file {full_config_path} was not found.'
        )

    with open(full_config_path, 'r', encoding='utf-8') as file:
        config_data = json.load(file)

    return config_data


def save_config(
    config_path: str, config_data: dict, processor_name: str
) -> None:
    """Saves a dictionary to a specified JSON configuration file.

    Args:
        config_path (str): Path to the JSON configuration file.
        config_data (dict): Configuration data to be saved.

    Returns:
        None

    Raises:
        TypeError: If the data provided is not serializable to JSON.
        IOError: If there is an issue writing to the file.
    """
    if not os.path.exists(config_path):
        os.makedirs(config_path, exist_ok=True)

    full_config_path = os.path.join(config_path, f'{processor_name}.json')
    # Save the configuration data to the specified file

    with open(full_config_path, 'w', encoding='utf-8') as file:
        json.dump(config_data, file, indent=4)
