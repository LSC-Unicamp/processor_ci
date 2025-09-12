"""
This script automates the generation of processor configurations and Jenkinsfiles for FPGA projects.

It includes the following functionality:
- Cloning processor repositories and analyzing their files.
- Extracting hardware modules and testbench files from the repository.
- Building module dependency graphs.
- Generating configuration files for the processor.
- Generating Jenkinsfiles for CI/CD pipelines targeting multiple FPGAs.
- Optionally adding generated configurations to a central configuration file or plotting module
    graphs.

Modules and Functions:
----------------------
- **get_top_module_file**: Retrieves the file path of a specific top module.
- **copy_hardware_template**: Copies a hardware template file, naming it after the repository.
- **generate_processor_config**: Clones a repository, analyzes it, and generates a configuration
    for the processor.
- **generate_all_pipelines**: Generates Jenkinsfiles for all processors defined in the configuration
    file.
- **main**: Parses command-line arguments and triggers the appropriate operations.

Command-Line Interface:
-----------------------
- `-j`, `--generate-all-jenkinsfiles`: Generates Jenkinsfiles for processors.
- `-c`, `--generate-config`: Generates a configuration for a specified processor.
- `-g`, `--plot-graph`: Plots the module dependency graph for the generated configuration.
- `-a`, `--add-config`: Adds the generated configuration to the central config file.
- `-p`, `--path-config`: Specifies the path to the config file (default: `config.json`).
- `-u`, `--processor-url`: Specifies the URL of the processor repository to clone.

Constants:
----------
- **EXTENSIONS**: Supported file extensions (`['v', 'sv', 'vhdl', 'vhd']`).
- **BASE_DIR**: Base directory for storing Jenkinsfiles.
- **FPGAs**: List of supported FPGAs for Jenkinsfile generation.
- **DESTINATION_DIR**: Temporary directory for processing repositories.
- **MAIN_SCRIPT_PATH**: Path to the main synthesis script used in Jenkinsfiles.

Usage:
------
1. To generate a processor configuration:
```python
python script.py -c -u <processor_url>
```

2. To generate all Jenkinsfiles:
```python
python script.py -j
```

3. For help:
```python
python script.py --help
```

Dependencies:
-------------
- `os`, `time`, `json`, `shutil`, `argparse`: Standard Python libraries.
- **Custom Modules**:
- `core.config`: Handles loading and saving configuration files.
- `core.file_manager`: Provides utilities for cloning repositories, finding files, and
    extracting modules.
- `core.graph`: Builds and visualizes module dependency graphs.
- `core.jenkins`: Generates Jenkinsfiles.
- `core.ollama`: Filters files and identifies top modules.
"""

import os
import time
import json
import shutil
import argparse
import shlex
import subprocess
import re
import tempfile
from core.config import load_config, save_config
from core.file_manager import (
    clone_repo,
    remove_repo,
    find_files_with_extension,
    extract_modules,
    is_testbench_file,
    find_include_dirs,
)
from core.graph import build_module_graph, plot_processor_graph
from core.ollama import (
    get_filtered_files_list,
    get_top_module,
    generate_top_file,
)
from core.jenkins import generate_jenkinsfile
from core.log import print_green, print_red, print_yellow


EXTENSIONS = ['v', 'sv', 'vhdl', 'vhd']
BASE_DIR = 'jenkins_pipeline/'
FPGAs = [
    #'colorlight_i9',
    #'digilent_nexys4_ddr',
    # "gowin_tangnano_20k",
    # "xilinx_vc709",
    'digilent_arty_a7_100t',
]
DESTINATION_DIR = './temp'
MAIN_SCRIPT_PATH = '/eda/processor_ci/main.py'

