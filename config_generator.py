"""
Processor Configuration Generator

This script analyzes processor repositories and generates processor configurations.
It includes the following functionality:
- Cloning processor repositories and analyzing their files.
- Extracting hardware modules and testbench files from the repository.
- Building module dependency graphs.
- Generating configuration files for the processor.
- Interactive simulation and file minimization.
- **Chisel/Scala support**: Automatic detection and processing of Chisel projects

Supported Languages:
-------------------
- Verilog (.v)
- SystemVerilog (.sv)
- VHDL (.vhd, .vhdl)
- **Chisel (.scala)** - Automatically detects, analyzes, and generates Verilog

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
- `-l`, `--local-repo`: Path to local repository (skips cloning if provided).

Usage:
------
# Process a remote repository
python config_generator.py -u <processor_url> -p config/

# Process a local repository (including Chisel projects)
python config_generator.py -u <repo_url> -l /path/to/local/repo -p config/
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
    find_missing_modules,
    find_missing_module_files,
    should_exclude_file,
)
from core.graph import build_module_graph, plot_processor_graph
from core.ollama import (
    get_filtered_files_list,
    get_top_module,
)
from core.log import print_green, print_red, print_yellow
from core.chisel_manager import (
    find_scala_files,
    extract_chisel_modules,
    build_chisel_dependency_graph,
    find_top_module as find_chisel_top_module,
    generate_main_app,
    configure_build_file,
    emit_verilog,
    process_chisel_project,
)
from verilator_runner import (
    compile_incremental as verilator_incremental,
)
from ghdl_runner import (
    incremental_compilation as ghdl_incremental,
)


# Constants
EXTENSIONS = ['v', 'sv', 'vhdl', 'vhd', 'scala']  # Note: .vm files are FPGA netlists, not RTL
DESTINATION_DIR = './temp'
UTILITY_PATTERNS = (
    "gen_", "dff", "buf", "full_handshake", "fifo", "mux", "regfile"
)


def _is_peripheral_like_name(name: str) -> bool:
    """Heuristic check for peripheral/SoC fabric/memory module names we don't want as CPU tops.
    Examples: axi4memory, axi_*, apb_*, ahb_*, wb_*, uart, spi, i2c, gpio, timer, dma, plic, clint, cache, ram, rom, bridge, interconnect.
    """
    n = (name or "").lower()
    # Strong signals for bus fabrics and memories
    if ("axi" in n) or n.startswith(("axi_", "apb_", "ahb_", "wb_", "avalon_", "tl_", "tilelink_")):
        return True
    if any(t in n for t in ["memory", "ram", "rom", "cache", "sdram", "ddr", "bram"]):
        return True
    if any(t in n for t in ["uart", "spi", "i2c", "gpio", "timer", "dma", "plic", "clint", "jtag", "bridge", "interconnect", "xbar"]):
        return True
    if any(t in n for t in ["axi4", "axi_lite", "axi4lite", "axi_lite_ctrl", "axi_ctrl"]):
        return True
    return False


def _is_functional_unit_name(name: str) -> bool:
    """Heuristic for small functional units we don't want as the overall CPU top.
    Examples: multiplier, divider, alu, adder, shifter, barrel, encoder, decoder, fpu, cache.
    """
    n = (name or "").lower()
    terms = [
    "multiplier", "divider", "div", "mul", "alu", "adder", "shifter", "barrel",
    "encoder", "decoder",
    "fpu", "fpdiv", "fpsqrt",
    "cache", "icache", "dcache", "tlb",
    "btb", "branch", "predictor", "ras", "returnaddress", "rsb"
    ]
    # Check for branch predictor patterns but avoid false positives with project initials
    # e.g., "bp" should match "branch_predictor" or "_bp_" but not "bp_core" (BlackParrot core)
    for t in terms:
        if t in n:
            return True
    
    # Special check for "bp" (branch predictor) - only match if it's clearly branch predictor context
    # Match: "_bp_", "_bp", "bp_pred", "bpred", etc.
    # Don't match: "bp_core", "bp_processor", "bp_unicore" (BlackParrot modules)
    if ("_bp_" in n or n.endswith("_bp") or n.startswith("bp_pred") or "bpred" in n):
        # But don't penalize if it's clearly a CPU core/processor
        if not any(x in n for x in ["core", "processor", "cpu", "unicore", "multicore"]):
            return True
    
    return False


def _is_micro_stage_name(name: str) -> bool:
    """Heuristic for pipeline stage blocks that are not full CPU tops (fetch/rename/issue/etc.)."""
    n = (name or "").lower()
    terms = [
    "fetch", "decode", "rename", "issue", "schedule", "commit", "retire",
    "execute", "registerread", "registerwrite", "regread", "regwrite",
    "lsu", "mmu", "reorder", "rob", "iq", "btb", "bpu", "ras",
    "predecode", "dispatch", "wakeup", "queue", "storequeue", "loadqueue",
    "activelist", "freelist", "rmt", "nextpc", "pcstage"
    ]
    exact_stage_names = ["wb", "id", "ex", "mem", "if", "ma", "wr", "pc", "ctrl", "regs", "alu", "dram", "iram", "halt", "machine"]
    if n in exact_stage_names:
        return True
    
    # Check for 'rs' (reservation station) with word boundaries to avoid matching "RS5"
    if "_rs_" in n or n.startswith("rs_") or n.endswith("_rs") or n == "rs":
        return True
    
    return any(t in n for t in terms)


def _is_interface_module_name(name: str) -> bool:
    """Return True for interface-like module names (ControllerIF, DCacheIF, ...)."""
    n = (name or "").lower()
    return n.endswith("if") or "interface" in n


def _is_fpga_path(path: str) -> bool:
    """Return True if the file lives under an 'fpga' or 'boards' folder (case-insensitive).
    Treat these as FPGA board wrapper trees to exclude from core detection.
    Works with relative or absolute paths.
    """
    try:
        p = path.replace("\\", "/").lower()
        return (
            "/fpga/" in p
            or p.startswith("fpga/")
            or "/fpga-" in p
            or p.endswith("/fpga")
            or "/boards/" in p
            or p.startswith("boards/")
            or "/board/" in p
            or p.startswith("board/")
        )
    except Exception:
        return False


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
        r'\b(external_mem|ext_mem|ddr|sdram)\b',
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
        r'\b(addr|address|mem_addr|i_addr|d_addr)\b',
        r'\b(data|mem_data|i_data|d_data|mem_rdata|mem_wdata|rdata|wdata)\b',
        r'\b(mem_req|mem_gnt|mem_rvalid|mem_we|mem_be|we|be)\b',
        r'\b(instr|instruction|i_req|i_gnt|i_rvalid)\b',
        r'\b(icache|dcache|cache_req|cache_resp)\b',
        r'\b(clk|clock|rst|reset|rstn)\b',
        r'\b(irq|interrupt|exception)\b',
        r'\b(halt|stall|flush|valid|ready)\b',
        r'\b(hart|hartid|mhartid)\b',
        r'\b(retire|commit|trap)\b',
        r'\b(axi|ahb|apb|wb|wishbone)\b',
        r'\b(avalon|tilelink)\b'
    ]
    
    # Look for instantiation of the specific module and analyze its connections
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
    # module_graph: A -> [B, C] means A instantiates B and C
    # module_graph_inverse: B -> [A] means B is instantiated by A
    
    instantiates = _ensure_mapping(module_graph)  # What each module instantiates (its children)
    instantiated_by = _ensure_mapping(module_graph_inverse)  # What instantiates each module (its parents)

    nodes = set(instantiated_by.keys()) | set(instantiates.keys())
    for n in nodes:
        instantiated_by.setdefault(n, [])
        instantiates.setdefault(n, [])

    # Filter out Verilog keywords and invalid module names
    valid_modules = []
    verilog_keywords = {"if", "else", "always", "initial", "begin", "end", "case", "default", "for", "while", "assign"}
    
    for module in nodes:
        if (module not in verilog_keywords and 
            len(module) > 1 and 
            (module.replace('_', '').isalnum())):
            valid_modules.append(module)
    
    # Find candidates: modules with few parents (few modules instantiate them) are preferred as top modules
    zero_parent_modules = [m for m in valid_modules if not instantiated_by.get(m, [])]
    low_parent_modules = [m for m in valid_modules if len(instantiated_by.get(m, [])) <= 2]
    
    # Always include standalone 'core' and 'cpu' modules as candidates
    core_cpu_modules = [m for m in valid_modules if m.lower() in ['core', 'cpu', 'processor']]
    
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
            # Enhanced repo matching - include exact matches regardless of parent count
            if (repo_lower == module_lower or 
                repo_lower in module_lower or 
                module_lower in repo_lower):
                repo_name_matches.append(module)
            
            # Also check for common variations
            repo_variations = [repo_lower, repo_lower.upper(), repo_lower.capitalize()]
            for variation in repo_variations:
                if variation == module:
                    repo_name_matches.append(module)
                    print_green(f"[REPO-MATCH] Found repo variation match: {module} -> {variation}")
                    break
            
            # Enhanced CPU core detection using instantiation patterns
            if (any(pattern in module_lower for pattern in [repo_lower, 'cpu', 'core', 'risc', 'processor', 'microcontroller']) and 
                module not in zero_parent_modules and module not in low_parent_modules and
                (module_lower == 'microcontroller' or module_lower == 'core' or module_lower == 'cpu' or 
                 not any(bad_pattern in module_lower for bad_pattern in 
                       ['div', 'mul', 'alu', 'fpu', 'cache', 'mem', 'bus', '_ctrl', 'ctrl_', 'reg', 'decode', 'fetch', 'exec', 'forward', 'hazard', 'pred',
                        'sm3', 'sha', 'aes', 'des', 'rsa', 'ecc', 'crypto', 'hash', 'cipher', 'encrypt', 'decrypt', 'uart', 'spi', 'i2c', 'gpio',
                        'timer', 'interrupt', 'dma', 'pll', 'clk', 'pwm', 'aon', 'hclk', 'oitf', 'wrapper', 'regs'])) and
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
    
    candidates = list(set(zero_parent_modules + low_parent_modules + core_cpu_modules + repo_name_matches + cpu_core_matches))
    
    if not candidates:
        candidates = valid_modules

    repo_lower = (repo_name or "").lower()
    scored = []
    
    # Normalize repo name: remove hyphens and underscores for matching
    repo_normalized = repo_lower.replace('-', '').replace('_', '')
    
    for c in candidates:
        reach = _reachable_size(instantiates, c)  # How many modules does this one instantiate (directly or indirectly)
        score = reach * 10  # Base score from connectivity
        name_lower = c.lower()
        name_normalized = name_lower.replace('_', '')

        # REPOSITORY NAME MATCHING (Highest Priority)
        # Only apply repo matching if the module actually exists in the dependency graph
        if repo_normalized and len(repo_normalized) > 2 and c in module_graph:
            if repo_normalized == name_normalized:
                score += 50000
            elif repo_normalized in name_normalized:
                score += 40000
            elif name_normalized in repo_normalized:
                score += 35000
            else:
                # Check initialism matching (e.g., "black-parrot" → "bp")
                # Extract initials from words separated by hyphens or underscores
                repo_words = repo_lower.replace('_', '-').split('-')
                if len(repo_words) >= 2:
                    initialism = ''.join(word[0] for word in repo_words if word)
                    # Check if module starts with initialism + underscore (e.g., "bp_core")
                    if name_lower.startswith(initialism + '_'):
                        # Check if it's a core/processor/cpu module
                        if any(x in name_lower for x in ['core', 'processor', 'cpu', 'unicore', 'multicore']):
                            score += 45000
                            print_green(f"[REPO-MATCH] Initialism match: {repo_lower} → {initialism} → {c}")
                
                # Fuzzy matching
                clean_repo = repo_lower
                clean_module = name_lower
                
                for pattern in ["_cpu", "_core", "cpu_", "core_", "_top", "top_"]:
                    clean_repo = clean_repo.replace(pattern, "")
                    clean_module = clean_module.replace(pattern, "")
                
                if clean_repo == clean_module and len(clean_repo) > 1:
                    score += 30000
                elif clean_repo in clean_module or clean_module in clean_repo:
                    score += 20000
        
        # SPECIAL CASE: "Top" module when repo name doesn't match any real module
        if name_lower == "top" and repo_lower:
            # Check if the exact repo name exists as a real module in the graph
            repo_name_exists = any(repo_lower == mod.lower() for mod in module_graph.keys() if mod in valid_modules)
            if not repo_name_exists:
                score += 48000  # High but slightly less than exact repo match

        # ARCHITECTURAL INDICATORS
        if any(term in name_lower for term in ["cpu", "processor"]):
            score += 2000
        
        # Special case for microcontroller - this is a CPU top module
        if "microcontroller" in name_lower:
            score += 3000
        
        # CPU TOP MODULE DETECTION (Very High Priority)
        # Look for typical CPU top module patterns
        cpu_top_patterns = [
            f"{repo_lower}_top", f"top_{repo_lower}", f"{repo_lower}_cpu", f"cpu_{repo_lower}",
            "cpu_top", "core_top", "processor_top", "riscv_top", "risc_top"
        ]
        if repo_lower:
            cpu_top_patterns.extend([repo_lower, f"{repo_lower}_core", f"core_{repo_lower}"])
        
        for pattern in cpu_top_patterns:
            if name_lower == pattern:
                # Ensure it's not a functional unit
                if not any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu"]):
                    score += 45000
                    break
        
        # DIRECT CORE NAME PATTERNS (high priority - we want cores, not SoCs)
        # Special case for exact "Core" module name - very common CPU top module pattern
        if name_lower == "core":
            score += 40000
        
        # Look for modules that are exactly the repo name (likely the core)
        if repo_lower and name_lower == repo_lower:
            score += 25000
        
        # Specific CPU core boost - give highest priority to actual core modules
        if "core" in name_lower and repo_lower:
            # Check if it's a functional unit core first - apply heavy penalty
            if any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu", "mem", "cache", "bus", "_ctrl", "ctrl_", "reg", "decode", "fetch", "exec", "forward", "hazard", "pred", "shift", "barrel", "adder", "mult", "divider", "encoder", "decoder"]):
                # Exception: don't penalize microcontroller
                if "microcontroller" not in name_lower:
                    score -= 15000
            # Penalize subsystem cores - they're usually wrappers around the actual core
            elif "subsys" in name_lower or "subsystem" in name_lower:
                score -= 8000
            # Strong boost for exact core modules like "repo_core"
            elif name_lower == f"{repo_lower}_core" or name_lower == f"core_{repo_lower}":
                score += 25000
            # Generic pattern: any module ending with "_core" that looks like a main core module
            elif name_lower.endswith("_core"):
                score += 20000
            # Medium boost for modules containing both repo name and core
            elif repo_lower in name_lower and "core" in name_lower:
                score += 15000
        
        if "core" in name_lower:
            # Heavy penalty for functional unit cores
            if any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu"]):
                score -= 10000
            # Additional penalty for other peripheral cores (but exclude microcontroller)
            elif not ("microcontroller" in name_lower) and any(unit in name_lower for unit in ["mem", "cache", "bus", "_ctrl", "ctrl_", "reg", "decode", "fetch", "exec", "forward", "hazard", "pred", "shift", "barrel", "adder", "mult", "divider", "encoder", "decoder"]):
                score -= 5000
            else:
                score += 1500
        
        if any(arch in name_lower for arch in ["riscv", "risc", "mips", "arm"]):
            score += 1000
        
        if name_lower.endswith("_top") or name_lower.startswith("top_"):
            score += 800

        # Penalize single functional units (ALU, multiplier, divider, etc.)
        if _is_functional_unit_name(name_lower):
            score -= 12000
        # Penalize micro-stage modules that are unlikely to be CPU tops
        if _is_micro_stage_name(name_lower):
            score -= 40000

        # Penalize interface-only modules
        if _is_interface_module_name(name_lower):
            score -= 12000

        # Path-aware penalty: if the module's file lives in a micro-stage subfolder, penalize
        mod_file = None
        if modules:
            for mname, mfile in modules:
                if mname == c:
                    mod_file = mfile
                    break
        if mod_file:
            path_l = mod_file.replace("\\", "/").lower()
            stage_dirs = [
                "/fetchunit/", "/fetchstage/", "/rename", "/renamelogic/", "/scheduler/", "/decode",
                "/commit", "/dispatch", "/issue", "/execute", "/integerbackend/",
                "/memorybackend/", "/fpbackend/", "/muldivunit/", "/floatingpointunit/"
            ]
            if any(sd in path_l for sd in stage_dirs):
                score -= 15000
        
        # SOC penalty - we want CPU cores, not full system-on-chip
        if "soc" in name_lower:
            score -= 5000
        
        # Penalize utility library modules when project-specific modules exist
        # e.g., penalize bsg_* modules when bp_* modules exist (basejump_stl vs black-parrot)
        if repo_lower and len(repo_lower) > 2:
            repo_words = repo_lower.replace('_', '-').split('-')
            if len(repo_words) >= 2:
                initialism = ''.join(word[0] for word in repo_words if word)
                # Check if any modules start with the project initialism
                project_modules_exist = any(m.lower().startswith(initialism + '_') for m in valid_modules)
                
                # If project modules exist (like bp_*) and this is a utility (like bsg_*)
                if project_modules_exist:
                    # Penalize modules that don't start with the project initialism
                    # Common utility prefixes: bsg_, hardfloat_, common_
                    if not name_lower.startswith(initialism + '_'):
                        # Only penalize if it starts with a known utility prefix
                        utility_prefixes = ['bsg_', 'common_', 'util_', 'lib_', 'helper_']
                        if any(name_lower.startswith(prefix) for prefix in utility_prefixes):
                            score -= 35000

    # STRUCTURAL HEURISTICS
        num_children = len(instantiates.get(c, []))  # What this module instantiates
        num_parents = len(instantiated_by.get(c, []))  # Who instantiates this module
        
        # Boost CPU cores (modules with few parents and "core"/"cpu"/"processor" in name)
        # These are better targets for testing than SoC tops
        # Can have multiple parents (different top-level wrappers, test harnesses, etc.)
        is_likely_core = (num_parents >= 1 and num_parents <= 3 and 
                          any(pattern in name_lower for pattern in ['core', 'cpu', 'processor']) and
                          not any(bad in name_lower for bad in ['_top', 'top_', 'soc', 'system', 'wrapper']))
        
        if is_likely_core and num_children > 2:
            score += 25000  # Very strong preference for CPU cores
        elif num_children > 10 and num_parents == 0:
            score += 1000
        elif num_children > 5 and num_parents <= 1:
            score += 500
        elif num_children > 2:
            score += 200

        # Boost if the module instantiates components from multiple CPU subsystems (suggests a core)
        if modules:
            mod_file = None
            for mname, mfile in modules:
                if mname == c:
                    mod_file = mfile
                    break
            if mod_file and os.path.exists(mod_file):
                patterns = _analyze_instantiation_patterns(c, mod_file)
                insts = patterns.get('instantiated_modules', []) if patterns else []
                subsys_hits = 0
                text = " ".join(insts)
                for kw in ["fetch", "decode", "rename", "issue", "commit", "schedule", "lsu", "cache", "branch", "rob", "regfile", "csr"]:
                    if re.search(rf"\b{kw}\b", text, re.I):
                        subsys_hits += 1
                if subsys_hits >= 3:
                    score += 4000

        # NEGATIVE INDICATORS
        if any(pattern in name_lower for pattern in ["_tb", "tb_", "test", "bench", "compliance", "verify", "checker", "monitor", "fpv", "bind", "assert"]):
            score -= 10000
        
        peripheral_terms = ["uart", "spi", "i2c", "gpio", "timer", "dma", "plic", "clint", "baud", "fifo", "ram", "rom", "cache", "pwm", "aon", "hclk", "oitf", "wrapper", "regs"]
        if any(term in name_lower for term in peripheral_terms):
            score -= 5000

        # Very strong penalty for modules that look like memory/fabric/peripheral wrappers
        if _is_peripheral_like_name(name_lower):
            score -= 15000
        
        # Generic penalty for likely peripheral module prefixes
        peripheral_prefixes = ["sirv_", "apb_", "axi_", "ahb_", "wb_", "avalon_"]
        if any(name_lower.startswith(prefix) for prefix in peripheral_prefixes):
            score -= 7000
        
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

    # CONDITIONAL TOP MODULE PENALTY
    # Check if there are any "core" or "cpu" candidates in the list that are better choices than "top"
    # This includes:
    # 1. Modules with "core", "cpu", "processor", or "riscv" in their names (but not wrapped in _top/top_)
    # 2. Exact matches like "CPU", "Core", "Processor", "RISCV" (standalone names)
    # 3. Exclude peripheral cores (SPI, UART, I2C, GPIO, etc.)
    peripheral_patterns = ['spi', 'uart', 'i2c', 'gpio', 'timer', 'pwm', 'adc', 'dac', 'can', 'usb', 'eth', 'pci']
    
    has_core_candidates = any(
        (any(pattern in c.lower() for pattern in ['core', 'cpu', 'processor', 'riscv', 'atom']) or
         c in ['CPU', 'Core', 'Processor', 'CORE', 'RISCV'])
        and not any(bad in c.lower() for bad in ['_top', 'top_', 'soc', 'system', 'wrapper'])
        and not any(periph in c.lower() for periph in peripheral_patterns)
        for score, reach, c in scored
    )
    
    # If core candidates exist, apply penalty to "top" modules and boost to core/cpu modules
    if has_core_candidates:
        adjusted_scored = []
        for score, reach, c in scored:
            name_lower = c.lower()
            # Check if this is a top-level wrapper
            num_parents = len(instantiated_by.get(c, []))
            
            # Penalize if:
            # 1. Has "_top" or "top_" pattern (like e203_cpu_top, ibex_top)
            # 2. Is exactly named "top" (generic top module)
            is_top_wrapper = (num_parents == 0 and 
                             (any(pattern in name_lower for pattern in ['_top', 'top_']) or
                              name_lower == 'top'))
            
            # Boost if this is a CPU/core/RISCV module (exact matches or with cpu/core/riscv/atom in name)
            # Exclude peripheral cores (SPI_core, UART_core, etc.)
            is_cpu_core = (
                (c in ['CPU', 'Core', 'Processor', 'CORE', 'RISCV'] or
                 any(pattern in name_lower for pattern in ['_cpu', 'cpu_', '_core', 'core_', 'riscv', 'atom']))
                and not any(periph in name_lower for periph in peripheral_patterns)
            )
            
            # Check if this is a bus wrapper (has bus protocol suffix)
            bus_wrapper_patterns = ['_wb', '_axi', '_ahb', '_apb', '_obi', '_tilelink']
            is_bus_wrapper = any(pattern in name_lower for pattern in bus_wrapper_patterns)
            
            # Always penalize top wrappers when core candidates exist, even if they have core/cpu/riscv in name
            # (e.g., RISCV_TOP should be penalized in favor of RISCV)
            if is_top_wrapper:
                # Apply a strong penalty to prefer cores over wrappers
                score -= 15000  # Strong penalty to overcome structural advantage
                print_yellow(f"[RANKING] Applying top-wrapper penalty to {c} (core/cpu candidates available)")
            elif is_cpu_core and is_bus_wrapper:
                # Bus wrappers get a smaller boost (prefer the unwrapped core)
                score += 5000  # Moderate boost for bus-wrapped cores
                print_yellow(f"[RANKING] Applying bus-wrapper boost to {c}")
            elif is_cpu_core and not any(bad in name_lower for bad in ['_top', 'top_', 'soc', 'system', 'wrapper']):
                # Pure cores get the full boost
                score += 10000  # Significant boost for CPU/core modules
                print_yellow(f"[RANKING] Applying CPU/core boost to {c}")
            
            adjusted_scored.append((score, reach, c))
        scored = adjusted_scored

    # Sort by score (descending), then by reach (descending), then by name
    scored.sort(reverse=True, key=lambda t: (t[0], t[1], t[2]))

    ranked = [c for score, _, c in scored if score > -5000]
    # If the top few are micro-stage or interface modules, try to skip them in favor of a core-like one
    filtered_ranked = [c for c in ranked if not _is_micro_stage_name(c.lower()) and not _is_interface_module_name(c.lower())]
    if filtered_ranked:
        ranked = filtered_ranked
    return ranked, cpu_core_matches


def try_incremental_approach(
    repo_root: str,
    repo_name: str,
    top_candidates: list,
    modules: list,
    module_graph: dict,
    language_version: str = "1800-2017",
    verilator_extra_flags: list = None,
    timeout: int = 300,
) -> tuple:
    """
    Try the incremental bottom-up approach for Verilog/SystemVerilog files.
    
    Returns: (final_files, final_includes, last_log, selected_top, is_simulable)
    """
    print_green(f"[INCREMENTAL] Trying bottom-up incremental approach for {repo_name}")
    
    # Limit number of candidates to avoid excessive testing
    MAX_CANDIDATES_TO_TRY = 10
    if len(top_candidates) > MAX_CANDIDATES_TO_TRY:
        print_yellow(f"[INCREMENTAL] Limiting to top {MAX_CANDIDATES_TO_TRY} candidates (out of {len(top_candidates)})")
        top_candidates = top_candidates[:MAX_CANDIDATES_TO_TRY]
    
    print_green(f"[INCREMENTAL] Candidates to try: {', '.join(top_candidates)}")
    
    # Build module->file map
    module_to_file = {}
    for mname, mfile in (modules or []):
        module_to_file[mname] = mfile
    
    # Try each top candidate with incremental compilation
    for idx, top_module in enumerate(top_candidates, 1):
        print_green(f"[INCREMENTAL] === Candidate {idx}/{len(top_candidates)}: {top_module} ===")
        if top_module not in module_to_file:
            print_yellow(f"[INCREMENTAL] Skipping {top_module} - no file mapping found")
            continue
        
        top_module_file = module_to_file[top_module]
        
        # Make sure it's a relative path
        if os.path.isabs(top_module_file):
            top_module_file = os.path.relpath(top_module_file, repo_root)
        
        # Also strip any leading repo path components that might be in the path
        # For example: "temp/black-parrot/bp_be/..." should become "bp_be/..."
        repo_basename = os.path.basename(repo_root)
        if top_module_file.startswith(f"{repo_basename}/"):
            top_module_file = top_module_file[len(repo_basename)+1:]
        elif top_module_file.startswith("temp/"):
            # Handle "temp/black-parrot/..." -> strip temp/ prefix
            parts = top_module_file.split('/')
            if len(parts) > 2 and parts[0] == "temp":
                top_module_file = "/".join(parts[2:])  # Skip "temp/reponame/"
        
        print_green(f"[INCREMENTAL] Testing top module: {top_module}")
        print_green(f"[INCREMENTAL] Top module file (final): {top_module_file}")
        print_yellow(f"[INCREMENTAL] Repo root: {repo_root}")
        print_yellow(f"[INCREMENTAL] Repo basename: {repo_basename}")
        
        # Verify the file exists
        full_path = os.path.join(repo_root, top_module_file)
        if not os.path.exists(full_path):
            print_red(f"[INCREMENTAL] ERROR: File does not exist: {full_path}")
            print_red(f"[INCREMENTAL] Skipping {top_module}")
            continue
        else:
            print_green(f"[INCREMENTAL] ✓ File exists: {full_path}")
        
        rc, log, final_files, final_includes = verilator_incremental(
            repo_root=repo_root,
            top_module=top_module,
            top_module_file=top_module_file,
            module_graph=module_graph,
            language_version=language_version,
            extra_flags=verilator_extra_flags or ['-Wno-lint', '-Wno-fatal', '-Wno-style', '-Wno-BLKANDNBLK', '-Wno-SYMRSVDWORD'],
            max_iterations=20,
            timeout=timeout,
        )
        
        if rc == 0:
            print_green(f"[INCREMENTAL] ✓ Success with top module: {top_module}")
            return final_files, final_includes, log, top_module, True
        else:
            print_yellow(f"[INCREMENTAL] ✗ Failed with top module: {top_module}")
    
    # If all failed, return empty result
    return [], set(), "", "", False


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
    Interactive flow is now delegated to runners. Core only selects candidates and passes to runners.
    """
    # Proactively drop any FPGA-related files from candidates to avoid board wrappers influencing top detection
    candidate_files = [f for f in candidate_files if not _is_fpga_path(f)]
    tb_files = [f for f in tb_files if not _is_fpga_path(f)]

    # Filter out unit-test verification trees that frequently redefine parameters and test-only scaffolding
    def _is_unittest_path(p: str) -> bool:
        try:
            pl = p.replace("\\", "/").lower()
            return "/verification/unittest/" in pl
        except Exception:
            return False

    before_cf, before_tb = len(candidate_files), len(tb_files)
    candidate_files = [f for f in candidate_files if not _is_unittest_path(f)]
    tb_files = [f for f in tb_files if not _is_unittest_path(f)]
    dropped_cf, dropped_tb = before_cf - len(candidate_files), before_tb - len(tb_files)
    if dropped_cf or dropped_tb:
        print_yellow(f"[FILTER] Excluded Verification/UnitTest files -> non-tb:{dropped_cf} tb:{dropped_tb}")
    # Rank candidates using existing heuristics
    candidates, cpu_core_matches = rank_top_candidates(module_graph, module_graph_inverse, repo_name=repo_name, modules=modules)
    print(candidates)
    if not candidates:
        candidates = [m for m, _ in modules] if modules else []

    # Build module->file map
    module_to_file = {}
    for mname, mfile in (modules or []):
        module_to_file[mname] = mfile

    # Determine primary top candidate and refine if it looks peripheral-like (AXI/memory/fabric)
    primary_top = candidates[0] if candidates else None
    if primary_top and (
        _is_peripheral_like_name(primary_top)
        or _is_functional_unit_name(primary_top)
        or _is_micro_stage_name(primary_top)
        or _is_interface_module_name(primary_top)
    ):
        refined = _find_cpu_core_in_soc(primary_top, module_graph, modules)
        if refined and refined != primary_top:
            print_yellow(f"[TOP] Refined top from peripheral-like '{primary_top}' to CPU core '{refined}'")
            primary_top = refined
        else:
            # Fallback to first non-peripheral and non-functional candidate if available
            non_periph_cands = [
                c for c in candidates
                if not _is_peripheral_like_name(c)
                and not _is_functional_unit_name(c)
                and not _is_micro_stage_name(c)
                and not _is_interface_module_name(c)
            ]
            if non_periph_cands:
                print_yellow(f"[TOP] Swapping peripheral-like top '{candidates[0]}' to '{non_periph_cands[0]}'")
                primary_top = non_periph_cands[0]
            else:
                # As a last attempt, strongly prefer modules containing 'core', 'cpu', or repo name tokens
                prefer_terms = ["core", "cpu", "processor", (repo_name or "").lower()]
                strong_cands = [c for c in candidates if any(t and t in c.lower() for t in prefer_terms)]
                if strong_cands:
                    print_yellow(f"[TOP] Fallback to strong core-like candidate '{strong_cands[0]}'")
                    primary_top = strong_cands[0]

    # Reorder candidates to ensure primary_top is first
    if primary_top and candidates:
        candidates = [primary_top] + [c for c in candidates if c != primary_top]

    # Determine file extension of the chosen primary top
    primary_ext = None
    if primary_top and primary_top in module_to_file:
        try:
            primary_ext = os.path.splitext(module_to_file[primary_top])[1].lower()
        except Exception:
            primary_ext = None

    # Split files and candidates by language
    verilog_exts = {'.v', '.sv', '.vh', '.svh'}
    vhdl_exts = {'.vhd', '.vhdl'}
    verilog_files = [f for f in candidate_files if os.path.splitext(f)[1].lower() in verilog_exts]
    vhdl_files = [f for f in candidate_files if os.path.splitext(f)[1].lower() in vhdl_exts]
    tb_verilog = [f for f in tb_files if os.path.splitext(f)[1].lower() in verilog_exts]
    tb_vhdl = [f for f in tb_files if os.path.splitext(f)[1].lower() in vhdl_exts]


    verilog_candidates = [c for c in candidates if os.path.splitext(module_to_file.get(c, ''))[1].lower() in verilog_exts]
    vhdl_candidates = [c for c in candidates if os.path.splitext(module_to_file.get(c, ''))[1].lower() in vhdl_exts]


    # Filter out peripheral-like candidates if we still have others left; keep primary_top if it's the only option
    non_periph_verilog = [
        c for c in verilog_candidates
        if not _is_peripheral_like_name(c)
        and not _is_functional_unit_name(c)
        and not _is_micro_stage_name(c)
        and not _is_interface_module_name(c)
    ]
    if non_periph_verilog:
        # Preserve order and keep primary_top first when present
        if primary_top in non_periph_verilog:
            non_periph_verilog = [primary_top] + [c for c in non_periph_verilog if c != primary_top]
        verilog_candidates = non_periph_verilog

    non_periph_vhdl = [
        c for c in vhdl_candidates
        if not _is_peripheral_like_name(c)
        and not _is_functional_unit_name(c)
        and not _is_micro_stage_name(c)
        and not _is_interface_module_name(c)
    ]
    if non_periph_vhdl:
        if primary_top in non_periph_vhdl:
            non_periph_vhdl = [primary_top] + [c for c in non_periph_vhdl if c != primary_top]
        vhdl_candidates = non_periph_vhdl

    # Choose simulator based on the primary top candidate's file extension
    prefer_ghdl = False
    if primary_ext is not None:
        prefer_ghdl = primary_ext in vhdl_exts
    else:
        # Fallback: if majority of candidates are VHDL, prefer GHDL
        prefer_ghdl = len(vhdl_candidates) >= len(verilog_candidates)

    excluded_share = set()

    if prefer_ghdl and vhdl_candidates:
        print_green(f"[CORE] Selecting GHDL (VHDL) | top={primary_top} vhdl_candidates={len(vhdl_candidates)} files={len(vhdl_files)}")
        
        print_green(f"[CORE] Trying incremental bottom-up GHDL approach first...")
        is_simulable, last_log, final_files, top_module = ghdl_incremental(
            repo_root=repo_root,
            repo_name=repo_name,
            top_candidates=vhdl_candidates,
            modules=modules,
            ghdl_extra_flags=ghdl_extra_flags or ["-frelaxed"],
            timeout=240,
        )
        if is_simulable:
            print_green(f"[CORE] ✓ Incremental GHDL approach succeeded!")
            return final_files, set(), last_log, top_module, is_simulable
        else:
            print_yellow(f"[CORE] Incremental GHDL approach failed, returning failure...")
            return final_files, set(), last_log, top_module, is_simulable
        
        if is_simulable:
            return final_files, final_includes, last_log, top_module, is_simulable

    # Try Verilator if preferred path failed or primary is Verilog
    if verilog_candidates:
        print_green(f"[CORE] Selecting Verilator (Verilog/SV) | top={primary_top} verilog_candidates={len(verilog_candidates)} files={len(verilog_files)} includes={len(include_dirs)}")
        
        print_green(f"[CORE] Trying incremental bottom-up approach first...")
        final_files, final_includes, last_log, top_module, is_simulable = try_incremental_approach(
            repo_root=repo_root,
            repo_name=repo_name,
            top_candidates=verilog_candidates,
            modules=modules,
            module_graph=module_graph,
            language_version=language_version,
            verilator_extra_flags=verilator_extra_flags,
            timeout=240,
        )
        if is_simulable:
            print_green(f"[CORE] ✓ Incremental approach succeeded!")
            return final_files, final_includes, last_log, top_module, is_simulable
        else:
            print_yellow(f"[CORE] Incremental approach failed, returning failure...")
            return final_files, final_includes, last_log, top_module, is_simulable
        
        # Return empty result if incremental is disabled
        return [], set(), "", "", False

    # Final fallback: try GHDL if not yet tried or both lists empty
    if vhdl_candidates:
        print_yellow(f"[CORE] Fallback to GHDL (VHDL) after Verilator path | candidates={len(vhdl_candidates)}")
        
        print_green(f"[CORE] Trying fallback incremental GHDL approach...")
        is_simulable, last_log, final_files, top_module = ghdl_incremental(
            repo_root=repo_root,
            repo_name=repo_name,
            top_candidates=vhdl_candidates,
            modules=modules,
            ghdl_extra_flags=ghdl_extra_flags or ["-frelaxed"],
            timeout=240,
        )
        return final_files, set(), last_log, top_module, is_simulable
        
    # If we get here, nothing worked; return empty result
    return [], set(), "", "", False


