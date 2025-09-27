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
import glob
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
    find_files_with_extension_smart,
    extract_modules,
    is_testbench_file,
    find_include_dirs,
    should_exclude_file,
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
    Return number reachable distinct nodes (excluding start) from `start` using BFS.
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


def _find_missing_dependencies(repo_root: str, files_to_check: list, module_to_file: dict, current_files: list) -> list:
    """
    Generic function to find missing dependencies for VHDL files.
    Analyzes import statements and finds required packages/entities not in current file list.
    """
    missing_deps = []
    checked_files = set()
    
    def analyze_file_dependencies(file_path: str):
        if file_path in checked_files:
            return
        checked_files.add(file_path)
        
        full_path = os.path.join(repo_root, file_path)
        if not os.path.exists(full_path):
            return
            
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return
            
        # Find use statements and library imports
        use_patterns = [
            r'use\s+work\.(\w+)\.all',      # use work.package.all
            r'use\s+work\.(\w+)',           # use work.package
            r'library\s+(\w+)',             # library name
        ]
        
        for pattern in use_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Skip standard libraries
                if match.lower() in ['ieee', 'std', 'work']:
                    continue
                    
                # Find the file that contains this package/entity
                dep_file = module_to_file.get(match, "")
                if dep_file and dep_file not in current_files and dep_file not in missing_deps:
                    missing_deps.append(dep_file)
                    print_green(f"[DEP] Found missing dependency: {match} -> {dep_file}")
                    # Recursively check dependencies of dependencies
                    analyze_file_dependencies(dep_file)
    
    # Start analysis with the provided files
    for file_path in files_to_check:
        analyze_file_dependencies(file_path)
    
    return missing_deps


def _analyze_instantiation_patterns(module_name: str, file_path: str) -> dict:
    """
    Analyze what types of components a module instantiates to classify it as CPU core vs SoC top.
    Returns a dict with counts of different component types found.
    """
    if not file_path or not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return {}
    
    # CPU core component patterns (things a CPU would instantiate)
    cpu_patterns = [
        r'\b(alu|arithmetic|logic)\b',
        r'\b(mul|mult|multiplier)\b', 
        r'\b(div|divider|division)\b',
        r'\b(fpu|float|floating)\b',
        r'\b(cache|icache|dcache)\b',
        r'\b(mmu|tlb)\b',
        r'\b(branch|pred|predictor)\b',
        r'\b(decode|decoder)\b',
        r'\b(execute|exec|execution)\b',
        r'\b(fetch|instruction)\b',
        r'\b(register|regfile|rf|mprf)\b',
        r'\b(pipeline|pipe)\b',
        r'\b(hazard|forward|forwarding)\b',
        r'\b(csr|control|status)\b',
        # SuperScalar and RISC-V specific patterns
        r'\b(schedule|scheduler|issue|dispatch)\b',
        r'\b(retire|commit|completion)\b',
        r'\b(reservation|station|rob|reorder)\b',
        r'\b(inst|instr|instruction)\b',
        r'\b(mem|memory)(?!_external|_ext|_sys)\b',  # Internal memory components
        r'\b(lsu|load|store)\b',
        r'\b(sys|system)_(?!bus|external)\b'  # System components but not external bus
    ]
    
    # SoC/System component patterns (things an SoC top would instantiate)
    # Note: Exclude memory/clock patterns that could be internal to CPU cores
    soc_patterns = [
        r'\b(gpio|pin|port)\b',
        r'\b(uart|serial)\b',
        r'\b(spi|i2c)\b',
        r'\b(timer|counter)\b',
        r'\b(interrupt|plic|clint)\b',
        r'\b(dma|direct|memory|access)\b',
        r'\b(peripheral|periph)\b',
        r'\b(bridge|interconnect)\b',
        r'\b(debug|jtag)\b',
        # Only count external memory interfaces, not internal ones
        r'\b(external_mem|ext_mem|ddr|sdram)\b',
        # Only count system-level bus interfaces 
        r'\b(system_bus|main_bus|soc_bus)\b'
    ]
    
    instantiation_regex = r'^\s*(\w+)\s*(?:#\s*\([^)]*\))?\s*(\w+)\s*\('

    cpu_score = 0
    soc_score = 0
    total_instances = 0
    instantiated_modules = []
    
    for match in re.finditer(instantiation_regex, content, re.MULTILINE | re.IGNORECASE):
        module_type = match.group(1).lower()
        instance_name = match.group(2).lower()
        total_instances += 1
        instantiated_modules.append(module_type)
        
        combined_text = f"{module_type} {instance_name}"
        
        for pattern in cpu_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                cpu_score += 1
                break  
        
        for pattern in soc_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                soc_score += 1
                break  
    
    return {
        'cpu_score': cpu_score,
        'soc_score': soc_score,
        'total_instances': total_instances,
        'cpu_ratio': cpu_score / max(total_instances, 1),
        'soc_ratio': soc_score / max(total_instances, 1),
        'instantiated_modules': instantiated_modules
    }


