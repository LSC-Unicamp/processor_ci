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
from typing import Any, Dict, List
from collections import deque
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
UTILITY_PATTERNS = (
    "gen_", "dff", "buf", "full_handshake", "fifo", "mux", "regfile"
)

def _ensure_mapping(mapping: Any) -> Dict[str, List[str]]:
    """
    Normalize a graph-like input into a dict: node -> list(children/parents).
    Accepts:
      - dict[node] = list/tuple/set/str/None
      - list of (node, children) pairs
      - list of node names (then each node -> [])
    Returns an empty dict for unsupported shapes.
    """
    out: Dict[str, List[str]] = {}
    if not mapping:
        return out

    # If it's already a dict, normalize each value into a list
    if isinstance(mapping, dict):
        for k, v in mapping.items():
            if v is None:
                out[str(k)] = []
            elif isinstance(v, (list, tuple, set)):
                out[str(k)] = [str(x) for x in v]
            else:
                out[str(k)] = [str(v)]
        return out

    # If it's a list/tuple, try to interpret as pairs first
    if isinstance(mapping, (list, tuple)):
        # candidate: list of (node, children)
        pair_like = all(isinstance(el, (list, tuple)) and len(el) == 2 for el in mapping)
        if pair_like:
            for parent, children in mapping:
                key = str(parent)
                if children is None:
                    out.setdefault(key, [])
                elif isinstance(children, (list, tuple, set)):
                    out.setdefault(key, []).extend(str(x) for x in children)
                else:
                    out.setdefault(key, []).append(str(children))
            return out
        # candidate: list of node names
        if all(isinstance(el, (str, bytes)) for el in mapping):
            for node in mapping:
                out[str(node)] = []
            return out

    # fallback: try to iterate and coerce pairs, else return empty
    try:
        for el in mapping:
            if isinstance(el, (list, tuple)) and len(el) >= 2:
                key = str(el[0])
                val = el[1]
                if isinstance(val, (list, tuple, set)):
                    out.setdefault(key, []).extend(str(x) for x in val)
                else:
                    out.setdefault(key, []).append(str(val))
            elif isinstance(el, (str, bytes)):
                out.setdefault(str(el), [])
    except Exception:
        pass

    return out


def _reachable_size(children_of: Any, start: str) -> int:
    """
    Return number of reachable distinct nodes (excluding start) from `start`
    using BFS. Accepts children_of in many forms; normalizes internally.
    """
    children_map = _ensure_mapping(children_of)
    seen = set()
    q = deque([start])
    while q:
        cur = q.popleft()
        kids = children_map.get(cur, []) or []
        # normalize kids if someone passed a scalar by mistake
        if isinstance(kids, (str, bytes)):
            kids = [kids]
        for ch in kids:
            chs = str(ch)
            if chs not in seen and chs != start:
                seen.add(chs)
                q.append(chs)
    return len(seen)