def run_simulation_with_config(
    repo_root: str,
    repo_name: str,
    url: str,
    tb_files: list,
    files: list,
    include_dirs: set,
    top_module: str,
    language_version: str,
    timeout: int = 300,
    verilator_extra_flags: list | None = None,
    ghdl_extra_flags: list | None = None,
) -> tuple:
    """
    Write a temporary JSON config (via create_output_json) and invoke the right simulator directly:
      - Verilator for Verilog/SystemVerilog (language_version 'verilog' or 'systemverilog')
      - GHDL for VHDL (language_version 'vhdl' or 'vhd')
    Returns (returncode, stdout_and_stderr_str, config_path_used).

    Parameters:
      - verilator_extra_flags: list of extra flags to pass to verilator (e.g. ['-Wno-UNSIGNED'])
      - ghdl_extra_flags: list of extra flags to pass to ghdl (e.g. ['--std=08'])
    """
    # write config JSON for debugging / reproducibility
    config = create_output_json(repo_name, url, tb_files, files, include_dirs, top_module, language_version)
    tmpdir = tempfile.mkdtemp(prefix="simcfg_")
    try:
        config_path = os.path.join(tmpdir, f"{repo_name}_sim_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Normalize & sort include dirs
        include_dirs_sorted = sorted(include_dirs)

        # --- Build robust Verilator include flags ---
        # +incdir+dir (preferred by many Verilog tools). Quote if path contains spaces.
        incdir_flags_list = []
        for d in include_dirs_sorted:
            if " " in d:
                # +incdir+"dir with space"
                incdir_flags_list.append(f'+incdir+"{d}"')
            else:
                incdir_flags_list.append(f"+incdir+{d}")
        incdir_flags = " ".join(incdir_flags_list)

        # Also add -I form as fallback (properly shell-quoted)
        i_flags = " ".join(f"-I{shlex.quote(d)}" for d in include_dirs_sorted) if include_dirs_sorted else ""

        # Combined Verilator include flags, placed *before* file list when invoking verilator
        include_flags_verilator = " ".join(filter(None, [incdir_flags, i_flags]))

        # GHDL include flags: -Pdir (shell-quoted)
        include_flags_ghdl = " ".join(f"-P{shlex.quote(d)}" for d in include_dirs_sorted) if include_dirs_sorted else ""

        verilator_extra_flags = verilator_extra_flags or []
        ghdl_extra_flags = ghdl_extra_flags or []

        # build quoted file list (relative paths expected)
        file_list = " ".join(shlex.quote(f) for f in files)

        if language_version and language_version.lower() in ("vhd", "vhdl"):
            # GHDL flow
            ghdl_flags = " ".join(shlex.quote(f) for f in ghdl_extra_flags)
            # include flags put before file list
            cmd = f"ghdl -a {include_flags_ghdl} {ghdl_flags} {file_list} && ghdl -e {shlex.quote(top_module)} && ghdl -r {shlex.quote(top_module)}"
            print_green(f"[SIM] Running GHDL: {cmd}")
            return _run_shell_cmd(cmd, repo_root, timeout, config_path)
        else:
            # Verilator flow (verilog/systemverilog)
            obj_dir = os.path.join(tmpdir, "obj_dir")
            os.makedirs(obj_dir, exist_ok=True)
            extra_flags = " ".join(shlex.quote(f) for f in verilator_extra_flags)
            top_opt = f"--top-module {shlex.quote(top_module)}" if top_module else ""

            # Place include flags BEFORE the file list to ensure Verilator picks them up.
            # We include both +incdir+ and -I forms for compatibility.
            verilator_cmd = f"verilator --cc --exe --build {top_opt} -Mdir {shlex.quote(obj_dir)} {include_flags_verilator} {extra_flags} {file_list}"
            # Print the actual command so you can debug include paths easily
            print_green(f"[SIM] Verilator cmd: {verilator_cmd}")

            exe_name = "V" + top_module if top_module else "simv"
            exe_path = os.path.join(obj_dir, exe_name)
            cmd = f"{verilator_cmd} && {shlex.quote(exe_path)}"
            print_green(f"[SIM] Running Verilator and executing: {cmd}")
            return _run_shell_cmd(cmd, repo_root, timeout, config_path)
    finally:
        # Keep tmpdir for debugging. If you prefer cleanup, uncomment:
        # shutil.rmtree(tmpdir, ignore_errors=True)
        pass



def _run_shell_cmd(cmd: str, cwd: str, timeout: int, config_path: str) -> tuple:
    """
    Run a shell command streaming stdout/stderr to console and capturing it.
    Returns (rc, output_text, config_path).
    """
    # Use bash to support complex commands with &&, etc.
    proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        executable="/bin/bash",
    )
    out_lines = []
    start_t = time.time()
    try:
        while True:
            line = proc.stdout.readline()
            if line:
                out_lines.append(line)
                print(line, end="")  # echo to console for visibility
            if proc.poll() is not None:
                remaining = proc.stdout.read()
                if remaining:
                    out_lines.append(remaining)
                    print(remaining, end="")
                break
            if (time.time() - start_t) > timeout:
                proc.kill()
                return 1, f"[SIM-TIMEOUT] Simulator timed out after {timeout}s\n{''.join(out_lines)}", config_path
        return proc.returncode, "".join(out_lines), config_path
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        return 1, f"[SIM-ERROR] {e}\n{''.join(out_lines)}", config_path

