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
DESTINATION_DIR = './temp'

# Problematic directories and patterns that should be excluded
EXCLUDE_DIRECTORIES = [
    'dv', 'google_riscv-dv', 'lowrisc_ip/dv',
    'formal', 'fpv', 'verification', 'testbench', 'tb',
    'test', 'tests', 'sim', 'simulation', 'verification',
    'uvm', 'compliance', 'property', 'assert', 'bind',
    'coverage', 'checker', 'monitor', 'sequence',
    'boards', 'board', 'fpga'  # FPGA board-specific files
]

EXCLUDE_PATTERNS = [
    r'\buvm_',  # UVM prefixed files
    r'\bdv_',   # DV prefixed files  
    r'_dv\b',   # Files ending with _dv
    r'riscv-dv', # Google RISC-V DV
    r'compliance', # RISC-V compliance tests
    r'formal',  # Formal verification
    r'fpv',     # Formal Property Verification
    r'assert',  # Assertion files
    r'bind',    # Bind files
    r'property', # Property files
    r'sequence', # Sequence files
    r'checker',  # Checker files
    r'monitor',  # Monitor files
    r'coverage', # Coverage files
    r'_tb\b',   # Testbench files
    r'\btb_',   # TB prefixed files
    r'_test\b', # Files ending with _test
    r'\btest_', # Test prefixed files
    r'_verif\b',# Verification files
    r'\bverif_',# Verification prefixed files
    r'_pkg\b.*test', # Package files for testing
    r'_lib\b.*test', # Library files for testing
    r'vendor/google', # All Google vendor files  
    r'prim_generic.*flash', # Problematic flash primitives
    r'prim.*lc_', # Lifecycle control primitives
    r'prim_edn_req', # EDN request primitive
]


def analyze_file_dependencies(file_path: str) -> set:
    """Analyze a SystemVerilog file to extract its dependencies (includes, imports, instances).
    
    Args:
        file_path (str): Path to the SystemVerilog file
        
    Returns:
        set: Set of dependency names (packages, modules, includes)
    """
    dependencies = set()
    
    if not os.path.exists(file_path):
        return dependencies
        
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Find include statements
        include_pattern = r'`include\s+"([^"]+)"'
        for match in re.finditer(include_pattern, content):
            dependencies.add(match.group(1))
            
        # Find package imports
        import_pattern = r'import\s+(\w+)::'
        for match in re.finditer(import_pattern, content):
            dependencies.add(match.group(1))
            
        # Find module instantiations
        instance_pattern = r'^\s*(\w+)\s+(?:\#\([^)]*\)\s*)?(\w+)\s*\('
        for match in re.finditer(instance_pattern, content, re.MULTILINE):
            module_name = match.group(1)
            # Skip built-in SystemVerilog keywords and primitives
            if module_name not in ['logic', 'reg', 'wire', 'input', 'output', 'inout', 
                                  'parameter', 'localparam', 'genvar', 'generate', 'if', 
                                  'for', 'case', 'always', 'initial', 'assign']:
                dependencies.add(module_name)
                
    except Exception as e:
        # If we can't read the file, assume no dependencies
        pass
        
    return dependencies


