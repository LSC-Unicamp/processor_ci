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


def create_default_config(config_path: str) -> None:
    """Creates a default configuration file with an empty dictionary.

    Args:
        config_path (str): Path to the JSON configuration file.

    Returns:
        None

    Raises:
        IOError: If there is an issue writing to the file.
    """
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump({'cores': {}}, file, indent=4)


def load_config(config_path: str) -> dict:
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
        # raise FileNotFoundError(
        #    f'The configuration file {config_path} was not found.'
        # )
        create_default_config(config_path)

    with open(config_path, 'r', encoding='utf-8') as file:
        config_data = json.load(file)

    return config_data


def save_config(config_path: str, config_data: dict) -> None:
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
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config_data, file, indent=4)


def get_processor_data(config: dict, processor_name: str) -> dict:
    """Fetches processor data by name from the configuration dictionary.

    Args:
        config (dict): Loaded configuration dictionary.
        processor_name (str): Name of the processor to retrieve.

    Returns:
        dict: Dictionary containing processor data.

    Raises:
        KeyError: If the 'cores' key is missing in the configuration.
        ValueError: If the processor is not found in the configuration.
    """
    cores = config.get('cores', {})

    processor_data = cores.get(processor_name)
    if not processor_data:
        raise ValueError(
            f"Processor '{processor_name}' not found in the configuration."
        )

    return processor_data