def _search_repo_for_basename(repo_root: str, basename: str) -> list:
    """Search repo for files ending with basename (fast heuristic). Returns full paths."""
    matches = []
    for root, _, files in os.walk(repo_root):
        for f in files:
            if f == basename:
                matches.append(os.path.relpath(os.path.join(root, f), repo_root))
    return matches

def parse_missing_includes_from_log(log_text: str) -> list:
    """
    Parse simulator output looking for missing include/file-not-found messages.
    Returns list of basenames that appear missing.
    This uses several common patterns (verilator, iverilog, ghdl, etc.).
    """
    missing = set()
    # common patterns (case-insensitive)
    patterns = [
        r"can't find file \"([^\"]+)\"",
        r"Can't find file \"([^\"]+)\"",
        r"unable to find include file \"([^\"]+)\"",
        r"unable to find include file '([^']+)'",
        r"no such file or directory: '([^']+)'",
        r"no such file or directory: \"([^\"]+)\"",
        r"fatal: can't open file '([^']+)'",
        r"fatal: can't open file \"([^\"]+)\"",
        r"can't open file \"([^\"]+)\"",
        r"can't open file '([^']+)'",
        r"error: file not found: \"([^\"]+)\"",
        r"error: file not found: '([^']+)'",
        # Verilator-specific include-not-found patterns:
        r"Cannot find include file: ['\"]([^'\"]+)['\"]",
        r"%Error: .*Cannot find include file: ['\"]([^'\"]+)['\"]",
    ]

    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            group = m.group(1).strip()
            # if it's a path, take its basename
            missing.add(os.path.basename(group))
    # also catch lines that mention an include directive missing (heuristic)
    # e.g. `Include file "foo.svh" not found`
    for m in re.finditer(r'["\']([^"\']+\.(svh|vh|vhdr|v|sv|svh|vhd|vhdl))["\'] not found', log_text, flags=re.IGNORECASE):
        missing.add(os.path.basename(m.group(1)))
    return list(missing)

def _add_include_dirs_from_missing_files(repo_root: str, include_dirs: set, missing_basenames: list) -> list:
    """
    For each basename in missing_basenames, search the repo for matching files.
    Add their directories to include_dirs and return list of newly added dirs (rel paths).
    """
    newly_added = []
    for b in missing_basenames:
        if not b:
            continue
        matches = _search_repo_for_basename(repo_root, b)
        for m in matches:
            dirpath = os.path.dirname(m) or "."
            if dirpath not in include_dirs:
                include_dirs.add(dirpath)
                newly_added.append(dirpath)
    return newly_added