def rank_top_candidates(module_graph, module_graph_inverse, repo_name=None):
    children_of = _ensure_mapping(module_graph)
    parents_of = _ensure_mapping(module_graph_inverse)

    nodes = set(children_of.keys()) | set(parents_of.keys())
    for n in nodes:
        children_of.setdefault(n, [])
        parents_of.setdefault(n, [])

    # Filter out Verilog keywords and invalid module names
    valid_modules = []
    verilog_keywords = {"if", "else", "always", "initial", "begin", "end", "case", "default", "for", "while", "assign"}
    
    for module in nodes:
        if (module not in verilog_keywords and 
            len(module) > 1 and 
            module.isalnum() or '_' in module):
            valid_modules.append(module)
    
    # Find candidates: prefer modules with few or no parents, but include important CPU modules
    # even if they have some parents
    zero_parent_modules = [m for m in valid_modules if not parents_of.get(m, [])]
    
    # Also include likely CPU top modules even if they have parents (they might be instantiated in testbenches)
    cpu_modules = [m for m in valid_modules if any(key in m.lower() for key in ["soc_top", "soc", repo_name.lower(), "core", "cpu"]) and "tb" not in m.lower()]
    
    candidates = list(set(zero_parent_modules + cpu_modules))
    
    if not candidates:
        min_par = min((len(parents_of.get(m, [])) for m in valid_modules), default=0)
        candidates = [m for m in valid_modules if len(parents_of.get(m, [])) <= min_par + 2]

    repo_lower = (repo_name or "").lower()
    scored = []
    for c in candidates:
        reach = _reachable_size(children_of, c)
        score = reach * 100  # Increase base score multiplier

        name_lower = c.lower()

        # High priority: exact repo name match (highest for core modules)
        if repo_lower and repo_lower == name_lower:  # Exact repo match like "tinyriscv"
            score += 6000
        elif repo_lower and repo_lower in name_lower:
            score += 4000
        
        # CPU/Core modules (highest priority - we want the core, not the SoC wrapper)
        if any(tok in name_lower for tok in ("core", "cpu", "processor")) and "soc" not in name_lower:
            score += 5000
        elif any(tok in name_lower for tok in ("riscv", "risc")) and "soc" not in name_lower:
            score += 4500
            
        # SoC/System level modules (lower priority - these include peripherals we may not need)
        if any(tok in name_lower for tok in ("soc_top", "tinyriscv_soc_top", "soc")):
            score += 3000
        elif any(tok in name_lower for tok in ("chip_top", "system_top")):
            score += 2500
        elif any(tok in name_lower for tok in ("_top", "top")) and "soc" not in name_lower:
            score += 1500


        # Heavily penalize testbenches
        if any(tok in name_lower for tok in ("tb", "test", "bench", "sim", "case")):
            score -= 5000

        # Heavily penalize peripheral modules 
        if any(tok in name_lower for tok in ("uart", "spi", "i2c", "gpio", "timer", "ram", "rom", "dma")):
            score -= 3000
            
        # Penalize debug modules
        if any(tok in name_lower for tok in ("debug", "jtag")):
            score -= 2000

        # Penalize utility modules
        if any(name_lower.startswith(pat) or pat in name_lower for pat in UTILITY_PATTERNS):
            score -= 4000
        
        # Favor modules with more connections (likely top-level)
        if reach < 5:
            score -= 2000

        score -= len(name_lower) * 0.5
        scored.append((score, reach, c))

    scored.sort(reverse=True, key=lambda t: (t[0], t[1], t[2]))
    return [c for _, _, c in scored if _ > -2000]  # filter out heavily penalized


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
    """

    # write config JSON for debugging / reproducibility
    config = create_output_json(
        repo_name, url, tb_files, files, include_dirs, top_module, language_version
    )
    tmpdir = tempfile.mkdtemp(prefix="simcfg_")
    try:
        config_path = os.path.join(tmpdir, f"{repo_name}_sim_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # >>>> Debug pause here <<<<
        print_green(f"[DEBUG] Config JSON written to {config_path}")
        #_ = input("[DEBUG] Press Enter to continue simulation...")

        # Normalize & sort include dirs
        include_dirs_sorted = sorted(include_dirs)

        # --- Build robust Verilator include flags ---
        incdir_flags_list = []
        for d in include_dirs_sorted:
            if " " in d:
                incdir_flags_list.append(f'+incdir+"{d}"')
            else:
                incdir_flags_list.append(f"+incdir+{d}")
        incdir_flags = " ".join(incdir_flags_list)
        i_flags = " ".join(f"-I{shlex.quote(d)}" for d in include_dirs_sorted) if include_dirs_sorted else ""
        include_flags_verilator = " ".join(filter(None, [incdir_flags, i_flags]))

        # GHDL include flags
        include_flags_ghdl = " ".join(f"-P{shlex.quote(d)}" for d in include_dirs_sorted) if include_dirs_sorted else ""

        verilator_extra_flags = verilator_extra_flags or []
        ghdl_extra_flags = ghdl_extra_flags or []

        file_list = " ".join(shlex.quote(f) for f in files)

        if language_version and language_version.lower() in ("vhd", "vhdl"):
            ghdl_flags = " ".join(shlex.quote(f) for f in ghdl_extra_flags)
            cmd = (
                f"ghdl -a {include_flags_ghdl} {ghdl_flags} {file_list} "
                f"&& ghdl -e {shlex.quote(top_module)}"
            )
            print_green(f"[SIM] Running GHDL syntax check: {cmd}")
            return _run_shell_cmd(cmd, repo_root, timeout, config_path)
        else:
            extra_flags = " ".join(shlex.quote(f) for f in verilator_extra_flags)
            top_opt = f"--top-module {shlex.quote(top_module)}" if top_module else ""
            # Use lint mode instead of trying to build executable
            verilator_cmd = (
                f"verilator --lint-only {top_opt} "
                f"{include_flags_verilator} {extra_flags} {file_list}"
            )
            print_green(f"[SIM] Verilator syntax check: {verilator_cmd}")
            return _run_shell_cmd(verilator_cmd, repo_root, timeout, config_path)
    finally:
        # Keep tmpdir for debugging
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
    modules: list,
    module_graph: dict,
    module_graph_inverse: dict,
    language_version: str,
    maximize_attempts: int = 6,
    verilator_extra_flags: list | None = None,
    ghdl_extra_flags: list | None = None,
) -> tuple:
    """
    Interactive simulation:
      A) Fix include dirs using a bootstrap top candidate.
      B) Choose the real top_module once includes are fixed.
      C) Minimize the file list while keeping the chosen top.
    Returns (final_files, final_include_dirs, last_log, final_top_module).
    """
    files = list(candidate_files)
    inclu = set(include_dirs)
    last_log = ""

    # --------------------------
    # Phase A: include fixing
    # --------------------------
    bootstrap_candidates = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name)
    print_green(f"[BOOT] Bootstrap candidates: {bootstrap_candidates[:5]}")
    
    # Try to find a good bootstrap candidate (prefer CPU modules over peripherals)
    heuristic_top = None
    for candidate in bootstrap_candidates:
        if any(word in candidate.lower() for word in ["soc", "core", "cpu", repo_name.lower()]):
            heuristic_top = candidate
            break
    
    if not heuristic_top and bootstrap_candidates:
        heuristic_top = bootstrap_candidates[0]
    
    if not heuristic_top:
        print_red("[ERROR] No suitable top module candidates found")
        return files, inclu, last_log, ""
    
    print_green(f"[BOOT] Using heuristic bootstrap top_module: {heuristic_top}")

    for attempt in range(maximize_attempts):
        rc, out, cfg = run_simulation_with_config(
            repo_root,
            repo_name,
            url,
            tb_files,
            files,
            inclu,
            heuristic_top,
            language_version,
            timeout=120,
            verilator_extra_flags=verilator_extra_flags,
            ghdl_extra_flags=ghdl_extra_flags,
        )
        last_log = out
        if rc == 0:
            print_green(f"[BOOT] Bootstrap sim succeeded at attempt {attempt+1}")
            break

        missing = parse_missing_includes_from_log(out)
        if not missing:
            print_yellow("[BOOT] No missing includes detected; stopping include-fix loop")
            break

        newly_added = _add_include_dirs_from_missing_files(repo_root, inclu, missing)
        if newly_added:
            print_green(f"[BOOT] Added include dirs: {newly_added} — retrying")
        else:
            print_yellow("[BOOT] Could not resolve missing includes")
            break

    # --------------------------
    # Phase B: top selection
    # --------------------------
    candidates = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name)
    print_green(f"[TOP-CAND] Ranked candidates: {candidates}")

    selected_top = None
    working_candidates = []
    
    # Test all candidates to find working ones
    for cand in candidates:
        rc, out, cfg = run_simulation_with_config(
            repo_root,
            repo_name,
            url,
            tb_files,
            files,
            inclu,
            cand,
            language_version,
            timeout=120,
            verilator_extra_flags=verilator_extra_flags,
            ghdl_extra_flags=ghdl_extra_flags,
        )
        last_log = out
        if rc == 0:
            print_green(f"[TOP-CAND] Candidate '{cand}' succeeded")
            working_candidates.append(cand)
        else:
            print_yellow(f"[TOP-CAND] Candidate '{cand}' failed (rc={rc})")
    
    # Prefer core modules over SoC wrappers from working candidates
    if working_candidates:
        repo_lower = (repo_name or "").lower()
        # First priority: exact repo name match (like "tinyriscv")
        for cand in working_candidates:
            if repo_lower and repo_lower == cand.lower():
                selected_top = cand
                print_green(f"[TOP-CAND] Selected core module '{selected_top}' (exact repo match)")
                break
        
        # Second priority: core/CPU modules without "soc" 
        if not selected_top:
            for cand in working_candidates:
                cand_lower = cand.lower()
                if (any(tok in cand_lower for tok in ["core", "cpu"]) and "soc" not in cand_lower):
                    selected_top = cand
                    print_green(f"[TOP-CAND] Selected core module '{selected_top}' (core/cpu preference)")
                    break
        
        # Fallback: first working candidate
        if not selected_top:
            selected_top = working_candidates[0]
            print_green(f"[TOP-CAND] Selected first working candidate '{selected_top}'")

    if not selected_top:
        selected_top = candidates[0] if candidates else heuristic_top
        print_yellow(f"[TOP-CAND] Falling back to heuristic choice: {selected_top}")

    top_module = selected_top

    # --------------------------
    # Phase C: greedy minimization
    # --------------------------
    print_green("[MIN] Starting greedy minimization")

    # Build map: module -> file
    module_to_file = {}
    if modules and isinstance(modules[0], dict):
        for m in modules:
            rel = os.path.relpath(m["file"], repo_root) if os.path.isabs(m["file"]) else m["file"]
            module_to_file[m["module"]] = rel
    else:
        for name, path in modules:
            rel = os.path.relpath(path, repo_root) if os.path.isabs(path) else path
            module_to_file[name] = rel

    for f in list(files):
        # Stop minimization if we're down to just peripheral modules and the top is a peripheral
        if (top_module in ["uart", "spi", "i2c", "gpio", "timer"] and 
            len(files) <= 5 and 
            all("core" not in fname for fname in files)):
            print_yellow(f"[MIN] Stopping minimization - detected peripheral-only configuration")
            break
            
        is_top_file = module_to_file.get(top_module, "") == f
        print_green(f"[MIN] Trying to remove file: {f}")
        files.remove(f)

        if not is_top_file:
            # Normal case: keep same top
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
                print_green(f"[MIN] Removed {f} successfully")
                continue
            else:
                print_yellow(f"[MIN] Removing {f} broke sim, restoring")
                files.append(f)
                continue

        # Special case: removed the top file
        print_yellow(f"[MIN] Removed file of current top '{top_module}', trying to reselect…")
        candidates = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name)
        new_top = None
        for cand in candidates:
            # skip if module not present anymore
            if module_to_file.get(cand, "") not in files:
                continue
            rc, out, cfg = run_simulation_with_config(
                repo_root,
                repo_name,
                url,
                tb_files,
                files,
                inclu,
                cand,
                language_version,
                timeout=240,
                verilator_extra_flags=verilator_extra_flags,
                ghdl_extra_flags=ghdl_extra_flags,
            )
            last_log = out
            if rc == 0:
                new_top = cand
                break

        if new_top:
            print_green(f"[MIN] Promoted new top_module: {new_top}")
            top_module = new_top
        else:
            print_yellow(f"[MIN] No valid replacement top found, restoring {f}")
            files.append(f)



    print_green("[MIN] Minimization finished")
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
        repo_root=destination_path,
        repo_name=repo_name,
        url=url,
        tb_files=tb_files,
        candidate_files=filtered_files,
        include_dirs=set(include_dirs),
        modules=modules,
        module_graph=module_graph,
        module_graph_inverse=module_graph_inverse,
        language_version=language_version,
        maximize_attempts=6,
        verilator_extra_flags=['-Wno-lint', '-Wno-fatal'],
        ghdl_extra_flags=['--std=08'],
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
            #generate_top_file(top_module_file, repo_name, model=model)
            print_red('[WARN] Geração automática do template desativada temporariamente')
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
        try:
            # Set matplotlib to use a non-GUI backend
            import matplotlib
            matplotlib.use('Agg')
            plot_processor_graph(module_graph, module_graph_inverse)
            print_green('[LOG] Grafos plotados com sucesso\n')
        except ImportError as e:
            print_yellow(f'[WARN] Could not plot graphs: {e}\n')
        except Exception as e:
            print_yellow(f'[WARN] Error plotting graphs: {e}\n')


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