def _analyze_cpu_signals(module_name: str, file_path: str, instantiated_in_file: str) -> dict:
    """
    Analyze the signals/ports used when instantiating a module to determine if it's a CPU core.
    Look for CPU-characteristic signals like address buses, data buses, memory interfaces, etc.
    """
    if not file_path or not os.path.exists(file_path) or not os.path.exists(instantiated_in_file):
        return {'cpu_signal_score': 0, 'signals_found': []}
    
    try:
        with open(instantiated_in_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return {'cpu_signal_score': 0, 'signals_found': []}
    
    # CPU core signal patterns (things connected to CPU cores)
    cpu_signal_patterns = [
        # Address/Memory bus signals
        r'\b(addr|address|mem_addr|i_addr|d_addr)\b',
        r'\b(data|mem_data|i_data|d_data|mem_rdata|mem_wdata|rdata|wdata)\b',
        r'\b(mem_req|mem_gnt|mem_rvalid|mem_we|mem_be|we|be)\b',
        r'\b(instr|instruction|i_req|i_gnt|i_rvalid)\b',
        
        # Cache signals
        r'\b(icache|dcache|cache_req|cache_resp)\b',
        
        # Control signals
        r'\b(clk|clock|rst|reset|rstn)\b',
        r'\b(irq|interrupt|exception)\b',
        r'\b(halt|stall|flush|valid|ready)\b',
        
        # RISC-V specific
        r'\b(hart|hartid|mhartid)\b',
        r'\b(retire|commit|trap)\b',
        
        # Bus interfaces
        r'\b(axi|ahb|apb|wb|wishbone)\b',
        r'\b(avalon|tilelink)\b'
    ]
    
    # Look for instantiation of the specific module and analyze its connections
    # Pattern: module_name instance_name ( .port(signal), ... );
    module_instantiation_pattern = rf'\b{re.escape(module_name)}\s+(?:#\s*\([^)]*\))?\s*(\w+)\s*\((.*?)\);'
    
    cpu_signal_score = 0
    signals_found = []
    
    for match in re.finditer(module_instantiation_pattern, content, re.DOTALL | re.IGNORECASE):
        instance_name = match.group(1)
        port_connections = match.group(2)
        
        # Analyze the port connections
        for pattern in cpu_signal_patterns:
            signal_matches = re.findall(pattern, port_connections, re.IGNORECASE)
            if signal_matches:
                cpu_signal_score += len(signal_matches)
                signals_found.extend(signal_matches)
    
    # Bonus points for instance names that suggest CPU core
    instance_pattern = rf'\b{re.escape(module_name)}\s+(?:#\s*\([^)]*\))?\s*(\w+)\s*\('
    for match in re.finditer(instance_pattern, content, re.IGNORECASE):
        instance_name = match.group(1).lower()
        if any(term in instance_name for term in ['cpu', 'core', 'proc', 'hart', 'riscv']):
            cpu_signal_score += 20  # Higher bonus for CPU-like instance names
            signals_found.append(f"instance_name:{instance_name}")
        elif instance_name.startswith('core'):  # core0, core1, etc.
            cpu_signal_score += 25  # Even higher for numbered cores
            signals_found.append(f"instance_name:{instance_name}")
    
    return {
        'cpu_signal_score': cpu_signal_score,
        'signals_found': list(set(signals_found))  # Remove duplicates
    }


def _find_cpu_core_in_soc(top_module: str, module_graph: dict, modules: list) -> str:
    """
    If the top module is a SoC, try to find the actual CPU core it instantiates.
    Returns the CPU core module name, or the original top_module if not found.
    """
    print_green(f"[CORE_SEARCH] Starting SoC analysis for top_module: {top_module}")
    
    if not top_module or not modules:
        print_yellow(f"[CORE_SEARCH] Early return: top_module={top_module}, modules_count={len(modules) if modules else 0}")
        return top_module
    
    # Create module name to file path mapping
    module_to_file = {}
    for module_name, file_path in modules:
        module_to_file[module_name] = file_path
    
    print_green(f"[CORE_SEARCH] Created module mapping with {len(module_to_file)} entries")
    
    # Get the file path for the top module
    top_file_path = module_to_file.get(top_module)
    if not top_file_path:
        print_yellow(f"[CORE_SEARCH] No file found for top_module: {top_module}")
        return top_module
    
    print_green(f"[CORE_SEARCH] Found file for {top_module}: {top_file_path}")
    
    # Analyze what the top module instantiates
    patterns = _analyze_instantiation_patterns(top_module, top_file_path)
    if not patterns:
        print_yellow(f"[CORE_SEARCH] No instantiation patterns found for {top_module}")
        return top_module
    
    print_green(f"[CORE_SEARCH] Instantiation patterns: {patterns}")
    
    # Check if this looks like a SoC (has peripherals)
    soc_ratio = patterns.get('soc_ratio', 0)
    total_instances = patterns.get('total_instances', 0)
    instantiated_modules = patterns.get('instantiated_modules', [])
    
    # If SoC ratio is significant OR has many instances, look for CPU core candidates among instantiated modules
    if soc_ratio > 0.2:  # Has significant peripheral instantiations (increased threshold)
        print_green(f"[CORE_SEARCH] {top_module} appears to be a SoC (soc_ratio={soc_ratio:.2f}, total_instances={total_instances}), searching for CPU core...")
        
        # Look for CPU core candidates among instantiated modules
        cpu_core_candidates = []
        
        for inst_module in instantiated_modules:
            # Skip obvious non-CPU modules
            if any(skip in inst_module.lower() for skip in ['ram', 'rom', 'timer', 'uart', 'gpio', 'spi', 'i2c', 'vga', 'dma', 'bus', 'matrix', 'interface', 'sync', 'interconnect']):
                continue
                
            # Analyze this potential CPU core - do case-insensitive module lookup
            inst_file_path = None
            proper_module_name = None
            for module_name, file_path in module_to_file.items():
                if module_name.lower() == inst_module.lower():
                    inst_file_path = file_path
                    proper_module_name = module_name  # Use the proper-cased module name
                    break
            
            if inst_file_path:
                # Analyze the signals used when instantiating this module
                signal_analysis = _analyze_cpu_signals(proper_module_name, inst_file_path, top_file_path)
                
                inst_patterns = _analyze_instantiation_patterns(proper_module_name, inst_file_path)
                if inst_patterns:
                    inst_cpu_ratio = inst_patterns.get('cpu_ratio', 0)
                    inst_soc_ratio = inst_patterns.get('soc_ratio', 0)
                    inst_total = inst_patterns.get('total_instances', 0)
                    
                    # Score this module as a CPU core candidate
                    cpu_score = 0
                    
                    # Prefer modules with CPU-like keywords in name
                    name_lower = proper_module_name.lower()
                    if any(cpu_term in name_lower for cpu_term in ['cpu', 'core', 'risc', 'processor', 'hart']):
                        cpu_score += 10
                    
                    # Special bonus for repo-specific core names (like 'aukv' for AUK-V)
                    if top_module:
                        top_parts = [part.lower() for part in top_module.replace('_', ' ').split() if len(part) > 2]
                        for part in top_parts:
                            if part in name_lower and part not in ['soc', 'system', 'top', 'eggs']:
                                cpu_score += 15  # Higher bonus for repo-specific names
                    
                    # Signal analysis score - this is the key addition!
                    signal_score = signal_analysis['cpu_signal_score']
                    cpu_score += signal_score
                    
                    # Prefer modules with CPU-like internal structure
                    if inst_cpu_ratio > inst_soc_ratio:
                        cpu_score += 5
                    if inst_cpu_ratio > 0.3:
                        cpu_score += 3
                    
                    # Prefer modules with reasonable complexity (not too simple, not too complex)
                    if 5 <= inst_total <= 50:
                        cpu_score += 2
                    
                    # Only consider if it has some positive indicators
                    if cpu_score > 0:
                        cpu_core_candidates.append((proper_module_name, cpu_score, inst_cpu_ratio, inst_total, signal_analysis))
                        print_green(f"[CORE_SEARCH] Found CPU core candidate: {proper_module_name}")
                        print_green(f"[CORE_SEARCH]   Total score={cpu_score} (signal_score={signal_score}, cpu_ratio={inst_cpu_ratio:.2f}, instances={inst_total})")
                        print_green(f"[CORE_SEARCH]   CPU signals found: {signal_analysis['signals_found']}")
        
        # Select the best CPU core candidate
        if cpu_core_candidates:
            # Sort by score descending, then by CPU ratio descending
            cpu_core_candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
            selected_core = cpu_core_candidates[0][0]
            print_green(f"[CORE_SEARCH] Selected CPU core: {selected_core}")
            return selected_core
        else:
            print_yellow(f"[CORE_SEARCH] No suitable CPU core found in {top_module}, keeping original top module")
    
    return top_module


def rank_top_candidates(module_graph, module_graph_inverse, repo_name=None, modules=None):
    """
    Rank module candidates to identify the best top module.
    Analyzes both module connectivity and instantiation patterns to distinguish CPU cores from SoC tops.
    """
    children_of = _ensure_mapping(module_graph_inverse)
    parents_of = _ensure_mapping(module_graph)

    nodes = set(children_of.keys()) | set(parents_of.keys())
    for n in nodes:
        children_of.setdefault(n, [])
        parents_of.setdefault(n, [])

    # Filter out Verilog keywords and invalid module names
    valid_modules = []
    verilog_keywords = {"if", "else", "always", "initial", "begin", "end", "case", "default", "for", "while", "assign"}
    
    print_green(f"[DEBUG] All found modules: {sorted(nodes)}")
    
    for module in nodes:
        if (module not in verilog_keywords and 
            len(module) > 1 and 
            (module.replace('_', '').isalnum())):
            valid_modules.append(module)
    
    print_green(f"[DEBUG] Valid modules after filtering: {sorted(valid_modules)}")
    
    # Find candidates: modules with few parents are preferred
    zero_parent_modules = [m for m in valid_modules if not parents_of.get(m, [])]
    low_parent_modules = [m for m in valid_modules if len(parents_of.get(m, [])) <= 2]
    
    # Include repo name matches even if they have many parents
    repo_name_matches = []
    cpu_core_matches = []
    
    # Create module name to file path mapping for instantiation analysis
    module_to_file = {}
    if modules:
        for module_name, file_path in modules:
            module_to_file[module_name] = file_path
    
    if repo_name and len(repo_name) > 2:
        repo_lower = repo_name.lower()
        for module in valid_modules:
            module_lower = module.lower()
            if (repo_lower == module_lower or 
                repo_lower in module_lower or 
                module_lower in repo_lower):
                repo_name_matches.append(module)
            
            # Enhanced CPU core detection using instantiation patterns
            if (any(pattern in module_lower for pattern in [repo_lower, 'cpu', 'core', 'risc', 'processor']) and 
                module not in zero_parent_modules and module not in low_parent_modules and
                not any(bad_pattern in module_lower for bad_pattern in 
                       ['div', 'mul', 'alu', 'fpu', 'cache', 'mem', 'bus', 'ctrl', 'reg', 'decode', 'fetch', 'exec', 'forward', 'hazard', 'pred',
                        'sm3', 'sha', 'aes', 'des', 'rsa', 'ecc', 'crypto', 'hash', 'cipher', 'encrypt', 'decrypt', 'uart', 'spi', 'i2c', 'gpio',
                        'timer', 'interrupt', 'dma', 'pll', 'clk', 'pwm', 'aon', 'hclk', 'oitf', 'wrapper', 'regs']) and
                not any(module_lower.startswith(prefix) for prefix in ['sirv_', 'apb_', 'axi_', 'ahb_', 'wb_', 'avalon_'])):  # Exclude peripheral prefix modules
                
                # Check instantiation patterns if file path is available
                is_cpu_core = False
                file_path = module_to_file.get(module)
                if file_path:
                    patterns = _analyze_instantiation_patterns(module, file_path)
                    if patterns:
                        cpu_ratio = patterns.get('cpu_ratio', 0)
                        soc_ratio = patterns.get('soc_ratio', 0)
                        total_instances = patterns.get('total_instances', 0)
                        
                        if total_instances > 0 and (cpu_ratio > soc_ratio * 1.5 or cpu_ratio > 0.3):
                            is_cpu_core = True
                            print_green(f"[INSTANTIATION] {module}: CPU core (cpu_ratio={cpu_ratio:.2f}, soc_ratio={soc_ratio:.2f}, instances={total_instances})")
                        elif total_instances == 0:
                            is_cpu_core = True
                            print_green(f"[INSTANTIATION] {module}: CPU core (fallback - no instantiations found)")
                
                if is_cpu_core and module not in repo_name_matches:
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
        
        # Specific CPU core boost - give highest priority to actual core modules
        if "core" in name_lower and repo_lower:
            # Strong boost for exact core modules like "repo_core"
            if name_lower == f"{repo_lower}_core" or name_lower == f"core_{repo_lower}":
                score += 25000
                print_green(f"[SCORE] {c}: +25000 (exact repo core module)")
            # Generic pattern: any module ending with "_core" that looks like a main core module
            elif name_lower.endswith("_core"):
                # Check if it's a likely CPU core (not a functional unit core)
                if not any(unit in name_lower for unit in ["div", "mul", "alu", "fpu", "mem", "cache", "bus", "ctrl", "reg", "decode", "fetch", "exec", "forward", "hazard", "pred"]):
                    score += 20000
                    print_green(f"[SCORE] {c}: +20000 (generic core module)")
            # Medium boost for modules containing both repo name and core
            elif repo_lower in name_lower and "core" in name_lower:
                if not any(unit in name_lower for unit in ["div", "mul", "alu", "fpu", "mem", "cache", "bus", "ctrl", "reg", "decode", "fetch", "exec", "forward", "hazard", "pred"]):
                    score += 15000
                    print_green(f"[SCORE] {c}: +15000 (repo core module)")
        
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
        if any(pattern in name_lower for pattern in ["_tb", "tb_", "test", "bench", "compliance", "verify", "checker", "monitor", "fpv", "bind", "assert"]):
            score -= 10000
        
        peripheral_terms = ["uart", "spi", "i2c", "gpio", "timer", "dma", "plic", "clint", "baud", "fifo", "ram", "rom", "cache", "pwm", "aon", "hclk", "oitf", "wrapper", "regs"]
        if any(term in name_lower for term in peripheral_terms):
            score -= 3000
        
        # Generic penalty for likely peripheral module prefixes
        peripheral_prefixes = ["sirv_", "apb_", "axi_", "ahb_", "wb_", "avalon_"]
        if any(name_lower.startswith(prefix) for prefix in peripheral_prefixes):
            score -= 4000
            print_green(f"[SCORE] {c}: -4000 (peripheral prefix module)")
        
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
        repo_name, url, tb_files, files, include_dirs, top_module, language_version, is_simulable=False
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

        # Reorder files to put package definitions first
        ordered_files = reorder_files_by_dependencies(repo_root, files)
        file_list = " ".join(shlex.quote(f) for f in ordered_files)

        # Check if we're dealing with VHDL files by examining file extensions
        is_vhdl = any(f.endswith(('.vhdl', '.vhd')) for f in files) if files else False
        
        if is_vhdl:
            ghdl_flags = " ".join(shlex.quote(f) for f in ghdl_extra_flags)
            # Add -frelaxed flag by default to handle some GHDL warnings as warnings instead of errors
            relaxed_flag = "-frelaxed" if "-frelaxed" not in ghdl_flags else ""
            
            # Ensure proper spacing between flags
            include_part = f"{include_flags_ghdl} " if include_flags_ghdl else ""
            relaxed_part = f"{relaxed_flag} " if relaxed_flag else ""
            ghdl_part = f"{ghdl_flags} " if ghdl_flags else ""
            
            # Add --std flag explicitly to both analyze and elaborate steps
            std_flag = f"--std={language_version.lstrip('0')}"  # Remove leading zeros: "08" -> "8"
            if language_version == "08":
                std_flag = "--std=08"
            
            cmd = (f"ghdl -a {std_flag} {include_part}{relaxed_part}{ghdl_part}{file_list} && "
                   f"ghdl -e {std_flag} {shlex.quote(top_module)}")
            print_green(f"[SIM] Running GHDL syntax check: {cmd}")
            return _run_shell_cmd(cmd, repo_root, timeout, config_path)
        else:
            extra_flags = " ".join(shlex.quote(f) for f in verilator_extra_flags)
            top_opt = f"--top-module {shlex.quote(top_module)}" if top_module else ""
            
            # Add language standard flags based on version
            std_flags = ""
            if language_version.startswith('1800-'):  # SystemVerilog versions
                if language_version in ['1800-2017']:
                    std_flags = "--sv +1800-2017"
                elif language_version in ['1800-2012', '1800-2009', '1800-2005']:
                    std_flags = "--sv"
                else:
                    std_flags = "--sv"
            elif language_version.startswith('1364-'):  # Verilog versions
                std_flags = f"+{language_version}ext+"
            else:
                # Fallback: detect SystemVerilog by file extensions
                if any(f.endswith(('.sv', '.svh')) for f in files):
                    std_flags = "--sv"
                else:
                    std_flags = "+1364-2005ext+"
            
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
        r"%error: unit '([^']+)' not found",
        r"error: unit \"([^\"]+)\" not found in library",
        r"error: unit '([^']+)' not found in library",
    ]

    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            group = m.group(1).strip()
            missing.add(os.path.basename(group))
    
    for m in re.finditer(r'["\']([^"\']+\.(svh|vh|vhdr|v|sv|svh|vhd|vhdl))["\'] not found', log_text, flags=re.IGNORECASE):
        missing.add(os.path.basename(m.group(1)))
    return list(missing)


