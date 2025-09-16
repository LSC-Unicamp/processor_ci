"""
Processor Configuration Generator

This script analyzes processor repositories and generates processor configurations.
It includes the following functionality:
- Cloning processor repositories and analyzing their files.
- Extracting hardware modules and testbench files from the repository.
- Building module dependency graphs.
- Generating configuration files for the processor.
- Interactive simulation and file minimization.

Main Functions:
--------------
- **generate_processor_config**: Clones a repository, analyzes it, and generates a configuration
- **interactive_simulate_and_minimize**: Optimizes file lists through simulation
- **rank_top_candidates**: Identifies the best top module candidates

Command-Line Interface:
-----------------------
- `-u`, `--processor-url`: URL of the processor repository to clone.
- `-p`, `--config-path`: Path to save the configuration file.
- `-g`, `--plot-graph`: Plots the module dependency graph.
- `-a`, `--add-to-config`: Adds the generated configuration to a central config file.
- `-n`, `--no-llama`: Skip OLLAMA processing for top module identification.
- `-m`, `--model`: OLLAMA model to use (default: 'qwen2.5:32b').

Usage:
------
python config_generator_core.py -u <processor_url> -p config/
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
)
from core.log import print_green, print_red, print_yellow


# Constants
EXTENSIONS = ['v', 'sv', 'vhdl', 'vhd']
DESTINATION_DIR = './temp'
UTILITY_PATTERNS = (
    "gen_", "dff", "buf", "full_handshake", "fifo", "mux", "regfile"
)


def _ensure_mapping(mapping: Any) -> Dict[str, List[str]]:
    """
    Normalize a graph-like input into a dict: node -> list(children/parents).
    """
    out: Dict[str, List[str]] = {}
    if not mapping:
        return out

    if isinstance(mapping, dict):
        for k, v in mapping.items():
            if v is None:
                out[str(k)] = []
            elif isinstance(v, (list, tuple, set)):
                out[str(k)] = [str(x) for x in v]
            else:
                out[str(k)] = [str(v)]
        return out

    if isinstance(mapping, (list, tuple)):
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
        if all(isinstance(el, (str, bytes)) for el in mapping):
            for node in mapping:
                out[str(node)] = []
            return out

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
    Return number of reachable distinct nodes (excluding start) from `start` using BFS.
    """
    children_map = _ensure_mapping(children_of)
    seen = set()
    q = deque([start])
    while q:
        cur = q.popleft()
        kids = children_map.get(cur, []) or []
        if isinstance(kids, (str, bytes)):
            kids = [kids]
        for ch in kids:
            chs = str(ch)
            if chs not in seen and chs != start:
                seen.add(chs)
                q.append(chs)
    return len(seen)