def find_essential_files_by_dependency(directory: str, top_modules: list) -> set:
    """Find essential files by analyzing dependency chains from top modules.
    
    Args:
        directory (str): Root directory to search
        top_modules (list): List of top module names to start dependency analysis from
        
    Returns:
        set: Set of file paths that are essential based on dependency analysis
    """
    essential_files = set()
    
    # First, find all SystemVerilog files and map module names to file paths
    module_to_file = {}
    all_sv_files = find_files_with_extension(directory, ['.sv', '.svh'], exclude_filtered=False)
    
    for file_path in all_sv_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Find module/package definitions
            module_pattern = r'^\s*(module|package|interface)\s+(\w+)'
            for match in re.finditer(module_pattern, content, re.MULTILINE):
                module_name = match.group(2)
                module_to_file[module_name] = file_path
                
        except Exception:
            continue
    
    # Perform dependency analysis starting from top modules
    visited = set()
    
    def analyze_dependencies_recursive(module_name: str):
        if module_name in visited:
            return
        visited.add(module_name)
        
        # Find the file for this module
        if module_name not in module_to_file:
            return
            
        file_path = module_to_file[module_name]
        
        # Skip files that are obviously verification-related
        if should_exclude_file(file_path, directory):
            return
            
        essential_files.add(file_path)
        
        # Analyze dependencies of this file
        deps = analyze_file_dependencies(file_path)
        for dep in deps:
            # For includes, try to find the actual file
            if dep.endswith('.svh') or dep.endswith('.sv'):
                # Try to find this include file
                include_candidates = []
                for sv_file in all_sv_files:
                    if sv_file.endswith(dep):
                        include_candidates.append(sv_file)
                
                # Add include files that aren't verification-related
                for candidate in include_candidates:
                    if not should_exclude_file(candidate, directory):
                        essential_files.add(candidate)
            else:
                # This is a module/package dependency
                analyze_dependencies_recursive(dep)
    
    # Start analysis from each top module
    for top_module in top_modules:
        analyze_dependencies_recursive(top_module)
    
    return essential_files


def should_exclude_file(file_path: str, base_directory: str = None) -> bool:
    """Check if a file should be excluded based on its path and name.
    
    Args:
        file_path (str): Path to the file to check
        base_directory (str): Base directory to calculate relative path from
        
    Returns:
        bool: True if the file should be excluded, False otherwise
    """
    if base_directory:
        rel_path = os.path.relpath(file_path, base_directory)
    else:
        rel_path = file_path
        
    file_name = os.path.basename(file_path)
    
    # First, check for obvious verification/testbench patterns
    verification_patterns = [
        r'\buvm_', r'\bdv_', r'_dv\b', r'riscv-dv', r'compliance',
        r'formal', r'fpv', r'bind', r'property', r'sequence',
        r'checker', r'monitor', r'coverage', r'_tb\b', r'\btb_',
        r'_test\b', r'\btest_', r'_verif\b', r'\bverif_',
        r'_pkg\b.*test', r'_lib\b.*test'
    ]
    
    for pattern in verification_patterns:
        if re.search(pattern, file_name, re.IGNORECASE):
            return True
    
    # Check for verification directories and FPGA board directories
    verification_dirs = [
        'dv', 'google_riscv-dv', 'formal', 'fpv', 'verification',
        'testbench', 'tb', 'test', 'tests', 'sim', 'simulation',
        'uvm', 'compliance', 'property', 'assert', 'bind',
        'coverage', 'checker', 'monitor', 'sequence',
        'boards', 'board', 'fpga'  # FPGA board-specific directories
    ]
    
    for exclude_dir in verification_dirs:
        if exclude_dir in rel_path:
            return True
    
    # For vendor directories, be more selective - exclude obvious problematic files
    if 'vendor' in rel_path:
        # Exclude Google RISC-V DV completely
        if 'google_riscv-dv' in rel_path:
            return True
            
        # For lowrisc_ip, only exclude DV subdirectories
        if 'lowrisc_ip/dv' in rel_path:
            return True
            
        # Exclude problematic vendor files that commonly cause syntax errors
        problematic_vendor_patterns = [
            r'prim_generic.*flash',  # Flash primitives often have syntax issues
            r'prim.*usb_diff_rx',    # USB primitives
            r'prim.*latch',          # Latch files with special syntax
            r'crypto_dpi',           # Crypto DPI files
            r'mem_bkdr_util',        # Memory backdoor utilities
        ]
        
        for pattern in problematic_vendor_patterns:
            if re.search(pattern, file_name, re.IGNORECASE):
                return True
    
    # Don't exclude based on vendor paths alone - let dependency analysis decide
    return False


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
            ['git', 'clone', '--recursive', url, destination_path], check=True
        )
        return destination_path
    except subprocess.CalledProcessError as e:
        print(f'Error cloning the repository: {e}')
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
    extension = '.v'
    files = []
    
    for ext in extensions:
        found_files = glob.glob(f'{directory}/**/*.{ext}', recursive=True)
        
        for file_path in found_files:            
            if not should_exclude_file(file_path, directory):
                files.append(file_path)

    if not files:
        return [], '.v'

    if '.sv' in files[0]:
        extension = '.sv'
    elif '.vhdl' in files[0]:
        extension = '.vhdl'
    elif '.vhd' in files[0]:
        extension = '.vhd'
    elif '.v' in files[0]:
        extension = '.v'

    return files, extension