def interactive_simulate_and_minimize(
    repo_root: str,
    repo_name: str,
    url: str,
    tb_files: list,
    candidate_files: list,
    include_dirs: set,
    top_module: str,
    modules: list,
    language_version: str,
    maximize_attempts: int = 6,
    verilator_extra_flags: list | None = None,
    ghdl_extra_flags: list | None = None,
) -> tuple:
    """
    Phase 1: try simulation and add include dirs found in simulator logs.
    Phase 2: greedy minimization over module files while keeping/updating top_module.

    Returns (final_files, final_include_dirs, last_log, final_top_module)
    """
    files = list(candidate_files)
    inclu = set(include_dirs)

    def build_module_maps():
        """Return (module_to_file, module_files_ordered) based on current 'modules' and 'files'."""
        m2f = {}
        ordered = []
        if modules and isinstance(modules[0], dict):
            for m in modules:
                fname = m['file']
                rel = os.path.relpath(fname, repo_root) if os.path.isabs(fname) else fname
                m2f[m['module']] = rel
                if rel in files:
                    ordered.append(rel)
        else:
            for name, path in modules:
                rel = os.path.relpath(path, repo_root) if os.path.isabs(path) else path
                m2f[name] = rel
                if rel in files:
                    ordered.append(rel)
        return m2f, ordered

    module_to_file, module_files_ordered = build_module_maps()

    # ensure top_module exists in mapping; otherwise pick first available
    if not top_module or module_to_file.get(top_module, "") not in files:
        # pick first module whose file is present
        chosen = None
        for mname, mfile in module_to_file.items():
            if mfile in files:
                chosen = mname
                break
        if chosen:
            print_yellow(f"[TOP] Current top module missing; switching to detected module '{chosen}'")
            top_module = chosen
        else:
            print_yellow("[TOP] No module file detected among candidate files; leaving top_module empty.")
            top_module = ""

    last_log = ""
    success = False

    # Phase 1: include-fixing loop (unchanged)
    for attempt in range(maximize_attempts):
        rc, out, cfg = run_simulation_with_config(
            repo_root,
            repo_name,
            url,
            tb_files,
            files,
            inclu,
            top_module,
            language_version,
            timeout=300,
            verilator_extra_flags=verilator_extra_flags,
            ghdl_extra_flags=ghdl_extra_flags,
        )
        last_log = out
        if rc == 0:
            print_green(f"[SIM] Simulation succeeded on attempt {attempt+1}")
            success = True
            break

        missing = parse_missing_includes_from_log(out)
        if not missing:
            print_yellow("[SIM] No missing includes detected in log; cannot auto-add more include dirs.")
            break

        print_yellow(f"[SIM] Attempt {attempt+1}: Found missing basenames in log: {missing}")
        newly_added = _add_include_dirs_from_missing_files(repo_root, inclu, missing)
        if newly_added:
            print_green(f"[SIM] Added include dirs: {newly_added} — retrying simulation.")
            # rebuild module maps after potential include changes (files unchanged)
            module_to_file, module_files_ordered = build_module_maps()
            continue
        else:
            print_yellow("[SIM] Could not find any files corresponding to missing basenames in repo.")
            break

    # Phase 2: minimization (greedy), with top_module maintenance
    if not success:
        print_yellow("[SIM] Simulation did not succeed in phase 1. Minimization will still try, but results may be invalid.")
    print_green("[MIN] Starting greedy minimization over module-files")

    # Always rebuild the maps at start of minimization
    module_to_file, module_files_ordered = build_module_maps()
    top_module_file = module_to_file.get(top_module, "")

    # Iterate over an ordered copy of detected module files (we will mutate 'files' in the loop)
    for f in list(module_files_ordered):
        # Recompute maps at each iteration to keep in sync with removals
        module_to_file, module_files_ordered = build_module_maps()
        top_module_file = module_to_file.get(top_module, "")

        # skip if file already removed
        if f not in files:
            continue

        print_green(f"[MIN] Trying to remove file: {f}")

        # if f is not the current top module file, try simple removal
        if f != top_module_file:
            files.remove(f)
            rc, out, cfg = run_simulation_with_config(
                repo_root,
                repo_name,
                url,
                tb_files,
                files,
                inclu,
                top_module,
                language_version,
                timeout=240,
                verilator_extra_flags=verilator_extra_flags,
                ghdl_extra_flags=ghdl_extra_flags,
            )
            last_log = out
            if rc == 0:
                print_green(f"[MIN] OK to remove {f} (simulation still succeeds). File permanently excluded.")
                # removal kept; continue
                continue
            else:
                print_yellow(f"[MIN] Removing {f} broke simulation (rc={rc}). Restoring.")
                files.append(f)
                continue

        # If f is the file for the current top module, try to find an alternative top module
        print_yellow(f"[MIN] {f} is current top-module file. Attempting top-module swap to allow removal.")
        # candidates: other modules whose files are present and not equal to f
        alt_candidates = []
        for mname, mfile in module_to_file.items():
            if mfile != f and mfile in files:
                alt_candidates.append((mname, mfile))

        swapped = False
        for alt_name, alt_file in alt_candidates:
            print_green(f"[MIN] Trying alt top_module '{alt_name}' (file {alt_file}) and removing {f}")
            # try removing f and setting top_module to alt_name
            files.remove(f)
            prev_top = top_module
            top_module = alt_name
            rc, out, cfg = run_simulation_with_config(
                repo_root,
                repo_name,
                url,
                tb_files,
                files,
                inclu,
                top_module,
                language_version,
                timeout=240,
                verilator_extra_flags=verilator_extra_flags,
                ghdl_extra_flags=ghdl_extra_flags,
            )
            last_log = out
            if rc == 0:
                print_green(f"[MIN] Removed {f} and switched top module to {alt_name} successfully.")
                swapped = True
                break  # keep this change permanently
            else:
                print_yellow(f"[MIN] Swap to {alt_name} failed (rc={rc}). Restoring {f} and trying next candidate.")
                # restore file and top_module, try next candidate
                files.append(f)
                top_module = prev_top

        if not swapped:
            # no candidate worked — restore and keep original top
            if f not in files:
                files.append(f)
            print_yellow(f"[MIN] Could not remove top-module file {f}. It remains required.")

    # Final rebuild to ensure module mappings consistent and top_module points to a present file if possible
    module_to_file, module_files_ordered = build_module_maps()
    if module_to_file.get(top_module, "") not in files:
        # pick another
        new_top = None
        for mname, mfile in module_to_file.items():
            if mfile in files:
                new_top = mname
                break
        if new_top:
            print_yellow(f"[TOP] Final top module switched to '{new_top}' because previous top is missing.")
            top_module = new_top
        else:
            print_yellow("[TOP] No module file left to select as top; leaving top_module empty.")
            top_module = ""

    print_green("[MIN] Minimization finished.")
    return files, inclu, last_log, top_module