def parse_missing_packages_from_log(log_text: str) -> list:
    """
    Parse simulator output looking for missing package/import errors.
    """
    missing_packages = set()
    patterns = [
        r"Package/class '([^']+)' not found",
        r"Importing from missing package '([^']+)'",
        r"Package '([^']+)' not found",
        r"Unknown package '([^']+)'",
        r"Cannot find package '([^']+)'",
        r"%Error.*Package.*'([^']+)'.*not found",
        r"package.*'([^']+)'.*not declared",
        r"'([^']+)' is not a valid package",
    ]
    
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            package_name = m.group(1).strip()
            # Keep the full package name as reported, only clean up namespace operators
            clean_name = package_name.replace('::', '').strip()
            if clean_name:
                missing_packages.add(clean_name)
    
    return list(missing_packages)


def parse_ghdl_missing_entities_from_log(log_text: str) -> list:
    """
    Parse GHDL output looking for missing entity references.
    
    Returns entities that are truly missing, not compilation order issues.
    GHDL gives errors like: 
    - unit "entity_name" not found in library "work"
    - entity "entity_name" not found
    
    Note: "obsoleted by package" errors are logged but not returned as missing entities
    since they indicate compilation order issues, not missing files.
    """
    missing_entities = set()
    # Only patterns for truly missing entities - not compilation order issues
    patterns = [
        r'unit "([^"]+)" not found in library "work"',
        r"unit '([^']+)' not found in library 'work'",
        r'entity "([^"]+)" not found',
        r"entity '([^']+)' not found",
        r'cannot find entity "([^"]+)"',
        r"cannot find entity '([^']+)'",
        r'undefined entity "([^"]+)"',
        r"undefined entity '([^']+)'",
        # Note: "obsoleted by package" errors removed - these are compilation order issues, not missing entities
    ]
    
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            entity_name = m.group(1).strip()
            if entity_name:
                missing_entities.add(entity_name)
    
    # Log "obsoleted by package" errors for debugging but don't treat as missing entities
    obsoleted_patterns = [
        r'entity "([^"]+)" is obsoleted by package "([^"]+)"',
        r"entity '([^']+)' is obsoleted by package '([^']+)'",
        r':error:\s*entity\s*"([^"]+)"\s*is\s*obsoleted\s*by\s*package\s*"([^"]+)"',
        r":error:\s*entity\s*'([^']+)'\s*is\s*obsoleted\s*by\s*package\s*'([^']+)'",
    ]
    
    for pat in obsoleted_patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            if len(m.groups()) >= 2:
                entity_name = m.group(1).strip()
                package_name = m.group(2).strip()
                print(f"[MIN-GHDL-DEBUG] Entity '{entity_name}' obsoleted by package '{package_name}' - treating as compilation order issue, not missing entity")
    
    return list(missing_entities)


def parse_syntax_errors_from_log(log_text: str) -> list:
    """
    Parse simulator output looking for syntax errors and extract the files that contain them.
    Returns a list of file paths that have syntax errors.
    """
    error_files = set()
    
    # Pattern to match Verilator error messages with file paths
    # Examples:
    # %Error: rtl/external_peripheral/DRAM_Controller/fpga/opensourceSDRLabKintex7/main.sv:105:40: Too many digits for 1 bit number: '1'b10100101'
    # %Error: file.sv:123:45: Syntax error: unexpected token  
    # %Error: rtl/verilog/core/memory/riscv_dmem_ctrl.sv:67:44: syntax error, unexpected IDENTIFIER, expecting ','
    error_patterns = [
        r"%Error:\s+([^:]+\.s?v[h]?):\d+:\d+:.*(?:syntax error|parse error|Too many digits|unexpected)",
        r"%Error:\s+([^:]+\.s?v[h]?):\d+.*(?:syntax|parse|unexpected)",
        r"Error.*?:\s+([^:]+\.s?v[h]?):\d+.*(?:syntax|parse|unexpected)",
        r"Syntax error.*?in\s+([^:]+\.s?v[h]?)",
        r"Parse error.*?in\s+([^:]+\.s?v[h]?)",
    ]
    
    for pattern in error_patterns:
        for match in re.finditer(pattern, log_text, flags=re.IGNORECASE | re.MULTILINE):
            file_path = match.group(1).strip()
            if file_path and (file_path.endswith('.sv') or file_path.endswith('.v') or file_path.endswith('.svh') or file_path.endswith('.vh')):
                error_files.add(file_path)
    
    return list(error_files)


