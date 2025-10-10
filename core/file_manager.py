"""
This module provides utilities for handling Git repositories,
searching and analyzing files with specific extensions (Verilog, VHDL),
and identifying modules and entities in HDL designs.

Main functions:
- clone_repo: Clones a GitHub repository.
- remove_repo: Removes a cloned repository.
- find_files_with_extension: Finds files with specific extensions.
- is_testbench_file: Checks if a file appears to be a testbench.
- find_include_dirs: Locates directories containing include files.
- extract_modules: Extracts modules and entities from HDL files.
"""

import subprocess
import os
import glob
import re
import shutil

# Constant for the destination directory
DESTINATION_DIR = "./temp"


def clone_repo(url: str, repo_name: str) -> str:
    """Clones a GitHub repository to a specified directory.

    Args:
        url (str): URL of the GitHub repository.
        repo_name (str): Name of the repository (used as the directory name).

    Returns:
        str: Path to the cloned repository.

    Raises:
        subprocess.CalledProcessError: If the cloning process fails.
    """
    destination_path = os.path.join(DESTINATION_DIR, repo_name)

    try:
        subprocess.run(
            ["git", "clone", "--recursive", url, destination_path], check=True
        )
        return destination_path
    except subprocess.CalledProcessError as e:
        print(f"Error cloning the repository: {e}")
        return None


def remove_repo(repo_name: str) -> None:
    """Removes a cloned repository.

    Args:
        repo_name (str): Name of the repository to be removed.

    Returns:
        None
    """
    destination_path = os.path.join(DESTINATION_DIR, repo_name)
    shutil.rmtree(destination_path)


def find_files_with_extension(
    directory: str, extensions: list[str]
) -> tuple[list[str], str]:
    """Finds files with specific extensions in a directory.

    Args:
        directory (str): Path to the directory to search.
        extensions (list[str]): List of file extensions to search for.

    Returns:
        tuple[list[str], str]: List of found files and the predominant file extension.

    Raises:
        IndexError: If no files with the specified extensions are found.
    """
    extension = ".v"
    files = []
    for extension in extensions:
        files.extend(glob.glob(f"{directory}/**/*.{extension}", recursive=True))

    if ".sv" in files[0]:
        extension = ".sv"
    elif ".vhdl" in files[0]:
        extension = ".vhdl"
    elif ".vhd" in files[0]:
        extension = ".vhd"
    elif ".v" in files[0]:
        extension = ".v"

    return files, extension


def is_testbench_file(file_path: str, repo_name: str) -> bool:
    """Checks if a file is likely to be a testbench based on its name or location.

    Args:
        file_path (str): Path to the file.
        repo_name (str): Name of the repository containing the file.

    Returns:
        bool: True if the file is a testbench, otherwise False.
    """
    relative_path = os.path.relpath(file_path, os.path.join(DESTINATION_DIR, repo_name))

    file_name = os.path.basename(relative_path)
    directory_parts = os.path.dirname(relative_path).split(os.sep)

    # Checking if the file name contains keywords
    if re.search(r"(tb|testbench|test|verif)", file_name, re.IGNORECASE):
        return True

    # Checking if any part of the path contains keywords
    for part in directory_parts:
        if re.search(
            r"(tests?|testbenches?|testbenchs?|simulations?|tb|sim|verif)",
            part,
            re.IGNORECASE,
        ):
            return True

    return False


def find_include_dirs(directory: str) -> set[str]:
    """Finds directories containing include files (.svh or .vh).

    Args:
        directory (str): Path to the directory to search.

    Returns:
        set[str]: Set of directories containing include files.
    """
    include_files = glob.glob(f"{directory}/**/*.(svh|vh)", recursive=True)
    include_dirs = {os.path.dirname(file) for file in include_files}
    return include_dirs


def extract_modules(files: list[str]) -> list[tuple[str, str]]:
    """Extracts modules and entities from HDL files.

    Args:
        files (list[str]): List of HDL file paths.

    Returns:
        list[tuple[str, str]]: List of tuples with module/entity names and their file paths.
    """
    modules = []

    module_pattern_verilog = re.compile(r"module\s+(\w+)\s*")
    entity_pattern_vhdl = re.compile(r"entity\s+(\w+)\s+is", re.IGNORECASE)

    for file_path in files:
        with open(file_path, "r", errors="ignore", encoding="utf-8") as f:
            content = f.read()

            # Find Verilog/SystemVerilog modules
            verilog_matches = module_pattern_verilog.findall(content)
            modules.extend(
                [
                    (module_name, os.path.relpath(file_path))
                    for module_name in verilog_matches
                ]
            )

            # Find VHDL entities
            vhdl_matches = entity_pattern_vhdl.findall(content)
            modules.extend(
                [
                    (entity_name, os.path.relpath(file_path))
                    for entity_name in vhdl_matches
                ]
            )

    return modules