def get_top_module_file(modules: list[dict[str, str]], top_module: str) -> str:
    """
    Retrieves the file path of the specified top module from a list of module dictionaries.

    Args:
        modules (list[dict[str, str]]): A list of dictionaries where each dictionary
            contains the module name and its file path.
        top_module (str): The name of the top module to find.

    Returns:
        str: The file path of the top module if found, or an empty string otherwise.
    """
    for module in modules:
        if module['module'] == top_module:
            return module['file']

    return ''


def copy_hardware_template(repo_name: str) -> None:
    """
    Copies a hardware template file to a new destination, renaming it based on the repository name.

    Args:
        repo_name (str): The name of the repository to use in the destination file name.

    Returns:
        None
    """
    orig = 'rtl/template.sv'

    # Caminho do diretório de destino
    dest = f'rtl/{repo_name}.sv'

    if os.path.exists(dest):
        print_yellow('[WARN] RTL - Arquivo já existe')
        return

    # Copiar o diretório
    shutil.copy(orig, dest)


def generate_processor_config(
    url: str,
    add_config: bool,
    plot_graph: bool,
    config_file_path: str,
    no_llama: bool,
    model: str = 'qwen2.5:32b',
) -> None:
    """
    Generates a processor configuration by cloning a repository, analyzing its files,
    extracting modules, and optionally updating the configuration file and plotting graphs.

    Args:
        url (str): URL of the processor's repository to clone.
        add_config (bool): Whether to add the generated configuration to the config file.
        plot_graph (bool): Whether to plot the module dependency graphs.
        config_file_path (str): Path to the configuration file.
        no_llama (bool): Whether to use OLLAMA to identify the top module.

    Returns:
        None
    """
    repo_name = extract_repo_name(url)
    destination_path = clone_and_validate_repo(url, repo_name)
    if not destination_path:
        return

    files, extension = find_and_log_files(destination_path)
    modulename_list, modules = extract_and_log_modules(files, destination_path)

    tb_files, non_tb_files = categorize_files(
        files, repo_name, destination_path
    )
    include_dirs = find_and_log_include_dirs(destination_path)
    module_graph, module_graph_inverse = build_and_log_graphs(files, modules)
    print(module_graph)

    filtered_files, top_module = process_files_with_llama(
        no_llama,
        non_tb_files,
        tb_files,
        modules,
        module_graph,
        repo_name,
        model,
    )
    language_version = determine_language_version(extension)

    final_files, final_include_dirs, last_log, top_module = interactive_simulate_and_minimize(
        destination_path,
        repo_name,
        url,
        tb_files,
        filtered_files,
        include_dirs,
        top_module,
        modules,
        language_version,
        verilator_extra_flags=['-Wno-lint', '-Wno-fatal']
    )

    output_json = create_output_json(
        repo_name,
        url,
        tb_files,
        final_files,
        final_include_dirs,
        top_module,
        language_version,
    )
    print_json_output(output_json)

    if add_config:
        add_to_config_file(config_file_path, repo_name, output_json)

    save_log_and_generate_template(
        repo_name,
        output_json,
        modulename_list,
        top_module,
        model=model,
    )

    cleanup_repo_and_plot_graphs(
        repo_name, plot_graph, module_graph, module_graph_inverse
    )