def rank_top_candidates(module_graph, module_graph_inverse, repo_name=None):
    """
    Rank module candidates to identify the best top module.
    """
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
            (module.replace('_', '').isalnum())):
            valid_modules.append(module)
    
    # Find candidates: modules with few parents are preferred
    zero_parent_modules = [m for m in valid_modules if not parents_of.get(m, [])]
    low_parent_modules = [m for m in valid_modules if len(parents_of.get(m, [])) <= 2]
    
    # Include repo name matches even if they have many parents
    repo_name_matches = []
    cpu_core_matches = []
    if repo_name and len(repo_name) > 2:
        repo_lower = repo_name.lower()
        for module in valid_modules:
            module_lower = module.lower()
            if (repo_lower == module_lower or 
                repo_lower in module_lower or 
                module_lower in repo_lower):
                repo_name_matches.append(module)
            
            # Check for likely CPU core modules
            if ((module_lower == 'balotelli' or 
                 any(pattern in module_lower for pattern in [repo_lower, 'cpu', 'core', 'risc', 'processor'])) and 
                module not in zero_parent_modules and module not in low_parent_modules and
                not any(bad_pattern in module_lower for bad_pattern in 
                       ['div', 'mul', 'alu', 'fpu', 'cache', 'mem', 'bus', 'ctrl', 'reg', 'decode', 'fetch', 'exec', 'forward', 'hazard', 'pred'])):
                if module not in repo_name_matches:
                    cpu_core_matches.append(module)
                    print_green(f"[DEBUG] Added likely CPU core: {module}")
    
    candidates = list(set(zero_parent_modules + low_parent_modules + repo_name_matches + cpu_core_matches))
    
    if not candidates:
        candidates = valid_modules

    # Debug output
    print_green(f"[DEBUG] valid_modules count: {len(valid_modules)}")
    print_green(f"[DEBUG] zero_parent_modules count: {len(zero_parent_modules)}")  
    print_green(f"[DEBUG] low_parent_modules count: {len(low_parent_modules)}")
    print_green(f"[DEBUG] final candidates count: {len(candidates)}")

    repo_lower = (repo_name or "").lower()
    scored = []
    
    for c in candidates:
        reach = _reachable_size(children_of, c)
        score = reach * 10  # Base score from connectivity
        name_lower = c.lower()

        # REPOSITORY NAME MATCHING (Highest Priority)
        if repo_lower and len(repo_lower) > 2:
            if repo_lower == name_lower:
                score += 50000
                print_green(f"[SCORE] {c}: +50000 (exact repo match)")
            elif repo_lower in name_lower:
                score += 40000
                print_green(f"[SCORE] {c}: +40000 (repo in module name)")
            elif name_lower in repo_lower:
                score += 35000
                print_green(f"[SCORE] {c}: +35000 (module in repo name)")
            else:
                # Fuzzy matching
                clean_repo = repo_lower
                clean_module = name_lower
                
                for pattern in ["_cpu", "_core", "cpu_", "core_", "_top", "top_"]:
                    clean_repo = clean_repo.replace(pattern, "")
                    clean_module = clean_module.replace(pattern, "")
                
                if clean_repo == clean_module and len(clean_repo) > 1:
                    score += 30000
                    print_green(f"[SCORE] {c}: +30000 (cleaned exact match)")
                elif clean_repo in clean_module or clean_module in clean_repo:
                    score += 20000
                    print_green(f"[SCORE] {c}: +20000 (cleaned partial match)")

        # ARCHITECTURAL INDICATORS
        if any(term in name_lower for term in ["cpu", "processor"]):
            score += 2000
        
        if "core" in name_lower:
            if any(unit in name_lower for unit in ["div", "mul", "alu", "fpu"]):
                score -= 5000
                print_green(f"[SCORE] {c}: -5000 (functional unit core)")
            else:
                score += 1500
        
        if any(arch in name_lower for arch in ["riscv", "risc", "mips", "arm"]):
            score += 1000
        
        if name_lower.endswith("_top") or name_lower.startswith("top_"):
            score += 800
        
        if "soc" in name_lower:
            score += 500

        # STRUCTURAL HEURISTICS
        num_children = len(children_of.get(c, []))
        num_parents = len(parents_of.get(c, []))
        
        if num_children > 10 and num_parents == 0:
            score += 1000
        elif num_children > 5 and num_parents <= 1:
            score += 500
        elif num_children > 2:
            score += 200

        # NEGATIVE INDICATORS
        if any(pattern in name_lower for pattern in ["_tb", "tb_", "test", "bench"]):
            score -= 10000
        
        peripheral_terms = ["uart", "spi", "i2c", "gpio", "timer", "dma", "plic", "clint"]
        if any(term in name_lower for term in peripheral_terms):
            score -= 3000
        
        if any(pattern in name_lower for pattern in ["debug", "jtag", "bram"]):
            score -= 2000
        
        if any(name_lower.startswith(pat) for pat in UTILITY_PATTERNS):
            score -= 2000
        
        if reach < 2:
            score -= 1000

        if len(name_lower) > 25:
            score -= len(name_lower) * 5
        elif len(name_lower) < 6:
            score += 100

        scored.append((score, reach, c))

    # Sort by score (descending), then by reach (descending), then by name
    scored.sort(reverse=True, key=lambda t: (t[0], t[1], t[2]))
    
    # Debug output
    print_green(f"[DEBUG] All scored candidates for repo '{repo_name}' (repo_lower='{repo_lower}'):")
    for i, (score, reach, name) in enumerate(scored):
        if "balotelli" in name.lower() or "divcore" in name.lower() or i < 15:
            print_green(f"  {i+1}. {name}: score={score}, reach={reach}")
    
    return [c for score, _, c in scored if score > -5000], cpu_core_matches


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
    Write a temporary JSON config and invoke the appropriate simulator.
    """
    config = create_output_json(
        repo_name, url, tb_files, files, include_dirs, top_module, language_version
    )
    tmpdir = tempfile.mkdtemp(prefix="simcfg_")
    try:
        config_path = os.path.join(tmpdir, f"{repo_name}_sim_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print_green(f"[DEBUG] Config JSON written to {config_path}")

        include_dirs_sorted = sorted(include_dirs)

        # Build Verilator include flags
        incdir_flags_list = []
        for d in include_dirs_sorted:
            if " " in d:
                incdir_flags_list.append(f'+incdir+"{d}"')
            else:
                incdir_flags_list.append(f"+incdir+{d}")
        incdir_flags = " ".join(incdir_flags_list)
        i_flags = " ".join(f"-I{shlex.quote(d)}" for d in include_dirs_sorted) if include_dirs_sorted else ""
        include_flags_verilator = " ".join(filter(None, [incdir_flags, i_flags]))
        print_green(f"[DEBUG] Verilator include flags: {include_flags_verilator}")

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
            
            # Add language standard flags based on version
            std_flags = ""
            if language_version == '2012' or any(f.endswith(('.sv', '.svh')) for f in files):
                std_flags = "--sv"
            elif language_version == '2017':
                std_flags = "--sv +1800-2017"
            elif language_version == '2009':
                std_flags = "+1364-2005 --sv"
            else:
                std_flags = "+1364-2005"
            
            verilator_cmd = (
                f"verilator --lint-only {std_flags} {top_opt} "
                f"{include_flags_verilator} {extra_flags} {file_list}"
            )
            print_green(f"[SIM] Verilator syntax check: {verilator_cmd}")
            rc, out, cfg = _run_shell_cmd(verilator_cmd, repo_root, timeout, config_path)
            
            # Fallback: if Verilog 2005 fails, try SystemVerilog
            if rc != 0 and std_flags == "+1364-2005":
                print_yellow("[SIM] Verilog 2005 failed, trying SystemVerilog fallback...")
                sv_cmd = (
                    f"verilator --lint-only --sv {top_opt} "
                    f"{include_flags_verilator} {extra_flags} {file_list}"
                )
                print_green(f"[SIM] SystemVerilog fallback: {sv_cmd}")
                return _run_shell_cmd(sv_cmd, repo_root, timeout, config_path)
            
            return rc, out, cfg
    finally:
        pass


def _run_shell_cmd(cmd: str, cwd: str, timeout: int, config_path: str) -> tuple:
    """
    Run a shell command streaming stdout/stderr to console and capturing it.
    """
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
                print(line, end="")
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
    """Search repo for files ending with basename. Returns full paths."""
    matches = []
    for root, _, files in os.walk(repo_root):
        for f in files:
            if f == basename:
                matches.append(os.path.relpath(os.path.join(root, f), repo_root))
    return matches


def parse_missing_includes_from_log(log_text: str) -> list:
    """
    Parse simulator output looking for missing include/file-not-found messages.
    """
    missing = set()
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
        r"Cannot find include file: ['\"]([^'\"]+)['\"]",
        r"%Error: .*Cannot find include file: ['\"]([^'\"]+)['\"]",
    ]

    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            group = m.group(1).strip()
            missing.add(os.path.basename(group))
    
    for m in re.finditer(r'["\']([^"\']+\.(svh|vh|vhdr|v|sv|svh|vhd|vhdl))["\'] not found', log_text, flags=re.IGNORECASE):
        missing.add(os.path.basename(m.group(1)))
    return list(missing)


def _add_include_dirs_from_missing_files(repo_root: str, include_dirs: set, missing_basenames: list) -> list:
    """
    For each basename in missing_basenames, search the repo for matching files.
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
    cpu_core_matches: list,
    maximize_attempts: int = 6,
    verilator_extra_flags: list | None = None,
    ghdl_extra_flags: list | None = None,
) -> tuple:
    """
    Interactive simulation and file minimization.
    """
    files = list(candidate_files)
    inclu = set(include_dirs)
    last_log = ""

    # Phase A: include fixing
    print_green(f"[DEBUG] Bootstrapping with repo_name='{repo_name}'")
    bootstrap_candidates, _ = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name)
    print_green(f"[BOOT] Bootstrap candidates: {bootstrap_candidates[:5]}")
    
    heuristic_top = None
    for candidate in bootstrap_candidates:
        words_to_check = ["soc", "core", "cpu"]
        if repo_name:
            words_to_check.append(repo_name.lower())
        print_green(f"[DEBUG] Checking candidate '{candidate}' against words {words_to_check}")
        if any(word in candidate.lower() for word in words_to_check):
            heuristic_top = candidate
            print_green(f"[DEBUG] Selected '{candidate}' as heuristic_top")
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

    # Phase B: top selection
    print_green(f"[DEBUG] About to rank candidates with repo_name='{repo_name}'")
    candidates, cpu_core_matches = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name)
    print_green(f"[TOP-CAND] Ranked candidates: {candidates}")
    print_green(f"[DEBUG] CPU core matches: {cpu_core_matches}")

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
        # First priority: exact repo name match
        for cand in working_candidates:
            if repo_lower and repo_lower == cand.lower():
                selected_top = cand
                print_green(f"[TOP-CAND] Selected core module '{selected_top}' (exact repo match)")
                break
        
        # Second priority: detected CPU cores
        if not selected_top:
            for cand in working_candidates:
                if cand in cpu_core_matches:
                    selected_top = cand
                    print_green(f"[TOP-CAND] Selected detected CPU core '{selected_top}' (cpu_core pattern match)")
                    break
        
        # Third priority: core/CPU modules without "soc" 
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

    # Phase C: greedy minimization
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
        # Stop minimization if we're down to just peripheral modules
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
        candidates, _ = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name)
        new_top = None
        for cand in candidates:
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