def determine_language_version(extension: str, files: list = None, base_path: str = None) -> str:
    """
    Determines a starting language version based on file extension.
    The actual language will be detected per-file-set during incremental compilation.
    """
    # Return a reasonable default based on extension
    # The incremental compiler will do the actual detection on the selected files
    base_version = {
        '.vhdl': '08',
        '.vhd': '08', 
        '.sv': '1800-2017',    # SystemVerilog files default to SV
        '.svh': '1800-2017',   
        '.v': '1800-2017',     # .v files default to SV (will be downgraded if needed)
    }.get(extension, '1800-2017')
    
    return base_version


def create_output_json(
    repo_name,
    url,
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
        'sim_files': filtered_files,
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


def detect_and_run_config_script(repo_path: str, repo_name: str) -> bool:
    """
    Detects and runs configuration scripts that generate necessary defines/headers.
    
    Supports multiple patterns:
    - configs/*.config scripts (VeeR cores, etc.) - runs with no args or -target=default
    - configs/*.py scripts - runs with python3
    - configure scripts in root
    
    Returns:
        bool: True if a config script was found and run successfully
    """
    import subprocess
    
    # Pattern 1: configs directory with scripts
    config_dir = os.path.join(repo_path, 'configs')
    if os.path.isdir(config_dir):
        # Find config scripts (.config, .py, executable files)
        config_files = []
        for f in os.listdir(config_dir):
            full_path = os.path.join(config_dir, f)
            if f.endswith(('.config', '.py')) or (os.access(full_path, os.X_OK) and not f.startswith('.')):
                config_files.append(f)
        
        if config_files:
            # Use the first config file found
            config_file = config_files[0]
            config_script = os.path.join(config_dir, config_file)
            print_yellow(f"[CONFIG] Found configuration script: {config_script}")
            
            # Make script executable
            try:
                os.chmod(config_script, 0o755)
            except Exception:
                pass
            
            # Set up environment variables
            env = os.environ.copy()
            env['RV_ROOT'] = repo_path  # VeeR-specific
            env['ROOT'] = repo_path
            env['REPO_ROOT'] = repo_path
            
            # Determine command based on file type
            if config_file.endswith('.py'):
                base_cmd = ['python3', config_script]
            else:
                base_cmd = [config_script]
            
            # Try different argument patterns
            arg_patterns = [
                [],  # No arguments (most generic)
                ['-target=default'],  # VeeR-style
                ['--default'],  # Common default flag
            ]
            
            for args in arg_patterns:
                cmd = base_cmd + args
                cmd_str = ' '.join(cmd)
                print_yellow(f"[CONFIG] Attempting: {cmd_str}")
                
                try:
                    result = subprocess.run(
                        cmd,
                        cwd=repo_path,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        print_green(f"[CONFIG] ✓ Configuration script completed successfully")
                        return True
                    else:
                        error_msg = result.stderr if result.stderr else result.stdout
                        # Check for specific errors
                        if 'Can\'t locate' in error_msg or 'BEGIN failed' in error_msg:
                            print_yellow(f"[CONFIG] ⚠ Config script requires dependencies: {error_msg.split(chr(10))[0]}")
                            return False
                        elif 'usage:' in error_msg.lower() and args == []:
                            # Script requires arguments, try next pattern
                            continue
                        else:
                            # Other error, try next pattern
                            continue
                            
                except subprocess.TimeoutExpired:
                    print_yellow(f"[CONFIG] Config script timed out")
                    return False
                except Exception as e:
                    print_yellow(f"[CONFIG] Could not run config script: {str(e)}")
                    continue
            
            # If all patterns failed but script exists, that's okay - continue anyway
            print_yellow(f"[CONFIG] Config script found but could not determine correct arguments, continuing...")
            return False
    
    return False


def clone_and_validate_repo(url: str, repo_name: str) -> str:
    """Clones the repository and validates the operation."""
    destination_path = clone_repo(url, repo_name)
    if not destination_path:
        print_red('[ERROR] Não foi possível clonar o repositório.')
    else:
        print_green('[LOG] Repositório clonado com sucesso\n')
        
        # Convert to absolute path for config script
        abs_path = os.path.abspath(destination_path)
        
        # Try to detect and run config scripts
        detect_and_run_config_script(abs_path, repo_name)
        
    return destination_path


def find_and_log_files(destination_path: str) -> tuple:
    """Finds files with specific extensions in the repository and logs the result."""
    print_green('[LOG] Procurando arquivos com extensão .v, .sv, .vhdl, .vhd ou .scala\n')
    
    # First check for Scala/Chisel files
    scala_files = find_scala_files(destination_path)
    if scala_files:
        print_green(f'[LOG] Encontrados {len(scala_files)} arquivos Scala - projeto Chisel detectado\n')
        return scala_files, '.scala'
    
    # Otherwise, look for HDL files
    files, extension = find_files_with_extension(destination_path, ['v', 'sv', 'vhdl', 'vhd'])
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
    local_repo: str = None,
) -> dict:
    """
    Main function to generate a processor configuration.
    
    Args:
        url: Repository URL
        config_path: Path to save configuration
        plot_graph: Whether to plot dependency graphs
        add_to_config: Whether to add to central config
        no_llama: Skip OLLAMA processing
        model: OLLAMA model to use
        local_repo: Path to local repository (skips cloning if provided)
    """
    repo_name = extract_repo_name(url)
    
    # Use local repo if provided, otherwise clone
    if local_repo and os.path.exists(local_repo):
        destination_path = os.path.abspath(local_repo)
        print_green(f"[LOG] Using local repository: {destination_path}")
    else:
        destination_path = clone_and_validate_repo(url, repo_name)
        if not destination_path:
            return {}

    files, extension = find_and_log_files(destination_path)
    
    # Check if this is a Chisel project
    if extension == '.scala':
        print_green('[LOG] Processando projeto Chisel\n')
        config = process_chisel_project(destination_path, repo_name)
        
        if not config:
            print_red('[ERROR] Failed to process Chisel project')
            if not local_repo:
                remove_repo(repo_name)
            return {}
        
        # Add repository URL
        config['repository'] = url
        
        # Save configuration
        print_green('[LOG] Salvando configuração\n')
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        
        config_file = os.path.join(config_path, f"{repo_name}.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        
        if add_to_config:
            central_config_path = os.path.join(config_path, "config.json")
            save_config(central_config_path, config, repo_name)
        
        # Cleanup
        if not local_repo:
            print_green('[LOG] Removendo o repositório clonado\n')
            remove_repo(repo_name)
        else:
            print_green('[LOG] Mantendo repositório local (não foi clonado)\n')
        
        return config
    
    # Continue with HDL processing (existing code)
    modulename_list, modules = extract_and_log_modules(files, destination_path)

    tb_files, non_tb_files = categorize_files(files, repo_name, destination_path)
    # Exclude FPGA board wrapper trees from consideration to avoid picking board 'top' modules
    orig_tb, orig_non_tb = len(tb_files), len(non_tb_files)
    tb_files = [f for f in tb_files if not _is_fpga_path(f)]
    non_tb_files = [f for f in non_tb_files if not _is_fpga_path(f)]
    removed_tb = orig_tb - len(tb_files)
    removed_non_tb = orig_non_tb - len(non_tb_files)
    if removed_tb or removed_non_tb:
        print_yellow(f"[FILTER] Excluded FPGA paths -> tb:{removed_tb} non-tb:{removed_non_tb}")

    # Also filter modules originating from FPGA folders
    try:
        filtered_modules = []
        for mname, mfile in modules:
            rel = os.path.relpath(mfile, destination_path) if os.path.isabs(mfile) else mfile
            if not _is_fpga_path(rel):
                filtered_modules.append((mname, mfile))
        if len(filtered_modules) != len(modules):
            print_yellow(f"[FILTER] Excluded {len(modules) - len(filtered_modules)} module entries from FPGA paths")
        modules = filtered_modules
        # Keep modulename_list consistent for any downstream consumers
        modulename_list = [d for d in modulename_list if not _is_fpga_path(d.get('file', ''))]
    except Exception:
        pass
    include_dirs = find_and_log_include_dirs(destination_path)
    module_graph, module_graph_inverse = build_and_log_graphs(non_tb_files, modules, destination_path)
    filtered_files, top_module = process_files_with_llama(
        no_llama, non_tb_files, tb_files, modules, module_graph, repo_name, model,
    )
    language_version = determine_language_version(extension, filtered_files, destination_path)

    # Processor-specific Verilator flags
    verilator_flags = ['-Wno-lint', '-Wno-fatal', '-Wno-style', '-Wno-UNOPTFLAT', '-Wno-UNDRIVEN', '-Wno-UNUSED', '-Wno-TIMESCALEMOD', '-Wno-PROTECTED', '-Wno-MODDUP', '-Wno-REDEFMACRO', '-Wno-BLKANDNBLK', '-Wno-SYMRSVDWORD']
    
    # orv64: Define FPGA to use pre-synthesized .vm module implementations instead of missing DW IP
    if 'orv64' in repo_name.lower():
        verilator_flags.append('-DFPGA')

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
        verilator_extra_flags=verilator_flags,
        ghdl_extra_flags=['--std=08', '-frelaxed'],
    )

    # Convert absolute include directories to relative paths
    relative_include_dirs = []
    for include_dir in final_include_dirs:
        if os.path.isabs(include_dir):
            try:
                relative_path = os.path.relpath(include_dir, destination_path)
                relative_include_dirs.append(relative_path)
            except ValueError:
                # If we can't make it relative, use the original
                relative_include_dirs.append(include_dir)
        else:
            relative_include_dirs.append(include_dir)

    # Choose sim_files that match the selected simulator language
    verilog_exts = {'.v', '.sv', '.vh', '.svh'}
    vhdl_exts = {'.vhd', '.vhdl'}
    has_verilog = any(os.path.splitext(f)[1].lower() in verilog_exts for f in final_files)
    has_vhdl = any(os.path.splitext(f)[1].lower() in vhdl_exts for f in final_files)

    if has_verilog and not has_vhdl:
        sim_tb_files = [f for f in tb_files if os.path.splitext(f)[1].lower() in verilog_exts]
    elif has_vhdl and not has_verilog:
        sim_tb_files = [f for f in tb_files if os.path.splitext(f)[1].lower() in vhdl_exts]
    else:
        # Fallback: keep original testbenches if we can't infer a single language
        sim_tb_files = tb_files

    # Normalize recorded language_version to reflect final selected files and simulator behavior
    # Prefer the runner-emitted effective language if available
    language_version_out = language_version
    try:
        if last_log:
            m = re.search(r"\[LANG-EFFECTIVE\]\s+([0-9\-]+)\s+mode=(sv|verilog)", last_log)
            if m:
                language_version_out = m.group(1)
                print_green(f"[CONFIG] Using effective language from verilator: {language_version_out}")
            else:
                # Fallback to file-extension based inference only if no effective language found
                if any(os.path.splitext(f)[1].lower() in {'.sv', '.svh'} for f in final_files):
                    language_version_out = '1800-2017'
                elif any(os.path.splitext(f)[1].lower() == '.v' for f in final_files):
                    # Don't blindly assume .v = Verilog 2005, check if we detected SV earlier
                    if language_version.startswith('1800'):
                        language_version_out = language_version
                    else:
                        language_version_out = '1364-2005'
                else:
                    language_version_out = language_version  # VHDL or unknown
        else:
            # No log? Infer from selected files
            if any(os.path.splitext(f)[1].lower() in {'.sv', '.svh'} for f in final_files):
                language_version_out = '1800-2017'
            elif any(os.path.splitext(f)[1].lower() == '.v' for f in final_files):
                language_version_out = '1364-2005'
            else:
                language_version_out = language_version
    except Exception:
        # On any parsing/inference issue, keep previously detected version
        language_version_out = language_version

    output_json = create_output_json(
        repo_name, url, final_files, relative_include_dirs, top_module, language_version_out, is_simulable,
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

    # Save runner output log (lint/analyze/minimize transcript)
    print_green('[LOG] Salvando o log em logs/\n')
    if not os.path.exists('logs'):
        os.makedirs('logs')
    try:
        ts = f"{time.time():.0f}"
        with open(f'logs/{repo_name}_{ts}.log', 'w', encoding='utf-8') as log_file:
            # last_log may be large; write as plain text
            log_file.write(last_log or '')
    except Exception as e:
        print_yellow(f'[WARN] Falha ao salvar o log: {e}')

    # Cleanup - only remove if we cloned it (not using local repo)
    if not local_repo:
        print_green('[LOG] Removendo o repositório clonado\n')
        remove_repo(repo_name)
        print_green('[LOG] Repositório removido com sucesso\n')
    else:
        print_green('[LOG] Mantendo repositório local (não foi clonado)\n')

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
    parser.add_argument(
        '-l',
        '--local-repo',
        type=str,
        default=None,
        help='Path to local repository (skips cloning if provided)'
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
            args.local_repo,
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