def find_files_with_extension_smart(
    directory: str, extensions: list[str], top_modules: list[str] = None
) -> tuple[list[str], str]:
    """Find files using intelligent dependency-based filtering.
    
    Args:
        directory (str): Directory to search in
        extensions (list[str]): List of file extensions to look for
        top_modules (list[str]): Optional list of top modules for dependency analysis
        
    Returns:
        tuple[list[str], str]: List of essential files and predominant extension
    """
    if top_modules:
        # Use dependency-based analysis
        essential_files = find_essential_files_by_dependency(directory, top_modules)
        
        # Filter by extensions
        filtered_files = []
        for file_path in essential_files:
            for ext in extensions:
                if file_path.endswith(f'.{ext}'):
                    filtered_files.append(file_path)
                    break
        
        # Determine predominant extension
        extension = '.v'
        if filtered_files:
            if any('.sv' in f for f in filtered_files):
                extension = '.sv'
            elif any('.vhdl' in f for f in filtered_files):
                extension = '.vhdl'
            elif any('.vhd' in f for f in filtered_files):
                extension = '.vhd'
                
        return filtered_files, extension
    else:
        # Fall back to pattern-based filtering
        return find_files_with_extension(directory, extensions)


def is_testbench_file(file_path: str, repo_name: str) -> bool:
    """Checks if a file is likely to be a testbench based on its name or location.

    Args:
        file_path (str): Path to the file.
        repo_name (str): Name of the repository containing the file.

    Returns:
        bool: True if the file is a testbench, otherwise False.
    """
    base_directory = os.path.join(DESTINATION_DIR, repo_name)
    
    # Use the shared exclusion logic
    if should_exclude_file(file_path, base_directory):
        return True
    
    # Additional testbench-specific checks
    relative_path = os.path.relpath(file_path, base_directory)
    file_name = os.path.basename(relative_path)
    directory_parts = os.path.dirname(relative_path).split(os.sep)

    # Checking if the file name contains testbench keywords (use word boundaries to avoid false positives)
    if re.search(r'\b(tb|testbench|test|verif)\b', file_name, re.IGNORECASE):
        return True

    # Checking if any part of the path contains testbench keywords (use word boundaries)
    for part in directory_parts:
        if re.search(
            r'\b(tests?|testbenches?|testbenchs?|simulations?|tb|sim|verif)\b',
            part,
            re.IGNORECASE,
        ):
            return True

    return False


def find_include_dirs(directory: str) -> set[str]:
    """Finds directories containing include files (.svh, .vh, or .v definition files).

    Args:
        directory (str): Path to the directory to search.

    Returns:
        set[str]: Set of directories containing include files.
    """
    # Find .svh and .vh files
    include_files = []
    include_files.extend(glob.glob(f'{directory}/**/*.svh', recursive=True))
    include_files.extend(glob.glob(f'{directory}/**/*.vh', recursive=True))
    
    # Also find .v files that appear to be include/definition files
    # Look for files with common include patterns in their names
    v_files = glob.glob(f'{directory}/**/*.v', recursive=True)
    for v_file in v_files:
        filename = os.path.basename(v_file).lower()
        if any(pattern in filename for pattern in ['define', 'param', 'config', 'include', 'const']):
            include_files.append(v_file)
    
    include_dirs = set()
    for file in include_files:
        dir_path = os.path.dirname(file)
        # Convert to relative path from the directory
        relative_dir_path = os.path.relpath(dir_path, directory)
        include_dirs.add(relative_dir_path)
    return include_dirs