def detect_systemverilog_features(files: list) -> bool:
    """
    Analyze files to detect SystemVerilog-specific features.
    """
    sv_patterns = [
        r'\binterface\b', r'\bmodport\b', r'\bpackage\b', r'\bclass\b',
        r'\balways_ff\b', r'\balways_comb\b', r'\blogic\b', r'\bit\b',
        r'\bunique\b', r'\bpriority\b', r'\bassert\b', r'\bassume\b',
        r'\bcover\b', r'\b`define\b.*\\$', r'\bstruct\b', r'\bunion\b',
        r'\benum\b', r'\btypedef\b', r'\bvirtual\b', r'\bconstraint\b'
    ]
    
    combined_pattern = '|'.join(sv_patterns)
    sv_regex = re.compile(combined_pattern, re.IGNORECASE)
    
    for file_path in files[:10]:  # Check first 10 files
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)  # Read first 4KB
                if sv_regex.search(content):
                    return True
        except Exception:
            continue
    
    return False


def determine_language_version(extension: str, files: list = None) -> str:
    """
    Determines the language version based on the file extension and content analysis.
    """
    base_version = {
        '.vhdl': '08',
        '.vhd': '08', 
        '.sv': '2012',
        '.svh': '2012',
    }.get(extension, '2005')
    
    # If we have .v files but detect SystemVerilog features, upgrade to 2012
    if base_version == '2005' and files and detect_systemverilog_features(files):
        print_green("[LANG] Detected SystemVerilog features in .v files, upgrading to 2012")
        return '2012'
    
    return base_version


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