# Helper functions for modularity


def extract_repo_name(url: str) -> str:
    """
    Extracts the repository name from the given URL.

    Args:
        url (str): The URL of the repository.

    Returns:
        str: The name of the repository without the '.git' extension.
    """
    return url.split('/')[-1].replace('.git', '')


def clone_and_validate_repo(url: str, repo_name: str) -> str:
    """
    Clones the repository and validates the operation.

    Args:
        url (str): The URL of the repository to clone.
        repo_name (str): The name of the repository.

    Returns:
        str: The destination path of the cloned repository, or an empty string if cloning fails.
    """
    destination_path = clone_repo(url, repo_name)
    if not destination_path:
        print_red('[ERROR] Não foi possível clonar o repositório.')
    else:
        print_green('[LOG] Repositório clonado com sucesso\n')
    return destination_path


def find_and_log_files(destination_path: str) -> tuple:
    """
    Finds files with specific extensions in the repository and logs the result.

    Args:
        destination_path (str): The path to the cloned repository.

    Returns:
        tuple: A tuple containing a list of file paths and the common extension found.
    """
    print_green(
        '[LOG] Procurando arquivos com extensão .v, .sv, .vhdl ou .vhd\n'
    )
    files, extension = find_files_with_extension(destination_path, EXTENSIONS)
    print_green('[LOG] Arquivos encontrados com sucesso\n')
    return files, extension


def extract_and_log_modules(
    files: list, destination_path: str
) -> tuple[list, list]:
    """
    Extracts module information from files and logs the result.

    Args:
        files (list): A list of file paths.
        destination_path (str): The path to the cloned repository.

    Returns:
        list: A list of dictionaries containing module names and their file paths
        relative to the repository.
    """
    print_green('[LOG] Extraindo módulos dos arquivos\n')
    modules = extract_modules(files)
    print_green('[LOG] Módulos extraídos com sucesso\n')
    return [
        {
            'module': module_name,
            'file': os.path.relpath(file_path, destination_path),
        }
        for module_name, file_path in modules
    ], modules


def categorize_files(
    files: list, repo_name: str, destination_path: str
) -> tuple:
    """
    Categorizes files into testbench and non-testbench files.

    Args:
        files (list): A list of file paths.
        repo_name (str): The name of the repository.
        destination_path (str): The path to the cloned repository.

    Returns:
        tuple: A tuple containing lists of testbench and non-testbench file
        paths relative to the repository.
    """
    tb_files, non_tb_files = [], []
    for f in files:
        if is_testbench_file(f, repo_name):
            tb_files.append(f)
        else:
            non_tb_files.append(f)
    return (
        [os.path.relpath(tb_f, destination_path) for tb_f in tb_files],
        [
            os.path.relpath(non_tb_f, destination_path)
            for non_tb_f in non_tb_files
        ],
    )


def find_and_log_include_dirs(destination_path: str) -> list:
    """
    Finds include directories in the repository and logs the result.

    Args:
        destination_path (str): The path to the cloned repository.

    Returns:
        list: A list of include directory paths.
    """
    print_green('[LOG] Procurando diretórios de inclusão\n')
    include_dirs = find_include_dirs(destination_path)
    print_green('[LOG] Diretórios de inclusão encontrados com sucesso\n')
    return include_dirs


def build_and_log_graphs(files: list, modules: list) -> tuple:
    """
    Builds the direct and inverse module dependency graphs and logs the result.

    Args:
        files (list): A list of file paths.
        modules (list): A list of module information.

    Returns:
        tuple: A tuple containing the direct and inverse module graphs.
    """
    print_green('[LOG] Construindo os grafos direto e inverso\n')
    module_graph, module_graph_inverse = build_module_graph(files, modules)
    print_green('[LOG] Grafos construídos com sucesso\n')
    return module_graph, module_graph_inverse