def find_missing_modules(directory: str, missing_module_names: list) -> set[str]:
    """Find directories containing specific missing modules.
    
    Args:
        directory (str): Base directory path to search
        missing_module_names (list): List of module names to search for
        
    Returns:
        set[str]: Set of directory paths that contain the missing modules
    """
    found_dirs = set()
    
    if not missing_module_names:
        return found_dirs
    
    try:
        # Search for .v/.sv files that might contain the missing modules
        for extension in ['**/*.v', '**/*.sv']:
            source_files = glob.glob(os.path.join(directory, extension), recursive=True)
            
            for file_path in source_files:
                try:
                    # Quick filename check first (most modules are named after their files)
                    file_basename = os.path.basename(file_path)
                    
                    for module_name in missing_module_names:
                        if module_name in file_basename:
                            dir_path = os.path.dirname(file_path)
                            # Convert to relative path from the directory
                            relative_dir_path = os.path.relpath(dir_path, directory)
                            found_dirs.add(relative_dir_path)
                            print(f"[DEBUG] Found potential module {module_name} in {file_path}")
                    
                except Exception as e:
                    print(f"[WARNING] Error checking file {file_path}: {e}")
                    
    except Exception as e:
        print(f"[WARNING] Error finding missing modules: {e}")
    
    return found_dirs


def find_missing_module_files(directory: str, missing_module_names: list) -> list[str]:
    """Find specific files containing missing modules.
    
    Args:
        directory (str): Base directory path to search
        missing_module_names (list): List of module names to search for
        
    Returns:
        list[str]: List of relative file paths that contain the missing modules
    """
    found_files = []
    
    if not missing_module_names:
        return found_files
    
    try:
        # Search for .v/.sv files that might contain the missing modules
        for extension in ['**/*.v', '**/*.sv']:
            source_files = glob.glob(os.path.join(directory, extension), recursive=True)
            
            for file_path in source_files:
                try:
                    # Quick filename check first (most modules are named after their files)
                    file_basename = os.path.basename(file_path)
                    matched = False
                    for module_name in missing_module_names:
                        if module_name in file_basename:
                            matched = True
                            # Convert to relative path from the directory
                            relative_path = os.path.relpath(file_path, directory)
                            found_files.append(relative_path)
                            print(f"[DEBUG] Found potential module {module_name} in {relative_path}")
                    # If basename doesn't hint, do a light content scan for 'module <name>'
                    if not matched and file_path.endswith(('.v', '.sv')):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
                                head = fh.read(200000)
                            for module_name in missing_module_names:
                                # Verilog module decl pattern
                                if re.search(rf"\bmodule\s+{re.escape(module_name)}\b", head):
                                    relative_path = os.path.relpath(file_path, directory)
                                    found_files.append(relative_path)
                                    print(f"[DEBUG] Found module by content {module_name} in {relative_path}")
                        except Exception as _:
                            pass
                    
                except Exception as e:
                    print(f"[WARNING] Error checking file {file_path}: {e}")
                    
    except Exception as e:
        print(f"[WARNING] Error finding missing modules: {e}")
    
    return found_files


def extract_modules(files: list[str]) -> list[tuple[str, str]]:
    """Extracts modules and entities from HDL files.

    Args:
        files (list[str]): List of HDL file paths.

    Returns:
        list[tuple[str, str]]: List of tuples with module/entity names and their file paths.
    """
    modules = []

    module_pattern_verilog = re.compile(r'module\s+(\w+)\s*')
    entity_pattern_vhdl = re.compile(r'entity\s+(\w+)\s+is', re.IGNORECASE)

    for file_path in files:
        with open(file_path, 'r', errors='ignore', encoding='utf-8') as f:
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