# Helper functions for modularity
def extract_repo_name(url: str) -> str:
    """Extracts the repository name from the given URL."""
    return url.split('/')[-1].replace('.git', '')


def clone_and_validate_repo(url: str, repo_name: str) -> str:
    """Clones the repository and validates the operation."""
    destination_path = clone_repo(url, repo_name)
    if not destination_path:
        print_red('[ERROR] Não foi possível clonar o repositório.')
    else:
        print_green('[LOG] Repositório clonado com sucesso\n')
    return destination_path


def find_and_log_files(destination_path: str) -> tuple:
    """Finds files with specific extensions in the repository and logs the result."""
    print_green('[LOG] Procurando arquivos com extensão .v, .sv, .vhdl ou .vhd\n')
    files, extension = find_files_with_extension(destination_path, EXTENSIONS)
    print_green('[LOG] Arquivos encontrados com sucesso\n')
    return files, extension


def extract_and_log_modules(files: list, destination_path: str) -> tuple[list, list]:
    """Extracts module information from files and logs the result."""
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


def categorize_files(files: list, repo_name: str, destination_path: str) -> tuple:
    """Categorizes files into testbench and non-testbench files."""
    tb_files, non_tb_files = [], []
    for f in files:
        if is_testbench_file(f, repo_name):
            tb_files.append(f)
        else:
            non_tb_files.append(f)
    return (
        [os.path.relpath(tb_f, destination_path) for tb_f in tb_files],
        [os.path.relpath(non_tb_f, destination_path) for non_tb_f in non_tb_files],
    )


def find_and_log_include_dirs(destination_path: str) -> list:
    """Finds include directories in the repository and logs the result."""
    print_green('[LOG] Procurando diretórios de inclusão\n')
    include_dirs = find_include_dirs(destination_path)
    print_green('[LOG] Diretórios de inclusão encontrados com sucesso\n')
    return include_dirs