def process_files_with_llama(
    no_llama: bool,
    non_tb_files: list,
    tb_files: list,
    modules: list,
    module_graph: dict,
    repo_name: str,
    model: str,
) -> tuple:
    """
    Processes files and identifies the top module using OLLAMA, if enabled.

    Args:
        no_llama (bool): Whether to skip OLLAMA processing.
        non_tb_files (list): A list of non-testbench file paths.
        tb_files (list): A list of testbench file paths.
        modules (list): A list of module information.
        module_graph (dict): The direct module dependency graph.
        repo_name (str): The name of the repository.
        model (str): The model to use with OLLAMA.

    Returns:
        tuple: A tuple containing the filtered file list and the top module name.
    """
    if not no_llama:
        print_green(
            '[LOG] Utilizando OLLAMA para identificar os arquivos do processador\n'
        )
        filtered_files = get_filtered_files_list(
            non_tb_files, tb_files, modules, module_graph, repo_name, model
        )
        print_green(
            '[LOG] Utilizando OLLAMA para identificar o módulo principal\n'
        )
        top_module = get_top_module(
            non_tb_files, tb_files, modules, module_graph, repo_name, model
        )
    else:
        filtered_files, top_module = non_tb_files, ''
    return filtered_files, top_module


def determine_language_version(extension: str) -> str:
    """
    Determines the language version based on the file extension.

    Args:
        extension (str): The file extension.

    Returns:
        str: The language version (e.g., '08', '2012', or '2005').
    """
    return {
        '.vhdl': '08',
        '.vhd': '08',
        '.sv': '2012',
    }.get(extension, '2005')


def create_output_json(
    repo_name,
    url,
    tb_files,
    filtered_files,
    include_dirs,
    top_module,
    language_version,
):
    """
    Creates the output JSON structure for the processor configuration.

    Args:
        repo_name (str): The name of the repository.
        url (str): The repository URL.
        tb_files (list): A list of testbench file paths.
        filtered_files (list): A list of filtered file paths.
        include_dirs (list): A list of include directories.
        top_module (str): The name of the top module.
        language_version (str): The HDL language version.

    Returns:
        dict: The output JSON structure.
    """
    return {
        'name': repo_name,
        'folder': repo_name,
        'sim_files': tb_files,
        'files': filtered_files,
        'include_dirs': list(include_dirs),
        'repository': url,
        'top_module': top_module,
        'extra_flags': [],
        'language_version': language_version,
        'march': 'rv32i',
        'two_memory': False,
    }


def print_json_output(output_json: dict) -> None:
    """
    Prints the generated output JSON to the console.

    Args:
        output_json (dict): The JSON structure to print.

    Returns:
        None
    """
    print('Result: ')
    print(json.dumps(output_json, indent=4))


def add_to_config_file(
    config_file_path: str, repo_name: str, output_json: dict
) -> None:
    """
    Adds the generated configuration to the config file.

    Args:
        config_file_path (str): Path to the configuration file.
        repo_name (str): The name of the repository.
        output_json (dict): The JSON structure of the configuration.

    Returns:
        None
    """

    save_config(config_file_path, output_json, repo_name)


def save_log_and_generate_template(
    repo_name,
    output_json,
    modules,
    top_module,
    model: str = 'qwen3:14b',
):
    """
    Saves the log file and generates the hardware template.

    Args:
        repo_name (str): The name of the repository.
        output_json (dict): The output JSON structure.
        modules (list): The extracted modules.
        module_graph (dict): The direct module dependency graph.
        module_graph_inverse (dict): The inverse module dependency graph.
        non_tb_files (list): A list of non-testbench file paths.
        top_module (str): The name of the top module.

    Returns:
        None
    """
    print_green('[LOG] Salvando o log em logs/\n')
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open(
        f'logs/{repo_name}_{time.time()}.json', 'w', encoding='utf-8'
    ) as log_file:
        log_file.write(json.dumps(output_json, indent=4))
    print_green('[LOG] Arquivo de log salvo com sucesso\n')

    if top_module:
        top_module_file = get_top_module_file(modules, top_module)
        if top_module_file:
            generate_top_file(top_module_file, repo_name, model=model)
        else:
            print_red('[ERROR] Módulo principal não encontrado')
    else:
        copy_hardware_template(repo_name)


def cleanup_repo_and_plot_graphs(
    repo_name, plot_graph, module_graph, module_graph_inverse
):
    """
    Cleans up the cloned repository and optionally plots graphs.

    Args:
        repo_name (str): The name of the repository.
        plot_graph (bool): Whether to plot the dependency graphs.
        module_graph (dict): The direct module dependency graph.
        module_graph_inverse (dict): The inverse module dependency graph.

    Returns:
        None
    """
    print_green('[LOG] Removendo o repositório clonado\n')
    remove_repo(repo_name)
    print_green('[LOG] Repositório removido com sucesso\n')

    if plot_graph:
        print_green('[LOG] Plotando os grafos\n')
        plot_processor_graph(module_graph, module_graph_inverse)
        print_green('[LOG] Grafos plotados com sucesso\n')