def find_files_with_syntax_errors(repo_root: str, file_list: list) -> list:
    """
    Identify files that contain syntax errors by running a quick Verilator syntax check.
    Returns a list of files that should be excluded due to syntax errors.
    """
    syntax_error_files = []
    
    # Test each file individually to isolate syntax errors
    for file_path in file_list:
        full_path = os.path.join(repo_root, file_path)
        
        # Skip problematic files entirely
        if should_exclude_file(full_path, repo_root):
            continue
            
        if not os.path.exists(full_path):
            continue
            
        if not (file_path.endswith('.sv') or file_path.endswith('.v')):
            continue
        
        # Run a quick syntax check on individual file
        cmd = ['verilator', '--lint-only', '--sv', '-Wno-lint', '-Wno-fatal', '-Wno-style', full_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0 and result.stderr:
                # Check if this specific file has syntax errors
                syntax_files = parse_syntax_errors_from_log(result.stderr)
                if syntax_files:
                    # Check if our file is mentioned in the syntax errors
                    for error_file in syntax_files:
                        if error_file == file_path or error_file.endswith(file_path.split('/')[-1]):
                            syntax_error_files.append(file_path)
                            print_yellow(f"[SYNTAX_ERROR] Found syntax error in {file_path}")
                            break
        except subprocess.TimeoutExpired:
            print_yellow(f"[SYNTAX_ERROR] Timeout checking {file_path}")
            continue
        except Exception as e:
            print_yellow(f"[SYNTAX_ERROR] Error checking {file_path}: {e}")
            continue
    
    return syntax_error_files


def is_vhdl_project(files: list) -> bool:
    """
    Check if this is a VHDL project by examining file extensions.
    """
    vhdl_extensions = ['.vhd', '.vhdl']
    vhdl_count = sum(1 for f in files if any(f.endswith(ext) for ext in vhdl_extensions))
    total_count = len(files)
    
    # Consider it VHDL if more than 50% of files are VHDL
    return vhdl_count > total_count * 0.5 if total_count > 0 else False


def references_missing_entity(file_path: str, entity_name: str, repo_root: str) -> bool:
    """
    Check if a VHDL file references a missing entity or has GHDL-specific conflicts.
    Returns True if the file should be excluded due to referencing missing entities or conflicts.
    """
    full_path = os.path.join(repo_root, file_path)
    if not os.path.exists(full_path):
        return False
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Check for entity instantiation patterns that reference the missing entity
        patterns = [
            rf'\bentity\s+work\.{re.escape(entity_name)}\b',  # entity work.entity_name
            rf':\s*entity\s+work\.{re.escape(entity_name)}\b',  # label: entity work.entity_name
            rf'\bentity\s+{re.escape(entity_name)}\b',  # entity entity_name (without work prefix)
            rf':\s*entity\s+{re.escape(entity_name)}\b',  # label: entity entity_name
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        # Check if this file defines the problematic entity (GHDL obsoleted entity issue)
        # If a file defines an entity that GHDL says is "obsoleted", it might be the problem file itself
        entity_def_pattern = rf'^\s*entity\s+{re.escape(entity_name)}\s+is'
        if re.search(entity_def_pattern, content, re.MULTILINE | re.IGNORECASE):
            return True
                
        return False
        
    except Exception as e:
        print_yellow(f"[MIN-GHDL] Error reading {file_path}: {e}")
        return False


def check_package_exists_in_repo(repo_root: str, package_name: str) -> bool:
    """
    Check if a package definition exists anywhere in the repository.
    Only returns True for exact matches to avoid false positives.
    """
    # Search for exact package definitions only
    package_patterns = [
        rf'\bpackage\s+{re.escape(package_name)}_pkg\s*;',
        rf'\bpackage\s+{re.escape(package_name)}\s*;',
        rf'^\s*package\s+{re.escape(package_name)}_pkg\b',
        rf'^\s*package\s+{re.escape(package_name)}\b',
    ]
    
    for root, _, files in os.walk(repo_root):
        for file in files:
            if not file.endswith(('.sv', '.svh', '.v', '.vh', '.vhd', '.vhdl')):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in package_patterns:
                    if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                        print_green(f"[PACKAGE_CHECK] Found package '{package_name}' in {file_path}")
                        return True
                        
            except Exception:
                continue
    
    return False


def find_package_files(repo_root: str, files: list) -> dict:
    """
    Find files that contain package definitions and entity definitions.
    Map package/entity names to file paths.
    Returns dict: {package_or_entity_name: file_path}
    """
    package_files = {}
    
    print_green("[PKG_ORDER] Scanning for package and entity definitions...")
    
    for file_path in files:
        full_path = file_path
        if not os.path.isabs(file_path):
            full_path = os.path.join(repo_root, file_path)
        
        if not os.path.exists(full_path):
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Search for package definitions
            package_patterns = [
                r'^\s*package\s+(\w+)\s*;',
                r'\bpackage\s+(\w+)\s*;',
            ]
            
            for pattern in package_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    package_name = match.group(1)
                    package_files[package_name] = file_path
            
            # Search for entity definitions
            entity_patterns = [
                r'^\s*entity\s+(\w+)\s+is',
                r'\bentity\s+(\w+)\s+is',
            ]
            
            for pattern in entity_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    entity_name = match.group(1)
                    package_files[entity_name] = file_path
                    
        except Exception as e:
            print_yellow(f"[PKG_ORDER] Warning: Could not analyze file {file_path}: {e}")
            continue
    
    return package_files


def find_import_dependencies(repo_root: str, files: list) -> dict:
    """
    Find which files import which packages and instantiate entities.
    Returns dict: {file_path: [list_of_imported_packages_and_entities]}
    """
    file_imports = {}
    
    print_green("[PKG_ORDER] Scanning for import dependencies...")
    
    for file_path in files:
        full_path = file_path
        if not os.path.isabs(file_path):
            full_path = os.path.join(repo_root, file_path)
        
        if not os.path.exists(full_path):
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            imports = []
            
            # Search for import statements
            import_patterns = [
                # SystemVerilog import patterns
                r'\bimport\s+(\w+)(?:_pkg)?\s*::\s*\*\s*;',
                r'\bimport\s+(\w+)(?:_pkg)?\s*::\s*\w+',
                r'\bfrom\s+(\w+)(?:_pkg)?\s+import',
                # VHDL use patterns - more comprehensive
                r'\buse\s+work\.(\w+)\.all\s*;',  # use work.package_name.all;
                r'\buse\s+work\.(\w+)\.\w+\s*;',  # use work.package_name.something;
                r'\buse\s+(\w+)(?:_pkg)?\.',       # fallback for other patterns
            ]
            
            for pattern in import_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    package_name = match.group(1)
                    # Clean up package name
                    clean_name = package_name.replace('_pkg', '').strip()
                    if clean_name and clean_name not in imports:
                        imports.append(clean_name)
            
            # Search for VHDL entity instantiations
            entity_patterns = [
                # entity work.entity_name port map
                r'\bentity\s+work\.(\w+)\s+port\s+map',
                # entity work.entity_name generic map
                r'\bentity\s+work\.(\w+)\s+generic\s+map',
                # entity work.entity_name (without explicit port/generic map)
                r'\bentity\s+work\.(\w+)(?:\s|$|\()',
                # component instantiation: entity_name : entity work.entity_name
                r':\s*entity\s+work\.(\w+)',
            ]
            
            for pattern in entity_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group(1).strip()
                    if entity_name and entity_name not in imports:
                        imports.append(entity_name)
            
            if imports:
                file_imports[file_path] = imports
                    
        except Exception as e:
            print_yellow(f"[PKG_ORDER] Warning: Could not analyze file {file_path}: {e}")
            continue
    
    return file_imports


def reorder_files_by_dependencies(repo_root: str, files: list) -> list:
    """
    Reorder files so that package definitions come before files that import them.
    """
    print_green("[PKG_ORDER] Reordering files by package dependencies...")
    
    # Find package definitions and imports
    package_files = find_package_files(repo_root, files)
    file_imports = find_import_dependencies(repo_root, files)
    
    if not package_files and not file_imports:
        print_green("[PKG_ORDER] No packages or imports found, keeping original order")
        return files
    
    # Separate files into categories
    pkg_definition_files = set(package_files.values())
    importing_files = set(file_imports.keys())
    other_files = set(files) - pkg_definition_files - importing_files
    
    print_green(f"[PKG_ORDER] Found {len(pkg_definition_files)} package files, {len(importing_files)} importing files, {len(other_files)} other files")
    
    # Create dependency-ordered list
    ordered_files = []
    
    # 1. First, add package definition files with dependency resolution
    remaining_pkg_files = list(pkg_definition_files)
    max_pkg_iterations = len(remaining_pkg_files) + 5
    pkg_iteration = 0
    
    while remaining_pkg_files and pkg_iteration < max_pkg_iterations:
        pkg_iteration += 1
        made_progress = False
        
        for pkg_file in remaining_pkg_files[:]:  # Copy to avoid modification during iteration
            imports = file_imports.get(pkg_file, [])
            
            # Check if all package dependencies are satisfied
            dependencies_satisfied = True
            for imported_pkg in imports:
                # Check if the imported package file is already in ordered_files
                imported_pkg_file = package_files.get(imported_pkg) or package_files.get(f"{imported_pkg}_pkg")
                if imported_pkg_file and imported_pkg_file not in ordered_files and imported_pkg_file in pkg_definition_files:
                    dependencies_satisfied = False
                    break
            
            if dependencies_satisfied:
                ordered_files.append(pkg_file)
                remaining_pkg_files.remove(pkg_file)
                made_progress = True
                print_green(f"[PKG_ORDER] Added package file: {pkg_file}")
        
        if not made_progress:
            # Add remaining package files anyway to avoid infinite loop
            for pkg_file in remaining_pkg_files:
                ordered_files.append(pkg_file)
                print_yellow(f"[PKG_ORDER] Added package file with unresolved dependencies: {pkg_file}")
            break
    
    # 2. Then add other non-importing files
    for other_file in sorted(other_files):
        if other_file not in ordered_files:
            ordered_files.append(other_file)
    
    # 3. Finally add importing files (with dependency resolution)
    # Filter out files that are already added as package files
    remaining_importing_files = [f for f in importing_files if f not in ordered_files]
    max_iterations = len(remaining_importing_files) + 5
    iteration = 0
    
    while remaining_importing_files and iteration < max_iterations:
        iteration += 1
        made_progress = False
        
        for file_path in remaining_importing_files[:]:  # Copy to avoid modification during iteration
            imports = file_imports.get(file_path, [])
            
            # Check if all dependencies are satisfied
            dependencies_satisfied = True
            for imported_pkg in imports:
                # Check if the package file is already in ordered_files
                pkg_file = package_files.get(imported_pkg) or package_files.get(f"{imported_pkg}_pkg")
                if pkg_file and pkg_file not in ordered_files:
                    dependencies_satisfied = False
                    break
            
            if dependencies_satisfied:
                ordered_files.append(file_path)
                remaining_importing_files.remove(file_path)
                made_progress = True
                print_green(f"[PKG_ORDER] Added importing file: {file_path}")
        
        if not made_progress:
            # Add remaining files anyway to avoid infinite loop
            for file_path in remaining_importing_files:
                ordered_files.append(file_path)
                print_yellow(f"[PKG_ORDER] Added file with unresolved dependencies: {file_path}")
            break
    
    # Only add missing files if they weren't intentionally excluded
    # Check if missing files have broken imports that would make them problematic
    if len(ordered_files) != len(files):
        missing_files = [f for f in files if f not in ordered_files]
        print_yellow(f"[PKG_ORDER] Warning: File count mismatch. Original: {len(files)}, Ordered: {len(ordered_files)}")
        print_yellow(f"[PKG_ORDER] Missing files: {missing_files}")
        
        # Check if missing files have broken imports before re-adding them
        for f in missing_files:
            # Quick check: if file imports packages that don't exist, don't re-add it
            file_path = os.path.join(repo_root, f)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        # Look for import statements that might be problematic
                        import_matches = re.findall(r'import\s+(\w+)(?:::.*)?;', content, re.IGNORECASE)
                        has_potentially_broken_import = any(
                            pkg_name.endswith('_pkg') and pkg_name not in package_files 
                            for pkg_name in import_matches
                        )
                        
                        if has_potentially_broken_import:
                            print_yellow(f"[PKG_ORDER] Skipping re-addition of {f} (has potentially broken imports)")
                            continue
                except:
                    pass
            
            # If we get here, the file seems safe to re-add
            ordered_files.append(f)
            print_yellow(f"[PKG_ORDER] Added missing file: {f}")
    
    print_green(f"[PKG_ORDER] Reordering complete. Package files moved to front.")
    return ordered_files


def find_files_with_broken_imports(repo_root: str, files: list, missing_packages: list) -> list:
    """
    Find files that import missing packages that cannot be resolved.
    Returns list of files that should be excluded from simulation.
    """
    broken_files = []
    
    if not missing_packages:
        return broken_files
    
    print_green(f"[BROKEN_IMPORTS] Searching for files with missing packages: {missing_packages}")
    
    # First, check which packages actually don't exist in the repo
    truly_missing_packages = []
    for package in missing_packages:
        if not check_package_exists_in_repo(repo_root, package):
            truly_missing_packages.append(package)
            print_yellow(f"[BROKEN_IMPORTS] Package '{package}' not found in repository")
        else:
            print_green(f"[BROKEN_IMPORTS] Package '{package}' exists in repository, not excluding files")
    
    if not truly_missing_packages:
        print_green("[BROKEN_IMPORTS] All packages exist in repository, no files to exclude")
        return broken_files
    
    for file_path in files:
        full_path = file_path
        if not os.path.isabs(file_path):
            full_path = os.path.join(repo_root, file_path)
        
        # Skip problematic files entirely
        if should_exclude_file(full_path, repo_root):
            continue
            
        if not os.path.exists(full_path):
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check for import statements of truly missing packages
            for package in truly_missing_packages:
                # Match various import patterns
                import_patterns = [
                    rf'\bimport\s+{re.escape(package)}_pkg\s*::\s*\*\s*;',
                    rf'\bimport\s+{re.escape(package)}\s*::\s*\*\s*;',
                    rf'\bfrom\s+{re.escape(package)}_pkg\s+import',
                    rf'\bfrom\s+{re.escape(package)}\s+import',
                    rf'\buse\s+{re.escape(package)}_pkg\.',
                    rf'\buse\s+{re.escape(package)}\.',
                    rf'`include\s+["\'][^"\']*{re.escape(package)}[^"\']*["\']',
                ]
                
                for pattern in import_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        if file_path not in broken_files:
                            broken_files.append(file_path)
                            print_yellow(f"[BROKEN_IMPORTS] Found broken import in {file_path}: {package}")
                        break
                        
        except Exception as e:
            print_yellow(f"[BROKEN_IMPORTS] Warning: Could not analyze file {file_path}: {e}")
            continue
    
    return broken_files


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
    maximize_attempts: int = 6,
    verilator_extra_flags: list | None = None,
    ghdl_extra_flags: list | None = None,
) -> tuple:
    """
    Interactive simulation and file minimization.
    """
    print_yellow(f"[DEBUG] Files list: {candidate_files}") 
    files = list(candidate_files)
    inclu = set(include_dirs)
    last_log = ""
    
    # Build module-to-file mapping from modules list
    module_to_file = {}
    for module_name, file_path in modules:
        module_to_file[module_name] = file_path

    # Phase A: include fixing
    print_green(f"[DEBUG] Bootstrapping with repo_name='{repo_name}'")
    bootstrap_candidates, cpu_core_candidates = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name, modules=modules)
    print_green(f"[BOOT] Bootstrap candidates: {bootstrap_candidates[:5]}")
    
    heuristic_top = None
    for candidate in bootstrap_candidates:
        words_to_check = ["soc", "core", "cpu"]
        if repo_name:
            words_to_check.append(repo_name.lower())
        print_green(f"[DEBUG] Checking candidate '{candidate}' against words {words_to_check}")
        candidate_lower = candidate.lower()
        
        # Skip testbench and verification modules
        if any(tb_pattern in candidate_lower for tb_pattern in 
               ['tb', 'test', 'bench', 'compliance', 'verify', 'checker', 'monitor', 'fpv', 'bind', 'assert']):
            print_green(f"[DEBUG] Skipping testbench/verification module '{candidate}'")
            continue
        
        if (any(word in candidate_lower for word in words_to_check) and
            not any(bad_pattern in candidate_lower for bad_pattern in 
                   ['sm3', 'sha', 'aes', 'des', 'rsa', 'ecc', 'crypto', 'hash', 'cipher', 'encrypt', 'decrypt', 
                    'uart', 'spi', 'i2c', 'gpio', 'timer', 'interrupt', 'dma', 'pll', 'clk'])):
            heuristic_top = candidate
            print_green(f"[DEBUG] Selected '{candidate}' as heuristic_top")
            break
    
    if not heuristic_top and bootstrap_candidates:
        heuristic_top = bootstrap_candidates[0]
    
    if not heuristic_top:
        print_red("[ERROR] No suitable top module candidates found")
        return files, inclu, last_log, ""
    
    print_green(f"[BOOT] Using heuristic bootstrap top_module: {heuristic_top}")
    
    # Phase A1: Smart dependency-based file refinement
    print_green(f"[SMART] Performing dependency-based file refinement for top module: {heuristic_top}")
    try:
        # Use smart dependency analysis to refine file list
        extensions_no_dot = ['v', 'sv', 'vhd', 'vhdl']  # remove dots from extensions
        smart_files, smart_extension = find_files_with_extension_smart(
            repo_root, extensions_no_dot, [heuristic_top]
        )
        
        if smart_files and len(smart_files) < len(files):
            original_count = len(files)
            files = smart_files
            print_green(f"[SMART] Refined file list from {original_count} to {len(files)} files using dependency analysis")
            print_yellow(f"[SMART] Smart selection kept {len(files)} essential files for top module '{heuristic_top}'")
        else:
            print_yellow(f"[SMART] Smart analysis didn't reduce file count significantly, using original list")
            
    except Exception as e:
        print_yellow(f"[SMART] Smart dependency analysis failed: {e}")
        print_yellow(f"[SMART] Continuing with original file list")

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
        missing_packages = parse_missing_packages_from_log(out)
        missing_entities = parse_ghdl_missing_entities_from_log(out)
        syntax_error_files_in_log = parse_syntax_errors_from_log(out)
        
        # Initialize exclusion tracking variables
        newly_added = []
        broken_files = []
        entity_files_to_exclude = []
        syntax_files_to_exclude = []
        
        # Handle missing includes first
        if missing:
            newly_added = _add_include_dirs_from_missing_files(repo_root, inclu, missing)
            if newly_added:
                print_green(f"[BOOT] Added include dirs: {newly_added} — retrying")
                continue
            else:
                print_yellow("[BOOT] Could not resolve missing includes")
                print_yellow(f"[BOOT] Ressorting to file exclusion for missing includes: {missing}")
                
        
        # Handle broken imports - first try reordering, then exclude if needed
        if missing_packages:
            # First, try reordering files to fix dependency order
            print_green(f"[BOOT] Missing packages detected: {missing_packages}")
            print_green(f"[BOOT] Attempting to fix by reordering files...")
            original_files = files[:]
            files = reorder_files_by_dependencies(repo_root, files)
            
            # If we reordered files, try again immediately
            if files != original_files:
                print_green(f"[BOOT] Files reordered for dependency resolution — retrying")
                continue
            
            # If reordering didn't help, look for truly broken imports to exclude
            broken_files = find_files_with_broken_imports(repo_root, files, missing_packages)
            if broken_files:
                print_yellow(f"[BOOT] Found {len(broken_files)} files with unresolvable imports")
                original_count = len(files)
                files = [f for f in files if f not in broken_files]
                excluded_count = original_count - len(files)
                print_green(f"[BOOT] Excluded {excluded_count} files with broken imports — retrying")
                continue
        
        # Handle missing GHDL entities - exclude files that reference missing entities
        if missing_entities and is_vhdl_project(files):
            print_yellow(f"[BOOT] Missing GHDL entities detected: {missing_entities}")
            entity_files_to_exclude = []
            for missing_entity in missing_entities:
                for f in files:
                    if references_missing_entity(f, missing_entity, repo_root):
                        entity_files_to_exclude.append(f)
                        print_yellow(f"[BOOT] File '{f}' references missing entity '{missing_entity}' - marking for exclusion")
            
            if entity_files_to_exclude:
                original_count = len(files)
                files = [f for f in files if f not in entity_files_to_exclude]
                excluded_count = original_count - len(files)
                print_green(f"[BOOT] Excluded {excluded_count} files with missing entity references — retrying")
                for excluded in entity_files_to_exclude:
                    print_yellow(f"[MISSING_ENTITY] Excluded file: {excluded}")
                continue
        
        # Handle syntax errors - check for files with syntax errors and exclude them
        if syntax_error_files_in_log:
            print_yellow(f"[BOOT] Syntax errors detected in: {syntax_error_files_in_log}")
            # Find which files in our current file list have syntax errors
            syntax_files_to_exclude = []
            for error_file in syntax_error_files_in_log:
                # Match both exact paths and filename-only matches
                for f in files:
                    if f == error_file or f.endswith(error_file.split('/')[-1]):
                        syntax_files_to_exclude.append(f)
            
            if syntax_files_to_exclude:
                original_count = len(files)
                files = [f for f in files if f not in syntax_files_to_exclude]
                excluded_count = original_count - len(files)
                print_green(f"[BOOT] Excluded {excluded_count} files with syntax errors — retrying")
                for excluded in syntax_files_to_exclude:
                    print_yellow(f"[SYNTAX_EXCLUDE] Excluded file: {excluded}")
                continue
        
        # If no missing includes, packages, entities, or syntax errors, or couldn't resolve them, break
        if not missing and not missing_packages and not missing_entities and not syntax_error_files_in_log:
            print_yellow("[BOOT] No missing includes, packages, entities, or syntax errors detected; stopping include-fix loop")
            break
        elif (missing and not newly_added) and (missing_packages and not broken_files) and (missing_entities and not entity_files_to_exclude) and (syntax_error_files_in_log and not syntax_files_to_exclude):
            print_yellow("[BOOT] Could not resolve missing includes, packages, entities, or syntax errors")
            break

    # Phase B: top selection
    print_green(f"[DEBUG] About to rank candidates with repo_name='{repo_name}'")
    print_green(f"[DEBUG] Available modules in graph: {[module_name for module_name, _ in modules]}")
    candidates, cpu_core_matches = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name, modules=modules)
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
        
        # Third priority: core/CPU modules without "soc" and without peripheral patterns
        if not selected_top:
            for cand in working_candidates:
                cand_lower = cand.lower()
                if (any(tok in cand_lower for tok in ["core", "cpu"]) and 
                    "soc" not in cand_lower and
                    not any(bad_pattern in cand_lower for bad_pattern in 
                           ['sm3', 'sha', 'aes', 'des', 'rsa', 'ecc', 'crypto', 'hash', 'cipher', 'encrypt', 'decrypt', 
                            'uart', 'spi', 'i2c', 'gpio', 'timer', 'interrupt', 'dma', 'pll', 'clk'])):
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

    # CRITICAL CHECK: Ensure the selected top module's file is actually in our file list
    top_module_file = module_to_file.get(selected_top, "")
    if top_module_file not in files:
        print_red(f"[TOP-CAND] ERROR: Selected top module '{selected_top}' file '{top_module_file}' not in file list!")
        
        # First, try to add the missing top module file if it exists in the repository
        if top_module_file and os.path.exists(os.path.join(repo_root, top_module_file)):
            # Normalize the path to be relative to repo_root
            normalized_top_file = os.path.relpath(top_module_file, repo_root) if os.path.isabs(top_module_file) else top_module_file
            print_green(f"[TOP-CAND] FIXING: Adding missing top module file '{normalized_top_file}' to file list")
            files.append(normalized_top_file)
            
            # For VHDL files, dynamically find and include missing dependencies
            if top_module_file.endswith(('.vhd', '.vhdl')):
                missing_deps = _find_missing_dependencies(repo_root, [top_module_file], module_to_file, files)
                for dep_file in missing_deps:
                    if os.path.exists(os.path.join(repo_root, dep_file)):
                        # Also normalize dependency paths
                        normalized_dep_file = os.path.relpath(dep_file, repo_root) if os.path.isabs(dep_file) else dep_file
                        print_green(f"[TOP-CAND] FIXING: Adding missing dependency '{normalized_dep_file}' for top module")
                        files.append(normalized_dep_file)
                        
            print_green(f"[TOP-CAND] Successfully added top module file and dependencies. Total files now: {len(files)}")
        else:
            print_green(f"[TOP-CAND] Available files: {files[:10]}...")  # Show first 10 files for debugging
            print_green(f"[TOP-CAND] Searching for alternative top module from available files...")
        
        # Find alternative top modules that actually have files in our list
        alternative_candidates = []
        for cand in candidates:
            cand_file = module_to_file.get(cand, "")
            if cand_file and cand_file in files:
                alternative_candidates.append(cand)
        
        print_green(f"[TOP-CAND] Found {len(alternative_candidates)} alternative candidates with available files: {alternative_candidates}")
        
        # Test alternatives to find a working one
        final_top = None
        for alt_cand in alternative_candidates:
            print_green(f"[TOP-CAND] Testing alternative: {alt_cand}")
            rc, out, cfg = run_simulation_with_config(
                repo_root,
                repo_name,
                url,
                tb_files,
                files,
                inclu,
                alt_cand,
                language_version,
                timeout=120,
                verilator_extra_flags=verilator_extra_flags,
                ghdl_extra_flags=ghdl_extra_flags,
            )
            if rc == 0:
                final_top = alt_cand
                print_green(f"[TOP-CAND] Found working alternative: {alt_cand}")
                break
        
        if final_top:
            selected_top = final_top
            print_green(f"[TOP-CAND] Successfully switched to alternative top module: {selected_top}")
        else:
            print_red(f"[TOP-CAND] No working alternative found! This will likely fail in simulation.")
            # Keep the original selection but warn user
            print_yellow(f"[TOP-CAND] Continuing with missing top module '{selected_top}' - expect compilation failure")
    else:
        print_green(f"[TOP-CAND] Verified top module '{selected_top}' file '{top_module_file}' is available")

    top_module = selected_top

    # Phase B.5: Check if we found a SoC and try to find the actual CPU core
    original_top = top_module
    cpu_core = _find_cpu_core_in_soc(top_module, module_graph, modules)
    
    if cpu_core != top_module:
        print_green(f"[CORE_SEARCH] Switching from SoC top '{top_module}' to CPU core '{cpu_core}'")
        # Verify the CPU core can compile
        rc, out, cfg = run_simulation_with_config(
            repo_root,
            repo_name,
            url,
            tb_files,
            files,
            inclu,
            cpu_core,
            language_version,
            timeout=240,
            verilator_extra_flags=verilator_extra_flags,
            ghdl_extra_flags=ghdl_extra_flags,
        )
        if rc == 0:
            top_module = cpu_core
            last_log = out
            print_green(f"[CORE_SEARCH] Successfully switched to CPU core: {cpu_core}")
        else:
            print_yellow(f"[CORE_SEARCH] CPU core '{cpu_core}' failed compilation, keeping SoC top '{original_top}'")
            top_module = original_top

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
        
        # Smart protection: Use existing analysis to determine if top module is CPU core vs SoC  
        if is_top_file:
            # Analyze the top module using existing instantiation pattern analysis
            patterns = _analyze_instantiation_patterns(top_module, f)
            cpu_ratio = patterns.get('cpu_ratio', 0)
            soc_ratio = patterns.get('soc_ratio', 0)
            
            # Additional heuristic: check module name for CPU/core indicators
            top_name_lower = top_module.lower()
            has_cpu_indicators = any(term in top_name_lower for term in ['cpu', 'core', 'risc', 'processor'])
            has_soc_indicators = any(term in top_name_lower for term in ['soc', 'system', 'chip'])
            
            # Protect CPU cores: 
            # 1. High CPU ratio and low SoC ratio, OR
            # 2. Module name indicates CPU/core but not SoC, OR  
            # 3. CPU ratio is decent (>0.2) and name has CPU indicators
            should_protect = (
                (cpu_ratio > soc_ratio and cpu_ratio > 0.3) or
                (has_cpu_indicators and not has_soc_indicators) or
                (cpu_ratio > 0.2 and has_cpu_indicators)
            )
            
            if should_protect:
                print_yellow(f"[MIN] Protecting CPU core top module file: {f} (contains {top_module}, cpu_ratio={cpu_ratio:.2f}, has_cpu_indicators={has_cpu_indicators})")
                continue
            else:
                print_green(f"[MIN] Top module '{top_module}' appears to be SoC wrapper (cpu_ratio={cpu_ratio:.2f}, soc_ratio={soc_ratio:.2f}) - allowing removal to find CPU core")
            
        print_green(f"[MIN] Trying to remove file: {f}")
        try:
            files.remove(f)
        except ValueError:
            print_yellow(f"[MIN] Warning: file {f} not found in current file list, skipping")
            continue

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
                # Check if the failure is due to missing packages that we can fix by excluding more files
                missing_packages = parse_missing_packages_from_log(out)
                if missing_packages:
                    # Find files with broken imports and exclude them
                    broken_files = find_files_with_broken_imports(repo_root, files, missing_packages)
                    if broken_files:
                        # Remove broken files and try again with the current removal
                        original_count = len(files)
                        files = [candidate_f for candidate_f in files if candidate_f not in broken_files]
                        excluded_count = original_count - len(files)
                        print_green(f"[MIN] Excluded {excluded_count} additional files with broken imports")
                        for excluded in broken_files:
                            print_yellow(f"[MIN-BROKEN_IMPORTS] Excluded file: {excluded}")
                        
                        # Try simulation again without the broken files
                        rc_broken, out_broken, cfg_broken = run_simulation_with_config(
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
                        last_log = out_broken
                        if rc_broken == 0:
                            print_green(f"[MIN] Removed {f} successfully after excluding files with broken imports")
                            continue
                
                # Check if the failure is due to syntax errors that we can fix by excluding more files
                syntax_error_files = parse_syntax_errors_from_log(out)
                if syntax_error_files:
                    # Find files with syntax errors and exclude them
                    files_to_exclude = []
                    for error_file in syntax_error_files:
                        for candidate_f in files:
                            if candidate_f == error_file or candidate_f.endswith(error_file.split('/')[-1]):
                                files_to_exclude.append(candidate_f)
                    
                    if files_to_exclude:
                        # Remove syntax error files and try again with the current removal
                        original_count = len(files)
                        files = [candidate_f for candidate_f in files if candidate_f not in files_to_exclude]
                        excluded_count = original_count - len(files)
                        print_green(f"[MIN] Excluded {excluded_count} additional files with syntax errors")
                        for excluded in files_to_exclude:
                            print_yellow(f"[MIN-SYNTAX] Excluded file: {excluded}")
                        
                        # Try simulation again without the syntax error files
                        rc2, out2, cfg2 = run_simulation_with_config(
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
                        last_log = out2
                        if rc2 == 0:
                            print_green(f"[MIN] Removed {f} successfully after excluding syntax error files")
                            continue
                
                # Check if the failure is due to missing entities in GHDL that we can fix by excluding files with broken references
                missing_entities = parse_ghdl_missing_entities_from_log(out)
                if missing_entities and is_vhdl_project(files):
                    # Find files that reference missing entities and exclude them
                    files_to_exclude = []
                    for missing_entity in missing_entities:
                        for candidate_f in files:
                            if references_missing_entity(candidate_f, missing_entity, repo_root):
                                files_to_exclude.append(candidate_f)
                    
                    if files_to_exclude:
                        # Remove files with broken entity references and try again with the current removal
                        original_count = len(files)
                        files = [candidate_f for candidate_f in files if candidate_f not in files_to_exclude]
                        excluded_count = original_count - len(files)
                        print_green(f"[MIN] Excluded {excluded_count} additional files with missing entity references")
                        for excluded in files_to_exclude:
                            print_yellow(f"[MIN-GHDL] Excluded file: {excluded} (references missing entities)")
                        
                        # Try simulation again without the files with broken references
                        rc3, out3, cfg3 = run_simulation_with_config(
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
                        last_log = out3
                        if rc3 == 0:
                            print_green(f"[MIN] Removed {f} successfully after excluding files with missing entity references")
                            continue
                
                print_yellow(f"[MIN] Removing {f} broke sim, restoring")
                files.append(f)
                continue

        # Special case: removed the top file - decide whether to keep or replace
        print_yellow(f"[MIN] Removed file of current top '{top_module}' - analyzing module type...")
        
        # Analyze if the top module is likely a CPU core or SoC wrapper
        top_name_lower = top_module.lower()
        is_likely_core = any(term in top_name_lower for term in ['core', 'cpu', 'proc', 'processor'])
        is_likely_soc = any(term in top_name_lower for term in ['soc', 'system', 'chip', 'top'])
        
        # If it looks like a CPU core and not a SoC, keep the file
        if is_likely_core and not is_likely_soc:
            print_green(f"[MIN] Top module '{top_module}' appears to be CPU core - restoring file {f}")
            files.append(f)
            continue
        
        # Otherwise, try to find a replacement top module
        print_green(f"[MIN] Top module '{top_module}' appears to be SoC wrapper - searching for CPU core replacement...")
        candidates, _ = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name, modules=modules)
        
        # Filter candidates to those that still have files available and prefer CPU cores
        available_candidates = []
        for cand in candidates:
            if cand != top_module and module_to_file.get(cand, "") in files:
                cand_lower = cand.lower()
                cand_is_core = any(term in cand_lower for term in ['core', 'cpu', 'proc', 'processor'])
                cand_is_soc = any(term in cand_lower for term in ['soc', 'system', 'chip', 'top'])
                # Prefer CPU cores over SoC wrappers
                priority = 2 if cand_is_core and not cand_is_soc else 1 if not cand_is_soc else 0
                available_candidates.append((priority, cand))
        
        # Sort by priority (higher first)
        available_candidates.sort(key=lambda x: x[0], reverse=True)
        
        print_green(f"[MIN] Testing {len(available_candidates)} replacement candidates...")
        new_top = None
        for priority, cand in available_candidates:
            print_green(f"[MIN] Testing candidate: {cand} (priority: {priority})")
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
                print_green(f"[MIN] Found working replacement: {cand}")
                break
            else:
                # Try to handle syntax errors during top module reselection
                syntax_error_files = parse_syntax_errors_from_log(out)
                if syntax_error_files:
                    files_to_exclude = []
                    for error_file in syntax_error_files:
                        for candidate_f in files:
                            if candidate_f == error_file or candidate_f.endswith(error_file.split('/')[-1]):
                                files_to_exclude.append(candidate_f)
                    
                    if files_to_exclude:
                        # Try once more after excluding syntax error files
                        temp_files = [candidate_f for candidate_f in files if candidate_f not in files_to_exclude]
                        if module_to_file.get(cand, "") in temp_files:
                            rc2, out2, cfg2 = run_simulation_with_config(
                                repo_root,
                                repo_name,
                                url,
                                tb_files,
                                temp_files,
                                inclu,
                                cand,
                                language_version,
                                timeout=240,
                                verilator_extra_flags=verilator_extra_flags,
                                ghdl_extra_flags=ghdl_extra_flags,
                            )
                            if rc2 == 0:
                                # Success! Update files and set new top
                                files = temp_files
                                new_top = cand
                                excluded_count = len(files_to_exclude)
                                print_green(f"[MIN] Excluded {excluded_count} syntax error files during top reselection")
                                for excluded in files_to_exclude:
                                    print_yellow(f"[MIN-TOP-SYNTAX] Excluded file: {excluded}")
                                break

        if new_top:
            print_green(f"[MIN] Successfully switched from SoC '{top_module}' to replacement '{new_top}'")
            top_module = new_top
        else:
            print_yellow(f"[MIN] No valid replacement top found, restoring SoC file {f}")
            files.append(f)

    print_green("[MIN] Minimization finished")
    
    # Final simulation test to verify the configuration is actually simulable
    print_green("[FINAL_TEST] Testing final configuration for simulability...")
    rc, final_test_log, _ = run_simulation_with_config(
        repo_root,
        repo_name,
        url,
        tb_files,
        files,
        inclu,
        top_module,
        language_version,
        timeout=60,
        verilator_extra_flags=verilator_extra_flags,
        ghdl_extra_flags=ghdl_extra_flags,
    )
    
    is_simulable = (rc == 0)
    if is_simulable:
        print_green("[FINAL_TEST] ✓ Configuration is simulable!")
    else:
        print_yellow("[FINAL_TEST] ✗ Configuration failed final simulation test")
        print_yellow(f"[FINAL_TEST] Errors: {parse_syntax_errors_from_log(final_test_log)}")
    
    return files, inclu, last_log, top_module, is_simulable


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
        if not file_path:
            continue
        
        # Handle both absolute and relative paths
        full_path = file_path
        if not os.path.isabs(file_path):
            # Try to construct full path if it's relative
            if os.path.exists(file_path):
                full_path = file_path
            else:
                # Look for the file in common locations
                possible_paths = [
                    os.path.join('temp', file_path),
                    os.path.join('temp', '*', file_path),  # Will need glob for this
                ]
                for possible_path in possible_paths:
                    if '*' in possible_path:
                        matches = glob.glob(possible_path)
                        if matches:
                            full_path = matches[0]
                            break
                    elif os.path.exists(possible_path):
                        full_path = possible_path
                        break
        
        if not os.path.exists(full_path):
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)  # Read first 4KB
                if sv_regex.search(content):
                    return True
        except Exception:
            continue
    
    return False


def determine_language_version(extension: str, files: list = None, base_path: str = None) -> str:
    """
    Determines the language version based on file extension and incompatible syntax detection.
    Starts with newest version and only regresses when unsupported syntax is found.
    """
    # Start optimistic with modern versions
    base_version = {
        '.vhdl': '08',
        '.vhd': '08', 
        '.sv': '2017',    
        '.svh': '2017',   
    }.get(extension, '2017')  
    
    if not files:
        return base_version
    
    if extension in ['.vhdl', '.vhd']:
        return base_version
    
    detected_version = analyze_verilog_language_features(files, base_path)
    
    return detected_version


def analyze_verilog_language_features(files: list, base_path: str = None) -> str:
    """
    Analyze Verilog/SystemVerilog files and return the lowest common denominator
    language version string compatible with Verilator's --language flag.
    Starts from SystemVerilog-2017 and downgrades only if discontinued syntax is found.
    """

    versions = {
        "1364-1995": 0,
        "1364-2001": 1,
        "1364-2005": 2,
        "1800-2005": 3,
        "1800-2009": 4,
        "1800-2012": 5,
        "1800-2017": 6,
    }
    detected = versions["1800-2017"]  

    downgrade_rules = {
        "1364-1995": [
            r'`expand_vectornets',                 
            r'\bscalared\b|\bvectored\b',          
            r'^\s*primitive\s+\w+\s*\(',          
        ],
        "1364-2005": [
            r'`timescale\s+\d+\s*\w+\s*/\s*\d+\s*\w+(?!\s*//)',  
            r'\bforce\b|\brelease\b',             
            r'`include\s+"[^"]*\.vh"',             
        ],
        "1800-2005": [
            r'defparam\s+\w+\.\w+\s*=',            
            r'^\s*UDP\s+\w+\s*\(',                
            r'\$time\b(?!\s*\()',                  
            r'^\s*specify\s*$',                    
            r'\bwand\b|\bwor\b|\btri0\b|\btri1\b|\btriand\b|\btrior\b',
        ],
    }

    modern_features = [
        r'\balways_ff\b|\balways_comb\b|\balways_latch\b',
        r'\binterface\b|\bmodport\b',
        r'\blogic\b',
        r'\bclass\b|\bpackage\b',
        r'\btypedef\s+(enum|struct|union)',
        r'\bunique\s+case|\bpriority\s+case',
        r'\bcovergroup\b|\bassert\b|\bconstraint\b',
    ]

    compiled_rules = {
        target: [re.compile(p, re.I | re.M) for p in pats]
        for target, pats in downgrade_rules.items()
    }
    compiled_features = [re.compile(p, re.I | re.M) for p in modern_features]

    found_modern = False

    for file_path in files:
        try:
            full_path = (
                os.path.join(base_path, file_path)
                if base_path and not os.path.isabs(file_path)
                else file_path
            )
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for target, patterns in compiled_rules.items():
                for pat in patterns:
                    if pat.search(content):
                        detected = min(detected, versions[target])
                        print(f"[LANG] {file_path}: matched {pat.pattern}, downgrade → {target}")
                        break
                if detected == versions[target]:
                    break  

            if detected >= versions["1800-2009"]:
                for feat in compiled_features:
                    if feat.search(content):
                        found_modern = True
                        print(f"[LANG] {file_path}: found modern SV feature {feat.pattern}")
                        break

        except Exception as e:
            print(f"[LANG] Warning: Could not analyze {file_path}: {e}")

    if detected < versions["1800-2005"]:  
        resolved = [v for v, pri in versions.items() if pri == detected][0]
    else:
        if found_modern:
            resolved = "1800-2017"
        else:
            resolved = "1800-2012"

    print(f"[LANG] Final detected version: {resolved}")
    return resolved


def create_output_json(
    repo_name,
    url,
    tb_files,
    filtered_files,
    include_dirs,
    top_module,
    language_version,
    is_simulable=False,
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
        'is_simulable': is_simulable,
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


def build_and_log_graphs(files: list, modules: list, destination_path: str = None) -> tuple:
    """Builds the direct and inverse module dependency graphs and logs the result."""
    print_green('[LOG] Construindo os grafos direto e inverso\n')
    
    # Convert relative paths back to absolute paths for build_module_graph
    if destination_path:
        absolute_files = [os.path.join(destination_path, f) if not os.path.isabs(f) else f for f in files]
    else:
        absolute_files = files
    
    module_graph, module_graph_inverse = build_module_graph(absolute_files, modules)
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
    module_graph, module_graph_inverse = build_and_log_graphs(non_tb_files, modules, destination_path)

    filtered_files, top_module = process_files_with_llama(
        no_llama, non_tb_files, tb_files, modules, module_graph, repo_name, model,
    )
    language_version = determine_language_version(extension, filtered_files, destination_path)

    final_files, final_include_dirs, last_log, top_module, is_simulable = interactive_simulate_and_minimize(
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
        verilator_extra_flags=['-Wno-lint', '-Wno-fatal', '-Wno-style', '-Wno-UNOPTFLAT', '-Wno-UNDRIVEN', '-Wno-UNUSED'],
        ghdl_extra_flags=['--std=08', '-frelaxed'],
    )

    output_json = create_output_json(
        repo_name, url, tb_files, final_files, final_include_dirs, top_module, language_version, is_simulable,
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
        '-u', 
        '--processor-url', 
        type=str, 
        required=True,
        help='URL of the processor repository'
    )
    parser.add_argument(
        '-p', 
        '--config-path', 
        type=str, 
        default='config/',
        help='Path to save the configuration file'
    )
    parser.add_argument(
        '-g', 
        '--plot-graph', 
        action='store_true',
        help='Plot the module dependency graph'
    )
    parser.add_argument(
        '-a', 
        '--add-to-config', 
        action='store_true',
        help='Add the generated configuration to a central config file'
    )
    parser.add_argument(
        '-n', 
        '--no-llama', 
        action='store_true',
        help='Skip OLLAMA processing for top module identification'
    )
    parser.add_argument(
        '-m', 
        '--model', 
        type=str, 
        default='qwen2.5:32b',
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