def build_and_log_graphs(files: list, modules: list) -> tuple:
    """Builds the direct and inverse module dependency graphs and logs the result."""
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
    """Processes files and identifies the top module using OLLAMA, if enabled."""
    if not no_llama:
        print_green('[LOG] Utilizando OLLAMA para identificar os arquivos do processador\n')
        filtered_files = get_filtered_files_list(
            non_tb_files, tb_files, modules, module_graph, repo_name, model
        )
        print_green('[LOG] Utilizando OLLAMA para identificar o módulo principal\n')
        top_module = get_top_module(
            non_tb_files, tb_files, modules, module_graph, repo_name, model
        )
    else:
        filtered_files, top_module = non_tb_files, ''
    return filtered_files, top_module


def generate_processor_config(
    url: str,
    config_path: str,
    plot_graph: bool = False,
    add_to_config: bool = False,
    no_llama: bool = False,
    model: str = 'qwen2.5:32b',
) -> dict:
    """
    Main function to generate a processor configuration.
    """
    repo_name = extract_repo_name(url)
    destination_path = clone_and_validate_repo(url, repo_name)
    if not destination_path:
        return {}

    files, extension = find_and_log_files(destination_path)
    modulename_list, modules = extract_and_log_modules(files, destination_path)

    tb_files, non_tb_files = categorize_files(files, repo_name, destination_path)
    include_dirs = find_and_log_include_dirs(destination_path)
    module_graph, module_graph_inverse = build_and_log_graphs(files, modules)

    filtered_files, top_module = process_files_with_llama(
        no_llama, non_tb_files, tb_files, modules, module_graph, repo_name, model,
    )
    language_version = determine_language_version(extension, filtered_files)
    
    # Get cpu_core_matches for selection logic
    _, cpu_core_matches = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name)

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
        cpu_core_matches=cpu_core_matches,
        maximize_attempts=6,
        verilator_extra_flags=['-Wno-lint', '-Wno-fatal'],
        ghdl_extra_flags=['--std=08'],
    )

    output_json = create_output_json(
        repo_name, url, tb_files, final_files, final_include_dirs, top_module, language_version,
    )

    # Save configuration
    print_green('[LOG] Salvando configuração\n')
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    
    config_file = os.path.join(config_path, f"{repo_name}.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=4)
    
    if add_to_config:
        central_config_path = os.path.join(config_path, "config.json")
        save_config(central_config_path, output_json, repo_name)

    # Save log
    print_green('[LOG] Salvando o log em logs/\n')
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open(f'logs/{repo_name}_{time.time()}.json', 'w', encoding='utf-8') as log_file:
        log_file.write(json.dumps(output_json, indent=4))

    # Cleanup
    print_green('[LOG] Removendo o repositório clonado\n')
    remove_repo(repo_name)
    print_green('[LOG] Repositório removido com sucesso\n')

    # Plot graph if requested
    if plot_graph:
        print_green('[LOG] Plotando os grafos\n')
        try:
            import matplotlib
            matplotlib.use('Agg')
            plot_processor_graph(module_graph, module_graph_inverse)
            print_green('[LOG] Grafos plotados com sucesso\n')
        except ImportError as e:
            print_yellow(f'[WARN] Could not plot graphs: {e}\n')
        except Exception as e:
            print_yellow(f'[WARN] Error plotting graphs: {e}\n')

    return output_json


def main() -> None:
    """Main entry point for the config generator."""
    parser = argparse.ArgumentParser(description='Generate processor configurations')

    parser.add_argument(
        '-u', '--processor-url', type=str, required=True,
        help='URL of the processor repository'
    )
    parser.add_argument(
        '-p', '--config-path', type=str, default='config/',
        help='Path to save the configuration file'
    )
    parser.add_argument(
        '-g', '--plot-graph', action='store_true',
        help='Plot the module dependency graph'
    )
    parser.add_argument(
        '-a', '--add-to-config', action='store_true',
        help='Add the generated configuration to a central config file'
    )
    parser.add_argument(
        '-n', '--no-llama', action='store_true',
        help='Skip OLLAMA processing for top module identification'
    )
    parser.add_argument(
        '-m', '--model', type=str, default='qwen2.5:32b',
        help='OLLAMA model to use'
    )

    args = parser.parse_args()

    try:
        config = generate_processor_config(
            args.processor_url,
            args.config_path,
            args.plot_graph,
            args.add_to_config,
            args.no_llama,
            args.model,
        )
        
        print('Result: ')
        print(json.dumps(config, indent=4))
        
    except Exception as e:
        print_red(f'[ERROR] {e}')
        if os.path.exists('temp'):
            shutil.rmtree('temp')
        return 1


if __name__ == '__main__':
    main()