def generate_all_pipelines(config_dir: str) -> None:
    """
    Generates Jenkinsfiles for all processors defined in the configuration file.

    Args:
        config_dir (str): Path to the configuration dir.

    Returns:
        None
    """
    if not os.path.exists(config_dir):
        print_red('[ERROR] Config directory not found')
        raise FileNotFoundError(f'Config directory {config_dir} not found')

    files = os.listdir(config_dir)
    if not files:
        print_red('[ERROR] Config directory is empty')
        raise FileNotFoundError('Config directory is empty')

    for file in files:
        if not file.endswith('.json'):
            print_red(f'[ERROR] Invalid file: {file}')
            continue

        config = load_config(config_dir, file.replace('.json', ''))

        generate_jenkinsfile(
            config,
            FPGAs,
            MAIN_SCRIPT_PATH,
            config['language_version'],
            config['extra_flags'],
        )
        os.rename('Jenkinsfile', f'{BASE_DIR}{config["name"]}.Jenkinsfile')

    print('Jenkinsfiles generated successfully.')


def main() -> None:
    """
    Main entry point of the script. Parses command-line arguments and executes the
    corresponding actions.

    Command-line arguments:
        -j, --generate-all-jenkinsfiles: Generates Jenkinsfiles for the processors.
        -c, --generate-config: Generates a processor configuration.
        -g, --plot-graph: Plots the module dependency graph.
        -a, --add-config: Adds the generated configuration to the config file.
        -p, --path-config: Path to the config file (default: 'config.json').
        -u, --processor-url: URL of the processor repository.
        -n, --no-llama: Whether to use OLLAMA to identify the top module.
        -m, --model: Model to use for OLLAMA (default: 'qwen2.5:32b').

    Raises:
        ValueError: If `--generate-config` is used without providing `--processor-url`.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description='Script para gerar as configurações de um processador'
    )

    parser = argparse.ArgumentParser(
        description='Script to generate processor configurations'
    )

    parser.add_argument(
        '-j',
        '--generate-all-jenkinsfiles',
        action='store_true',
        help='Generates a Jenkinsfiles for the processors',
    )
    parser.add_argument(
        '-c',
        '--generate-config',
        action='store_true',
        help='Generates a processor configuration',
    )
    parser.add_argument(
        '-g',
        '--plot-graph',
        action='store_true',
        help='Plots the graph of the generated configuration',
    )
    parser.add_argument(
        '-a',
        '--add-config',
        action='store_true',
        help='Adds the generated configuration to the config file',
    )
    parser.add_argument(
        '-p',
        '--path-config',
        type=str,
        default='config',
        help='Path to the config folder',
    )
    parser.add_argument(
        '-u',
        '--processor-url',
        type=str,
        help='URL of the processor repository',
    )
    parser.add_argument(
        '-n',
        '--no-llama',
        action='store_true',
        help='Não utilizar o OLLAMA para identificar o módulo principal',
    )
    parser.add_argument(
        '-m',
        '--model',
        type=str,
        default='qwen2.5:32b',
        help='Modelo a ser utilizado pelo OLLAMA',
    )

    args = parser.parse_args()

    if args.generate_config:
        if not args.processor_url:
            raise ValueError('Argumento processor-url não encontrado')

        generate_processor_config(
            args.processor_url,
            args.add_config,
            args.plot_graph,
            args.path_config,
            args.no_llama,
            args.model,
        )

    if args.generate_all_jenkinsfiles:
        generate_all_pipelines(args.path_config)

    if not args.generate_config and not args.generate_all_jenkinsfiles:
        print('Nenhum comando fornecido, utilize --help para listar as opcões')


if __name__ == '__main__':
    main()
    # try:
    #    main()
    # except Exception as e:
    #    print_red(f'[ERROR] {e}')
    #    if os.path.exists('temp'):
    #        shutil.rmtree('temp')
    #    sys.exit(1)
    # finally:
    #    if os.path.exists('temp'):
    #        shutil.rmtree('temp')
