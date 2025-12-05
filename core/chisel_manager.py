"""
Chisel/SpinalHDL/Scala Manager Module

This module provides utilities for handling Chisel and SpinalHDL projects:
- Finding and parsing Scala files
- Extracting Module/Component definitions (class X extends Module/Component)
- Building dependency graphs from Module instantiations
- Identifying top-level modules
- Generating or modifying main App files
- Managing build.sbt configuration
- Running SBT to emit Verilog

Supported HDLs:
- Chisel 3.x (class X extends Module)
- SpinalHDL (class X extends Component)

Main functions:
- find_scala_files: Locates all Scala files in a directory
- extract_chisel_modules: Extracts Chisel Module and SpinalHDL Component definitions
- build_chisel_dependency_graph: Builds module instantiation graph
- find_top_module: Identifies the top-level module (not instantiated by others)
- generate_main_app: Creates or modifies main App to call top module
- configure_build_file: Ensures build file (build.sbt or build.sc) is properly configured
- emit_verilog: Runs SBT to generate Verilog output
"""

import os
import re
import glob
import json
from typing import List, Tuple, Dict, Set, Optional, Any
from collections import deque

# Helper constants and functions from config_generator.py
UTILITY_PATTERNS = (
    "gen_", "dff", "buf", "full_handshake", "fifo", "mux", "regfile"
)


def _is_peripheral_like_name(name: str) -> bool:
    """Heuristic check for peripheral/SoC fabric/memory module names."""
    n = (name or "").lower()
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
    """Heuristic for small functional units."""
    n = (name or "").lower()
    terms = [
        "multiplier", "divider", "div", "mul", "alu", "adder", "shifter", "barrel",
        "encoder", "decoder",
        "fpu", "fpdiv", "fpsqrt", "fadd", "fmul", "fdiv", "fsub", "fma", "fcmp", "fcvt",
        "cache", "icache", "dcache", "tlb",
        "btb", "branch", "predictor", "ras", "returnaddress", "rsb"
    ]
    for t in terms:
        if t in n:
            return True
    if ("_bp_" in n or n.endswith("_bp") or n.startswith("bp_pred") or "bpred" in n):
        if not any(x in n for x in ["core", "processor", "cpu", "unicore", "multicore"]):
            return True
    return False


def _is_micro_stage_name(name: str) -> bool:
    """Heuristic for pipeline stage blocks."""
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
    if "_rs_" in n or n.startswith("rs_") or n.endswith("_rs") or n == "rs":
        return True
    return any(t in n for t in terms)


def _is_interface_module_name(name: str) -> bool:
    """Return True for interface-like module names."""
    n = (name or "").lower()
    return n.endswith("if") or "interface" in n


def _ensure_mapping(mapping: Any) -> Dict[str, List[str]]:
    """Normalize a graph-like input into a dict: node -> list(children/parents)."""
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
    """Return number reachable distinct nodes (excluding start) from `start` using BFS."""
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


def find_scala_files(directory: str) -> List[str]:
    """Find all Scala files in the given directory.
    
    Args:
        directory (str): Root directory to search
        
    Returns:
        List[str]: List of absolute paths to Scala files
    """
    scala_files = []
    
    # Common directories to exclude (test directories, build artifacts, etc.)
    exclude_dirs = ['target', 'project/target', 'test', 'tests', '.git']
    
    for scala_file in glob.glob(f'{directory}/**/*.scala', recursive=True):
        # Skip files in excluded directories
        relative_path = os.path.relpath(scala_file, directory)
        if any(excl in relative_path for excl in exclude_dirs):
            continue
            
        # Skip broken symlinks
        if os.path.islink(scala_file) and not os.path.exists(scala_file):
            continue
            
        scala_files.append(os.path.abspath(scala_file))
    
    return scala_files


def extract_chisel_modules(scala_files: List[str]) -> List[Tuple[str, str]]:
    """Extract Chisel/SpinalHDL Module/Component definitions from Scala files.
    
    Looks for patterns like:
    Chisel:
    - class X extends Module
    - class X extends RawModule
    - class X extends LazyModule (Rocket Chip diplomacy)
    - class X(params) extends Module
    - object X extends Module
    
    SpinalHDL:
    - class X extends Component
    - class X(params) extends Component
    - object X extends Component
    
    Args:
        scala_files (List[str]): List of Scala file paths
        
    Returns:
        List[Tuple[str, str]]: List of (module_name, file_path) tuples
    """
    modules = []
    
    # Pattern to match Chisel module definitions and SpinalHDL Component definitions
    # Matches: class/object Name [generic params] [constructor params] extends Module/RawModule/LazyModule/Component
    module_pattern = re.compile(
        r'^\s*(?:class|object)\s+(\w+)(?:\[.*?\])?\s*(?:\(.*?\))?\s*extends\s+(?:(?:Raw)?Module|LazyModule|Component)\b',
        re.MULTILINE
    )
    
    # Also match classes that extend classes ending with "Base", "Core", "Module", "Tile" (likely module bases)
    # This catches cases like: class XSCore extends XSCoreBase
    base_class_pattern = re.compile(
        r'^\s*(?:class|object)\s+(\w+)(?:\[.*?\])?\s*(?:\(.*?\))?\s*extends\s+(\w+(?:Base|Core|Module|Tile|Top|Subsystem))\b',
        re.MULTILINE
    )
    
    for file_path in scala_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Remove block comments /* ... */
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Remove line comments // ...
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            
            # Find all module definitions (direct Module/LazyModule extensions)
            matches = module_pattern.findall(content)
            for module_name in matches:
                modules.append((module_name, file_path))
            
            # Also find classes extending base classes (indirect module extensions)
            base_matches = base_class_pattern.findall(content)
            for module_name, base_class in base_matches:
                # Only add if not already found (avoid duplicates)
                if not any(m[0] == module_name and m[1] == file_path for m in modules):
                    modules.append((module_name, file_path))
                
        except Exception as e:
            print(f"[WARNING] Error parsing {file_path}: {e}")
            continue
    
    return modules


def find_module_instantiations(file_path: str) -> Set[str]:
    """Find all Module instantiations in a Scala file.
    
    Looks for patterns like:
    - Module(new X)
    - Module(new X())
    - Module(new X(params))
    
    Args:
        file_path (str): Path to Scala file
        
    Returns:
        Set[str]: Set of instantiated module names
    """
    instantiations = set()
    
    # Pattern to match Module instantiations
    instantiation_pattern = re.compile(r'Module\s*\(\s*new\s+(\w+)(?:\(|[\s)])')
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Remove comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        
        # Find all instantiations
        matches = instantiation_pattern.findall(content)
        instantiations.update(matches)
        
    except Exception as e:
        print(f"[WARNING] Error analyzing {file_path}: {e}")
    
    return instantiations


def build_chisel_dependency_graph(
    modules: List[Tuple[str, str]]
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build dependency graph for Chisel modules.
    
    Args:
        modules (List[Tuple[str, str]]): List of (module_name, file_path) tuples
        
    Returns:
        Tuple[Dict, Dict]: (module_graph, module_graph_inverse)
            - module_graph: module_name -> list of instantiated modules
            - module_graph_inverse: module_name -> list of modules that instantiate it
    """
    module_graph = {}  # module -> list of modules it instantiates
    module_graph_inverse = {}  # module -> list of modules that instantiate it
    
    # Build module name to file mapping
    module_to_file = {}
    for module_name, file_path in modules:
        module_to_file[module_name] = file_path
    
    # Initialize graphs
    for module_name in module_to_file.keys():
        module_graph[module_name] = []
        module_graph_inverse[module_name] = []
    
    # Build dependency relationships
    for module_name, file_path in modules:
        instantiated_modules = find_module_instantiations(file_path)
        
        for inst_module in instantiated_modules:
            if inst_module in module_to_file:
                # module_name instantiates inst_module
                module_graph[module_name].append(inst_module)
                module_graph_inverse[inst_module].append(module_name)
    
    return module_graph, module_graph_inverse


def find_top_module(
    module_graph: Dict[str, List[str]],
    module_graph_inverse: Dict[str, List[str]],
    modules: List[Tuple[str, str]],
    repo_name: str = None
) -> Optional[str]:
    """Identify the top-level module using sophisticated scoring algorithm from config_generator.
    
    Uses the same comprehensive heuristics as the main Verilog/SystemVerilog ranking:
    - Repository name matching (highest priority)
    - Architectural indicators (CPU, core, processor)
    - Structural analysis (parent/child relationships)
    - Negative indicators (peripherals, test benches, utilities)
    
    Args:
        module_graph (Dict): module -> list of instantiated modules
        module_graph_inverse (Dict): module -> list of modules that instantiate it
        modules (List[Tuple[str, str]]): List of (module_name, file_path) tuples
        repo_name (str): Repository name for heuristic matching
        
    Returns:
        Optional[str]: Name of the top module, or None if not found
    """
    if not module_graph:
        print("[WARNING] Empty module graph")
        return None
    
    # Find zero-parent modules (top-level candidates)
    zero_parent_modules = [
        module for module in module_graph.keys()
        if not module_graph_inverse.get(module, [])
    ]
    
    # Find low-parent modules (1-2 instantiations - potential cores)
    low_parent_modules = [
        module for module in module_graph.keys()
        if len(module_graph_inverse.get(module, [])) in [1, 2]
    ]
    
    # Core/CPU modules with few parents
    core_cpu_modules = []
    for module in module_graph.keys():
        name_lower = module.lower()
        num_parents = len(module_graph_inverse.get(module, []))
        if num_parents <= 3 and any(pat in name_lower for pat in ['core', 'cpu', 'processor', 'riscv']):
            if not any(bad in name_lower for bad in ['test', 'tb', 'bench', 'periph', 'uart', 'spi', 'gpio']):
                core_cpu_modules.append(module)
    
    # Repository name matches
    repo_name_matches = []
    if repo_name:
        repo_lower = repo_name.lower().replace('-', '').replace('_', '')
        for module in module_graph.keys():
            name_lower = module.lower().replace('_', '')
            if repo_lower in name_lower or name_lower in repo_lower:
                repo_name_matches.append(module)
    
    # Combine candidates
    candidates = list(set(zero_parent_modules + low_parent_modules + core_cpu_modules + repo_name_matches))
    
    if not candidates:
        candidates = list(module_graph.keys())
    
    if not candidates:
        print("[WARNING] No valid candidates found")
        return None
    
    repo_lower = (repo_name or "").lower()
    scored = []
    
    # Normalize repo name
    repo_normalized = repo_lower.replace('-', '').replace('_', '')
    
    for c in candidates:
        reach = _reachable_size(module_graph, c)  # How many modules does this instantiate
        score = reach * 10  # Base score from connectivity
        name_lower = c.lower()
        name_normalized = name_lower.replace('_', '')
        
        # REPOSITORY NAME MATCHING (Highest Priority)
        if repo_normalized and len(repo_normalized) > 2 and c in module_graph:
            if repo_normalized == name_normalized:
                score += 50000
            elif repo_normalized in name_normalized:
                score += 40000
            elif name_normalized in repo_normalized:
                score += 35000
            else:
                # Initialism matching
                repo_words = repo_lower.replace('_', '-').split('-')
                if len(repo_words) >= 2:
                    initialism = ''.join(word[0] for word in repo_words if word)
                    if name_lower.startswith(initialism + '_'):
                        if any(x in name_lower for x in ['core', 'processor', 'cpu', 'unicore', 'multicore']):
                            score += 45000
                
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
        
        # SPECIAL CASE: "Top" module
        if name_lower == "top" and repo_lower:
            repo_name_exists = any(repo_lower == mod.lower() for mod in module_graph.keys())
            if not repo_name_exists:
                score += 48000
        
        # ARCHITECTURAL INDICATORS
        if any(term in name_lower for term in ["cpu", "processor"]):
            score += 2000
        if "microcontroller" in name_lower:
            score += 3000
        
        # CPU TOP MODULE DETECTION
        cpu_top_patterns = [
            f"{repo_lower}_top", f"top_{repo_lower}", f"{repo_lower}_cpu", f"cpu_{repo_lower}",
            "cpu_top", "core_top", "processor_top", "riscv_top", "risc_top"
        ]
        if repo_lower:
            cpu_top_patterns.extend([repo_lower, f"{repo_lower}_core", f"core_{repo_lower}"])
        
        for pattern in cpu_top_patterns:
            if name_lower == pattern:
                if not any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu"]):
                    score += 45000
                    break
        
        # DIRECT CORE NAME PATTERNS
        if name_lower == "core":
            score += 40000
        
        if repo_lower and name_lower == repo_lower:
            score += 25000
        
        # XSCore, XXXCore pattern - very strong signal
        if name_lower.endswith("core") and len(name_lower) <= 10:
            # This is likely "{Project}Core" pattern like XSCore, RocketCore, etc.
            score += 60000
        
        # Specific CPU core boost
        if "core" in name_lower and repo_lower:
            if any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu", "mem", "cache", "bus", "_ctrl", "ctrl_", "reg", "decode", "fetch", "exec", "forward", "hazard", "pred", "shift", "barrel", "adder", "mult", "divider", "encoder", "decoder"]):
                if "microcontroller" not in name_lower:
                    score -= 15000
            elif "subsys" in name_lower or "subsystem" in name_lower:
                score -= 8000
            elif name_lower == f"{repo_lower}_core" or name_lower == f"core_{repo_lower}":
                score += 25000
            elif name_lower.endswith("_core"):
                score += 20000
            elif repo_lower in name_lower and "core" in name_lower:
                score += 15000
        
        if "core" in name_lower:
            if any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu"]):
                score -= 10000
            elif not ("microcontroller" in name_lower) and any(unit in name_lower for unit in ["mem", "cache", "bus", "_ctrl", "ctrl_", "reg", "decode", "fetch", "exec", "forward", "hazard", "pred", "shift", "barrel", "adder", "mult", "divider", "encoder", "decoder"]):
                score -= 5000
            else:
                score += 1500
        
        if any(arch in name_lower for arch in ["riscv", "risc", "mips", "arm"]):
            score += 1000
        
        if name_lower.endswith("_top") or name_lower.startswith("top_"):
            score += 800
        
        # Penalize functional units
        if _is_functional_unit_name(name_lower):
            score -= 12000
        if _is_micro_stage_name(name_lower):
            score -= 40000
        if _is_interface_module_name(name_lower):
            score -= 12000
        
        # SOC penalty
        if "soc" in name_lower:
            score -= 5000
        
        # TileLink infrastructure penalty - these are bus/crossings, not cores
        if name_lower.startswith("tl") and any(pat in name_lower for pat in ["crossing", "async", "rational", "buffer", "width", "monitor", "fragmenter", "hint", "xbar", "arbiter"]):
            score -= 20000
        
        # Crypto/accelerator penalty - these are not CPU cores
        if any(pat in name_lower for pat in ["crypto", "aes", "sha", "rsa", "nist", "cipher"]):
            score -= 25000
        
        # Crossing/bridge penalty - infrastructure modules
        if any(pat in name_lower for pat in ["xing", "crossing", "mute", "rational"]) and "core" not in name_lower:
            score -= 20000
        
        # Source/sink node penalty - these are diplomacy infrastructure
        if any(pat in name_lower for pat in ["sourcenode", "sinknode", "tomodule", "tobundle"]):
            score -= 25000
        
        # STRUCTURAL HEURISTICS
        num_children = len(module_graph.get(c, []))
        num_parents = len(module_graph_inverse.get(c, []))
        
        is_likely_core = (num_parents >= 1 and num_parents <= 3 and 
                          any(pattern in name_lower for pattern in ['core', 'cpu', 'processor']) and
                          not any(bad in name_lower for bad in ['_top', 'top_', 'soc', 'system', 'wrapper']))
        
        if is_likely_core and num_children > 2:
            score += 25000
        elif num_children > 10 and num_parents == 0:
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
            score -= 5000
        
        if _is_peripheral_like_name(name_lower):
            score -= 15000
        
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
    
    # Sort by score (descending), then by reach, then by name
    scored.sort(reverse=True, key=lambda t: (t[0], t[1], t[2]))
    
    # Filter out micro-stage and interface modules
    ranked = [c for score, _, c in scored if score > -5000]
    filtered_ranked = [c for c in ranked if not _is_micro_stage_name(c.lower()) and not _is_interface_module_name(c.lower())]
    if filtered_ranked:
        ranked = filtered_ranked
    
    if not ranked:
        print("[WARNING] No valid top module after filtering")
        return None
    
    top_module = ranked[0]
    top_score = scored[0][0]
    print(f"[INFO] Selected top module: {top_module} (score: {top_score})")
    print(f"[INFO] Top 5 candidates: {[f'{c} ({s})' for s, _, c in scored[:5]]}")
    
    return top_module


def find_all_main_apps(
    directory: str,
    top_module: str,
    hdl_type: str = 'chisel',
    repo_name: str = None
) -> List[Tuple[int, str, str, str, str]]:
    """Find ALL existing main Apps that can generate Verilog, sorted by score.
    
    Returns all candidates sorted by score (highest first), including ones with
    negative scores. This allows trying multiple Apps in order until one works.
    
    Returns:
        List[Tuple[int, str, str, str, str]]: List of (score, file_path, main_class, app_name, instantiated_module)
    """
    scala_files = find_scala_files(directory)
    
    candidates = []
    
    # Normalize repo name for matching
    repo_lower = (repo_name or "").lower().replace('-', '').replace('_', '')
    
    # Look for App objects - can instantiate any module, not just top_module
    for scala_file in scala_files:
        try:
            with open(scala_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Don't filter by top_module - look for ANY App that generates Verilog
            # We'll prioritize ones that reference the top module in scoring
            
            # Try to find object with main method or extends App
            app_match = re.search(r'object\s+(\w+)\s+extends\s+App', content)
            main_method_match = re.search(r'object\s+(\w+)\s*\{[^}]*def\s+main\s*\(\s*args\s*:\s*Array\[String\]\s*\)', content, re.DOTALL)
            
            if not app_match and not main_method_match:
                continue
            
            if app_match:
                app_name = app_match.group(1)
                requires_args = False  # extends App typically doesn't require args
            elif main_method_match:
                app_name = main_method_match.group(1)
                # Check if the main method accesses args - search more content (2000 chars)
                main_start = main_method_match.end()
                requires_args = bool(re.search(r'args\s*[\(\.\[]', content[main_start:main_start+2000]))
            else:
                continue
            
            # For SpinalHDL, look for SpinalVerilog or SpinalConfig
            if hdl_type == 'spinalhdl':
                if 'SpinalVerilog' in content or 'SpinalConfig' in content:
                    # Look for module instantiation - prioritize patterns near SpinalVerilog/SpinalConfig
                    # Pattern 1: SpinalVerilog{ new Module }
                    spinal_block_pattern = re.search(r'Spinal(?:Verilog|Config)[^\{]*\{[^\{]*?new\s+(\w+)\s*[(\[]', content, re.DOTALL)
                    
                    # Pattern 2: val x = new Module inside Spinal block (look for it later in the file)
                    # Find all "new Module(" after any Spinal call
                    spinal_pos = content.find('Spinal')
                    if spinal_pos > 0:
                        after_spinal = content[spinal_pos:]
                        val_pattern = re.search(r'val\s+\w+\s*=\s*new\s+(\w+)\s*[(\[]', after_spinal)
                        if val_pattern:
                            instantiated_module = val_pattern.group(1)
                        elif spinal_block_pattern:
                            instantiated_module = spinal_block_pattern.group(1)
                        else:
                            # Fallback: look for any "new" after Spinal, but skip plugins/configs
                            all_news = re.findall(r'new\s+(\w+)\s*[(\[]', after_spinal)
                            # Filter out common plugin/config names
                            plugin_names = ['IBusSimplePlugin', 'DBusSimplePlugin', 'IBusCachedPlugin', 'DBusCachedPlugin',
                                          'DecoderSimplePlugin', 'RegFilePlugin', 'IntAluPlugin', 'SrcPlugin',
                                          'FullBarrelShifterPlugin', 'MulPlugin', 'DivPlugin', 'HazardSimplePlugin',
                                          'DebugPlugin', 'BranchPlugin', 'CsrPlugin', 'YamlPlugin',
                                          'DataCacheConfig', 'InstructionCacheConfig', 'CsrPluginConfig',
                                          'StaticMemoryTranslatorPlugin', 'MemoryTranslatorPortConfig']
                            
                            for module_name in all_news:
                                if module_name not in plugin_names and not module_name.endswith('Config'):
                                    instantiated_module = module_name
                                    break
                            else:
                                # No valid module found
                                continue
                    elif spinal_block_pattern:
                        instantiated_module = spinal_block_pattern.group(1)
                    else:
                        # Fallback to first "new" in file
                        module_instantiation = re.search(r'new\s+(\w+)\s*[(\[]', content)
                        if not module_instantiation:
                            continue
                        instantiated_module = module_instantiation.group(1)
                    
                    # Get package name
                    package = get_module_package(scala_file)
                    if package:
                        main_class = f"{package}.{app_name}"
                    else:
                        main_class = app_name
                    
                    # Calculate score based on filename, content, and heuristics
                    score = 0
                    
                    # CRITICAL: Apps that require arguments cannot be run without them
                    if requires_args:
                        score -= 50000  # Heavy penalty - basically disqualifies it
                    
                    # IMPORTANT: Boost if it instantiates the top_module we identified
                    if instantiated_module == top_module:
                        score += 30000
                    
                    filename_lower = os.path.basename(scala_file).lower()
                    app_name_lower = app_name.lower()
                    content_lower = content.lower()
                    instantiated_module_lower = instantiated_module.lower()
                    
                    # CRITICAL: Heavily penalize peripheral/memory/testbench modules
                    peripheral_names = ['uart', 'gpio', 'spi', 'i2c', 'timer', 'dma', 'plic', 'clint', 
                                       'memory', 'mem', 'ram', 'rom', 'cache', 'bram']
                    if any(periph in instantiated_module_lower for periph in peripheral_names):
                        score -= 20000
                    
                    # CRITICAL: Penalize "Sim" Apps (they require simulations/arguments)
                    if app_name_lower.endswith('sim'):
                        score -= 15000
                    
                    # HIGHEST PRIORITY: Apps ending in "Verilog" are simple generators
                    if app_name_lower.endswith('verilog'):
                        score += 15000
                    
                    # HIGHEST PRIORITY: Core-related Apps
                    if 'core' in app_name_lower or 'core' in instantiated_module_lower:
                        score += 12000
                    
                    # HIGHEST PRIORITY: Exact repository name match
                    if repo_lower and len(repo_lower) > 2:
                        filename_normalized = filename_lower.replace('_', '').replace('.scala', '')
                        app_normalized = app_name_lower.replace('_', '')
                        
                        if repo_lower == filename_normalized or repo_lower == app_normalized:
                            score += 10000
                        elif repo_lower in filename_normalized or repo_lower in app_normalized:
                            score += 8000
                    
                    # HIGHEST PRIORITY: Wishbone bus (THE BEST simulation interface)
                    if 'wishbone' in filename_lower or 'wishbone' in app_name_lower:
                        score += 20000
                    if 'wb' in filename_lower or '_wb' in app_name_lower or 'wb_' in app_name_lower:
                        # Only boost for wb if it's clearly "wishbone" context
                        if 'wishbone' in content_lower:
                            score += 15000
                    
                    # HIGH PRIORITY: Cached versions (better for simulation)
                    if 'cached' in filename_lower or 'cached' in app_name_lower:
                        score += 2500
                    
                    # MEDIUM PRIORITY: Top module name in filename
                    if top_module.lower() in filename_lower:
                        score += 2000
                    
                    # MEDIUM PRIORITY: Simple/minimal configuration (core-only, no complex SoC)
                    # Penalize files with many SoC peripherals
                    soc_indicators = ['uart', 'gpio', 'timer', 'spi', 'i2c', 'plic', 'clint', 'jtag']
                    soc_count = sum(1 for indicator in soc_indicators if indicator in content_lower)
                    
                    if soc_count == 0:
                        # No peripherals - likely core-only
                        score += 1500
                    elif soc_count <= 2:
                        # Few peripherals - minimal SoC
                        score += 500
                    else:
                        # Many peripherals - full SoC (penalize)
                        score -= 2000
                    
                    # Check if it's a minimal config (just core + bus interface)
                    if 'ibus' in content_lower and 'dbus' in content_lower:
                        # Has instruction and data bus - good sign
                        score += 1000
                    
                    # NEGATIVE: Demo/example files (usually too complex)
                    if 'demo' in filename_lower or 'example' in filename_lower:
                        score -= 1000
                    
                    # NEGATIVE: Briey, Murax, etc (known full SoC implementations)
                    known_socs = ['briey', 'murax', 'saxon', 'litex']
                    if any(soc in filename_lower or soc in app_name_lower for soc in known_socs):
                        score -= 3000
                    
                    # Boost based on references to instantiated module
                    score += content.count(instantiated_module) * 10
                    
                    candidates.append((score, scala_file, main_class, app_name, instantiated_module))
            
            # For Chisel, look for ChiselStage or emitVerilog
            elif hdl_type == 'chisel':
                if 'ChiselStage' in content or 'emitVerilog' in content:
                    # Look for ANY module instantiation
                    module_instantiation = re.search(r'new\s+(\w+)\s*[(\[]', content)
                    if not module_instantiation:
                        continue
                    
                    instantiated_module = module_instantiation.group(1)
                    
                    package = get_module_package(scala_file)
                    if package:
                        main_class = f"{package}.{app_name}"
                    else:
                        main_class = app_name
                    
                    score = 0
                    
                    # CRITICAL: Apps that require arguments cannot be run without them
                    if requires_args:
                        score -= 50000  # Heavy penalty - basically disqualifies it
                    
                    # IMPORTANT: Boost if it instantiates the top_module we identified
                    if instantiated_module == top_module:
                        score += 5000
                    
                    filename_lower = os.path.basename(scala_file).lower()
                    app_name_lower = app_name.lower()
                    
                    # Repository name match
                    if repo_lower and len(repo_lower) > 2:
                        filename_normalized = filename_lower.replace('_', '').replace('.scala', '')
                        if repo_lower == filename_normalized or repo_lower == app_name_lower:
                            score += 10000
                        elif repo_lower in filename_normalized or repo_lower in app_name_lower:
                            score += 8000
                    
                    # Top module name match
                    if top_module.lower() in filename_lower:
                        score += 2000
                    
                    score += content.count(instantiated_module) * 10
                    
                    candidates.append((score, scala_file, main_class, app_name, instantiated_module))
                    
        except Exception as e:
            continue
    
    if not candidates:
        return []
    
    # Sort by score (highest first) but return ALL candidates
    candidates.sort(reverse=True, key=lambda x: x[0])
    
    print(f"[INFO] Found {len(candidates)} App candidates:")
    for idx, (score, file, main_class, app_name, inst_module) in enumerate(candidates[:10]):  # Show top 10
        print(f"  {idx+1}. {app_name} -> {inst_module} (score: {score})")
    
    return candidates


def find_existing_main_app(directory: str, top_module: str, hdl_type: str = 'chisel', repo_name: str = None) -> Optional[Tuple[str, str, str]]:
    """Find existing main App file that instantiates any module.
    
    Searches for:
    - Chisel: object X extends App with ChiselStage or emitVerilog
    - SpinalHDL: object X extends App with SpinalVerilog or SpinalConfig
    - SpinalHDL: object X with def main(args: Array[String])
    
    Prioritizes Apps that:
    1. Don't require command-line arguments (heavily penalized otherwise)
    2. Match repository name (highest priority)
    3. Contain "wishbone" (common bus interface)
    4. Appear to be core-only (minimal SoC peripherals)
    5. Are marked as "ForSim" or similar
    
    Args:
        directory (str): Root directory to search
        top_module (str): Name of the top module (used for prioritization)
        hdl_type (str): 'chisel' or 'spinalhdl'
        repo_name (str): Repository name for matching
        
    Returns:
        Optional[Tuple[str, str, str]]: (file_path, main_class_name, instantiated_module) or None
    """
    scala_files = find_scala_files(directory)
    
    candidates = []
    
    # Normalize repo name for matching
    repo_lower = (repo_name or "").lower().replace('-', '').replace('_', '')
    
    # Look for App objects - can instantiate any module, not just top_module
    for scala_file in scala_files:
        try:
            with open(scala_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Don't filter by top_module - look for ANY App that generates Verilog
            # We'll prioritize ones that reference the top module in scoring
            
            # Try to find object with main method or extends App
            app_match = re.search(r'object\s+(\w+)\s+extends\s+App', content)
            main_method_match = re.search(r'object\s+(\w+)\s*\{[^}]*def\s+main\s*\(\s*args\s*:\s*Array\[String\]\s*\)', content, re.DOTALL)
            
            if not app_match and not main_method_match:
                continue
            
            if app_match:
                app_name = app_match.group(1)
                requires_args = False  # extends App typically doesn't require args
            elif main_method_match:
                app_name = main_method_match.group(1)
                # Check if the main method accesses args
                # Look for args( or args. in the rest of the file
                main_start = main_method_match.end()
                # Search a larger portion to catch args usage (comments can delay it)
                remaining_content = content[main_start:main_start+2000]
                requires_args = bool(re.search(r'args\s*[\(\.\[]', remaining_content))
            else:
                continue
            
            # For SpinalHDL, look for SpinalVerilog or SpinalConfig
            if hdl_type == 'spinalhdl':
                if 'SpinalVerilog' in content or 'SpinalConfig' in content:
                    # Look for ANY module instantiation pattern: new ModuleName(
                    module_instantiation = re.search(r'new\s+(\w+)\s*[(\[]', content)
                    if not module_instantiation:
                        continue
                    
                    instantiated_module = module_instantiation.group(1)
                    
                    # Get package name
                    package = get_module_package(scala_file)
                    if package:
                        main_class = f"{package}.{app_name}"
                    else:
                        main_class = app_name
                    
                    # Calculate score based on filename, content, and heuristics
                    score = 0
                    
                    # CRITICAL: Apps that require arguments cannot be run without them
                    if requires_args:
                        score -= 50000  # Heavy penalty - basically disqualifies it
                    
                    # IMPORTANT: Boost if it instantiates the top_module we identified
                    if instantiated_module == top_module:
                        score += 5000
                    
                    filename_lower = os.path.basename(scala_file).lower()
                    app_name_lower = app_name.lower()
                    content_lower = content.lower()
                    
                    # HIGHEST PRIORITY: Exact repository name match
                    if repo_lower and len(repo_lower) > 2:
                        filename_normalized = filename_lower.replace('_', '').replace('.scala', '')
                        app_normalized = app_name_lower.replace('_', '')
                        
                        if repo_lower == filename_normalized or repo_lower == app_normalized:
                            score += 10000
                        elif repo_lower in filename_normalized or repo_lower in app_normalized:
                            score += 8000
                    
                    # HIGH PRIORITY: Wishbone bus (common simulation interface)
                    if 'wishbone' in filename_lower or 'wishbone' in app_name_lower:
                        score += 5000
                    if 'wb' in filename_lower or '_wb' in app_name_lower or 'wb_' in app_name_lower:
                        # Only boost for wb if it's clearly "wishbone" context
                        if 'wishbone' in content_lower:
                            score += 4000
                    
                    # HIGH PRIORITY: Simulation-specific (ForSim, Sim, Testbench)
                    if 'forsim' in app_name_lower or 'sim' in app_name_lower:
                        score += 3000
                    
                    # HIGH PRIORITY: Cached versions (better for simulation)
                    if 'cached' in filename_lower or 'cached' in app_name_lower:
                        score += 2500
                    
                    # MEDIUM PRIORITY: Top module name in filename
                    if top_module.lower() in filename_lower:
                        score += 2000
                    
                    # MEDIUM PRIORITY: Simple/minimal configuration (core-only, no complex SoC)
                    # Penalize files with many SoC peripherals
                    soc_indicators = ['uart', 'gpio', 'timer', 'spi', 'i2c', 'plic', 'clint', 'jtag']
                    soc_count = sum(1 for indicator in soc_indicators if indicator in content_lower)
                    
                    if soc_count == 0:
                        # No peripherals - likely core-only
                        score += 1500
                    elif soc_count <= 2:
                        # Few peripherals - minimal SoC
                        score += 500
                    else:
                        # Many peripherals - full SoC (penalize)
                        score -= 2000
                    
                    # Check if it's a minimal config (just core + bus interface)
                    if 'ibus' in content_lower and 'dbus' in content_lower:
                        # Has instruction and data bus - good sign
                        score += 1000
                    
                    # NEGATIVE: Demo/example files (usually too complex)
                    if 'demo' in filename_lower or 'example' in filename_lower:
                        score -= 1000
                    
                    # NEGATIVE: Briey, Murax, etc (known full SoC implementations)
                    known_socs = ['briey', 'murax', 'saxon', 'litex']
                    if any(soc in filename_lower or soc in app_name_lower for soc in known_socs):
                        score -= 3000
                    
                    # Boost based on references to instantiated module
                    score += content.count(instantiated_module) * 10
                    
                    candidates.append((score, scala_file, main_class, app_name, instantiated_module))
            
            # For Chisel, look for ChiselStage or emitVerilog
            elif hdl_type == 'chisel':
                if 'ChiselStage' in content or 'emitVerilog' in content:
                    # Look for ANY module instantiation
                    module_instantiation = re.search(r'new\s+(\w+)\s*[(\[]', content)
                    if not module_instantiation:
                        continue
                    
                    instantiated_module = module_instantiation.group(1)
                    
                    package = get_module_package(scala_file)
                    if package:
                        main_class = f"{package}.{app_name}"
                    else:
                        main_class = app_name
                    
                    score = 0
                    
                    # CRITICAL: Apps that require arguments cannot be run without them
                    if requires_args:
                        score -= 50000  # Heavy penalty - basically disqualifies it
                    
                    # IMPORTANT: Boost if it instantiates the top_module we identified
                    if instantiated_module == top_module:
                        score += 5000
                    
                    filename_lower = os.path.basename(scala_file).lower()
                    app_name_lower = app_name.lower()
                    
                    # Repository name match
                    if repo_lower and len(repo_lower) > 2:
                        filename_normalized = filename_lower.replace('_', '').replace('.scala', '')
                        if repo_lower == filename_normalized or repo_lower == app_name_lower:
                            score += 10000
                        elif repo_lower in filename_normalized or repo_lower in app_name_lower:
                            score += 8000
                    
                    # Top module name match
                    if top_module.lower() in filename_lower:
                        score += 2000
                    
                    score += content.count(instantiated_module) * 10
                    
                    candidates.append((score, scala_file, main_class, app_name, instantiated_module))
                    
        except Exception as e:
            continue
    
    if not candidates:
        return None
    
    # Sort by score and return the best match
    candidates.sort(reverse=True, key=lambda x: x[0])
    best_match = candidates[0]
    
    # If the best candidate requires arguments (negative score), try to find one without
    if best_match[0] < 0:
        print(f"[WARNING] Best App candidate requires arguments (score: {best_match[0]})")
        print(f"[WARNING] Looking for Apps that don't require arguments...")
        # Look for any candidate with positive score
        for candidate in candidates:
            if candidate[0] > 0:
                best_match = candidate
                print(f"[INFO] Found alternative App without arguments: {candidate[3]} (score: {candidate[0]})")
                break
        else:
            # No candidates with positive score - return None to generate our own
            print(f"[WARNING] All App candidates require arguments - will generate new main App")
            return None
    
    print(f"[INFO] Found existing main App: {best_match[1]}")
    print(f"[INFO] Main class: {best_match[2]}")
    print(f"[INFO] App name: {best_match[3]} (score: {best_match[0]})")
    print(f"[INFO] Instantiates module: {best_match[4]}")
    
    # Show top candidates for debugging
    if len(candidates) > 1:
        print(f"[INFO] Other candidates:")
        for score, file, main_class, app_name, inst_module in candidates[1:min(5, len(candidates))]:
            print(f"  - {app_name} -> {inst_module} ({os.path.basename(file)}) - score: {score}")
    
    # Return file, main_class, and instantiated_module
    return best_match[1], best_match[2], best_match[4]


def get_module_package(file_path: str) -> Optional[str]:
    """Extract package name from a Scala file.
    
    Args:
        file_path (str): Path to Scala file
        
    Returns:
        Optional[str]: Package name, or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find package declaration
        package_match = re.search(r'^\s*package\s+([\w.]+)', content, re.MULTILINE)
        if package_match:
            return package_match.group(1)
    except Exception:
        pass
    
    return None


def detect_hdl_type(directory: str, build_sbt_path: str = None) -> str:
    """Detect whether the project uses Chisel or SpinalHDL.
    
    Args:
        directory (str): Root directory of the project
        build_sbt_path (str): Optional path to build.sbt
        
    Returns:
        str: Either 'chisel' or 'spinalhdl'
    """
    # First check build.sbt if provided
    if build_sbt_path and os.path.exists(build_sbt_path):
        try:
            with open(build_sbt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for SpinalHDL dependencies
            if 'spinalhdl-core' in content or 'spinalhdl-lib' in content:
                return 'spinalhdl'
            
            # Check for Chisel dependencies
            if 'chisel3' in content or '"chisel"' in content:
                return 'chisel'
        except Exception:
            pass
    
    # Search all build.sbt files if not found
    build_sbt_files = glob.glob(f'{directory}/**/build.sbt', recursive=True)
    for build_file in build_sbt_files:
        try:
            with open(build_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'spinalhdl-core' in content or 'spinalhdl-lib' in content:
                return 'spinalhdl'
            
            if 'chisel3' in content or '"chisel"' in content:
                return 'chisel'
        except Exception:
            pass
    
    # Default to chisel if can't determine
    print("[WARNING] Could not determine HDL type from build.sbt, defaulting to Chisel")
    return 'chisel'


def generate_main_app(
    directory: str,
    top_module: str,
    modules: List[Tuple[str, str]] = None,
    hdl_type: str = 'chisel'
) -> str:
    """Generate or modify main App file to call the top module.
    
    Tries to place the main App in an appropriate location:
    1. If top module has a package, use that package
    2. If there's an existing src/main/scala structure, use it
    3. Otherwise create in a 'generated' package
    
    Args:
        directory (str): Root directory of the project
        top_module (str): Name of the top module to instantiate
        modules (List[Tuple[str, str]]): Optional list of (module_name, file_path)
        hdl_type (str): Either 'chisel' or 'spinalhdl'
        
    Returns:
        str: Path to the generated main App file
    """
    # Check if main App already exists
    existing_app = find_existing_main_app(directory, top_module)
    if existing_app:
        # Return just the file path (generate_main_app doesn't need the rest)
        app_path = existing_app[0] if isinstance(existing_app, tuple) else existing_app
        print(f"[INFO] Found existing main App: {app_path}")
        return app_path
    
    # Determine package name and location
    package_name = "generated"
    base_src_dir = os.path.join(directory, 'src', 'main', 'scala')
    top_module_package = None
    
    # If we know where the top module is, try to use its package
    if modules:
        module_to_file = {name: path for name, path in modules}
        if top_module in module_to_file:
            top_module_file = module_to_file[top_module]
            top_module_package = get_module_package(top_module_file)
            
            if top_module_package:
                package_name = top_module_package
                print(f"[INFO] Using top module's package: {package_name}")
                
                # Find the base src/main/scala directory by walking up from module file
                current = os.path.dirname(top_module_file)
                while current.startswith(directory):
                    if current.endswith(os.path.join('src', 'main', 'scala')):
                        base_src_dir = current
                        break
                    parent = os.path.dirname(current)
                    if parent == current:
                        break
                    current = parent
    
    # Create directory structure
    package_path = package_name.replace('.', os.sep)
    main_dir = os.path.join(base_src_dir, package_path)
    os.makedirs(main_dir, exist_ok=True)
    
    # Generate main App file
    app_file = os.path.join(main_dir, 'GenerateVerilog.scala')
    
    # Generate appropriate content based on HDL type
    if hdl_type == 'spinalhdl':
        # SpinalHDL version
        import_statement = ""
        if top_module_package and package_name != top_module_package:
            import_statement = f"\nimport {top_module_package}.{top_module}"
        
        app_content = f"""package {package_name}

import spinal.core._
import spinal.core.sim._
{import_statement}

object GenerateVerilog extends App {{
  // Generate Verilog for the top module: {top_module}
  SpinalConfig(
    targetDirectory = "generated"
  ).generateVerilog(new {top_module}())
}}
"""
    else:
        # Chisel version
        import_statement = ""
        if package_name != "generated":
            # If using the same package as top module, no import needed
            # But we'll include it anyway for clarity
            import_statement = f"\n// Top module is in package {package_name}"
        
        app_content = f"""package {package_name}

import chisel3._
import chisel3.stage.{{ChiselStage, ChiselGeneratorAnnotation}}{import_statement}

object GenerateVerilog extends App {{
  // Generate Verilog for the top module: {top_module}
  (new ChiselStage).execute(
    Array("--target-dir", "generated"),
    Seq(ChiselGeneratorAnnotation(() => new {top_module}()))
  )
}}
"""
    
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(app_content)
    
    print(f"[INFO] Generated main App: {app_file}")
    print(f"[INFO] HDL type: {hdl_type}")
    print(f"[INFO] Package: {package_name}")
    return app_file


def find_build_file(directory: str, top_module: str = None, modules: List[Tuple[str, str]] = None) -> Optional[Tuple[str, str]]:
    """Find build file (build.sbt or build.sc) in the project.
    
    Supports both SBT and Mill build systems.
    
    Args:
        directory (str): Root directory of the project
        top_module (str): Optional top module name to search for
        modules (List[Tuple[str, str]]): Optional list of (module_name, file_path) to locate top module
        
    Returns:
        Optional[Tuple[str, str]]: Tuple of (build_file_path, build_tool) where build_tool is 'sbt' or 'mill'
    """
    # First check for Mill (build.sc)
    mill_files = glob.glob(f'{directory}/**/build.sc', recursive=True)
    
    # Then check for SBT (build.sbt)
    sbt_files = glob.glob(f'{directory}/**/build.sbt', recursive=True)
    
    # Prefer root-level build files
    root_mill = os.path.join(directory, 'build.sc')
    root_sbt = os.path.join(directory, 'build.sbt')
    
    # Strategy 1: Check for Mill first (simpler, newer)
    if os.path.exists(root_mill):
        print(f"[INFO] Found Mill build file: {root_mill}")
        return (root_mill, 'mill')
    
    if mill_files:
        print(f"[INFO] Found Mill build file: {mill_files[0]}")
        return (mill_files[0], 'mill')
    
    # Strategy 2: Look for SBT
    if os.path.exists(root_sbt):
        print(f"[INFO] Found SBT build file: {root_sbt}")
        return (root_sbt, 'sbt')
    
    # Strategy 3: If we know the top module location, find nearest build file
    if top_module and modules:
        module_to_file = {name: path for name, path in modules}
        if top_module in module_to_file:
            top_module_file = module_to_file[top_module]
            
            # Walk up from the module file to find build.sbt or build.sc
            current_dir = os.path.dirname(top_module_file)
            while current_dir.startswith(directory):
                candidate_mill = os.path.join(current_dir, 'build.sc')
                candidate_sbt = os.path.join(current_dir, 'build.sbt')
                
                if os.path.exists(candidate_mill):
                    print(f"[INFO] Found build.sc near top module: {candidate_mill}")
                    return (candidate_mill, 'mill')
                
                if os.path.exists(candidate_sbt):
                    print(f"[INFO] Found build.sbt near top module: {candidate_sbt}")
                    return (candidate_sbt, 'sbt')
                
                # Move up one directory
                parent_dir = os.path.dirname(current_dir)
                if parent_dir == current_dir:  # Reached root
                    break
                current_dir = parent_dir
    
    # Strategy 4: Multiple build files - analyze them
    if sbt_files:
        if len(sbt_files) == 1:
            return (sbt_files[0], 'sbt')
        
        print(f"[INFO] Found {len(sbt_files)} build.sbt files")
        
        # If top module is specified, search for it in build files
        if top_module:
            for build_file in sbt_files:
                try:
                    with open(build_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if top_module in content:
                            print(f"[INFO] Found build.sbt referencing top module: {build_file}")
                            return (build_file, 'sbt')
                except Exception:
                    continue
        
        # Prefer build.sbt with Chisel dependencies
        for build_file in sbt_files:
            try:
                with open(build_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'chisel' in content.lower():
                        print(f"[INFO] Found build.sbt with Chisel dependencies: {build_file}")
                        return (build_file, 'sbt')
            except Exception:
                continue
        
        # Fallback: return the first one found
        print(f"[INFO] Using first build.sbt found: {sbt_files[0]}")
        return (sbt_files[0], 'sbt')
    
    return None


def configure_build_file(directory: str, top_module: str = None, modules: List[Tuple[str, str]] = None) -> Tuple[str, str]:
    """Ensure build file (build.sbt or build.sc) is properly configured for Verilog generation.
    
    In multi-module projects, finds the build file that corresponds to the top module.
    If no suitable build file exists, creates one near the top module or at the root.
    
    Args:
        directory (str): Root directory of the project
        top_module (str): Optional top module name
        modules (List[Tuple[str, str]]): Optional list of (module_name, file_path)
        
    Returns:
        Tuple[str, str]: Tuple of (build_file_path, build_tool) where build_tool is 'sbt' or 'mill'
    """
    build_result = find_build_file(directory, top_module, modules)
    
    if build_result:
        return build_result
    
    # No build file found - create build.sbt (default to SBT for now)
    # TODO: Could detect Mill preference if certain conditions are met
    print("[INFO] No build file found, creating build.sbt")
    
    # Determine where to create build.sbt
    # If we know the top module location, create it near the module
    build_dir = directory
    
    if top_module and modules:
        module_to_file = {name: path for name, path in modules}
        if top_module in module_to_file:
            top_module_file = module_to_file[top_module]
            # Find the src/main/scala directory or closest parent
            current = os.path.dirname(top_module_file)
            
            # Walk up to find src directory or project root
            while current.startswith(directory):
                if os.path.basename(current) == 'scala':
                    # Go up to 'main', then 'src', then the project dir
                    parent = os.path.dirname(current)
                    if os.path.basename(parent) == 'main':
                        grandparent = os.path.dirname(parent)
                        if os.path.basename(grandparent) == 'src':
                            build_dir = os.path.dirname(grandparent)
                            break
                
                parent_dir = os.path.dirname(current)
                if parent_dir == current:
                    break
                current = parent_dir
    
    # Create build.sbt
    build_sbt = os.path.join(build_dir, 'build.sbt')
    
    build_content = """name := "chisel-processor"

version := "0.1"

scalaVersion := "2.13.10"

libraryDependencies ++= Seq(
  "edu.berkeley.cs" %% "chisel3" % "3.6.0",
  "edu.berkeley.cs" %% "chiseltest" % "0.6.0" % "test"
)

scalacOptions ++= Seq(
  "-deprecation",
  "-feature",
  "-unchecked",
  "-language:reflectiveCalls"
)
"""
    
    with open(build_sbt, 'w', encoding='utf-8') as f:
        f.write(build_content)
    
    print(f"[INFO] Created build.sbt: {build_sbt}")
    
    return (build_sbt, 'sbt')


def emit_verilog(
    directory: str,
    main_app: str,
    timeout: int = 300,
    main_class_override: str = None,
    build_tool: str = 'sbt'
) -> Tuple[bool, str, str]:
    """Run SBT or Mill to emit Verilog from the main App.
    
    Args:
        directory (str): Root directory of the project
        main_app (str): Path to the main App file
        timeout (int): Timeout in seconds for build tool execution
        main_class_override (str): Optional main class name (package.ClassName)
        build_tool (str): Build tool to use ('sbt' or 'mill')
        
    Returns:
        Tuple[bool, str, str]: (success, verilog_file_path, log_output)
    """
    import subprocess
    
    # Use override if provided, otherwise extract from file
    if main_class_override:
        main_class = main_class_override
    else:
        # Extract the main class name from the App file
        main_class = None
        try:
            with open(main_app, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find object name that extends App
            match = re.search(r'object\s+(\w+)\s+extends\s+App', content)
            if match:
                main_class = match.group(1)
            
            # Find package name
            package_match = re.search(r'package\s+([\w.]+)', content)
            if package_match:
                package_name = package_match.group(1)
                main_class = f"{package_name}.{main_class}"
        
        except Exception as e:
            print(f"[ERROR] Failed to parse main App file: {e}")
            return False, "", ""
    
    if not main_class:
        print("[ERROR] Could not determine main class name")
        return False, "", ""
    
    # Construct the appropriate command for the build tool
    if build_tool == 'mill':
        # Mill command: mill <module>.runMain package.ClassName
        # Try to detect the module name from build.sc
        mill_module = 'design'  # Default
        
        # Try to find build.sc and parse module name
        build_sc = os.path.join(directory, 'build.sc')
        if os.path.exists(build_sc):
            try:
                with open(build_sc, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all modules that extend appropriate base classes
                module_matches = re.findall(r'object\s+(\w+)\s+extends\s+(?:\w+(?:Module|NS))', content)
                if module_matches:
                    # Prefer the last module (usually the main one that depends on others)
                    # or look for 'generator', 'design', 'main' as common names
                    for preferred in ['generator', 'design', 'main']:
                        if preferred in module_matches:
                            mill_module = preferred
                            break
                    else:
                        mill_module = module_matches[-1]  # Take the last one
                    print(f"[INFO] Detected Mill module: {mill_module}")
            except Exception as e:
                print(f"[WARNING] Could not parse build.sc: {e}")
        
        command = f'mill {mill_module}.runMain {main_class}'
        print(f"[INFO] Running Mill to generate Verilog (main class: {main_class})...")
    else:
        # SBT command: sbt "runMain package.ClassName"
        command = f'sbt "runMain {main_class}"'
        print(f"[INFO] Running SBT to generate Verilog (main class: {main_class})...")
    
    try:
        # Run build tool using shell to properly handle the command
        # We need shell=True to pass the quoted command correctly
        result = subprocess.run(
            command,
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True
        )
        
        log_output = result.stdout + result.stderr
        
        if result.returncode == 0:
            # Look for generated Verilog files in multiple locations
            # SpinalHDL typically generates in current directory (.) or specified targetDirectory
            # Chisel might use generated/ or other directories
            search_locations = [
                directory,  # Root directory (SpinalHDL default)
                os.path.join(directory, 'rtl'),  # Common target directory for SpinalHDL
                os.path.join(directory, 'generated'),  # Common generated directory
                os.path.join(directory, 'build'),  # Build directory
                os.path.join(directory, 'verilog'),  # Verilog output directory
                os.path.join(directory, 'target'),  # SBT target directory
            ]
            
            verilog_files = []
            for location in search_locations:
                if os.path.exists(location):
                    found_files = glob.glob(f'{location}/*.v')
                    # Filter by modification time (must be very recent, within last 2 minutes)
                    import time
                    current_time = time.time()
                    recent_files = [f for f in found_files 
                                   if os.path.getmtime(f) > current_time - 120]
                    verilog_files.extend(recent_files)
            
            if verilog_files:
                # Sort by modification time (most recent first)
                verilog_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
                verilog_file = verilog_files[0]
                print(f"[SUCCESS] Generated Verilog: {verilog_file}")
                return True, verilog_file, log_output
            
            print("[WARNING] SBT succeeded but no Verilog file found")
            print(f"[DEBUG] Searched locations: {search_locations}")
            return False, "", log_output
        else:
            print(f"[ERROR] SBT failed with return code {result.returncode}")
            return False, "", log_output
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] SBT execution timed out after {timeout} seconds")
        return False, "", "Timeout"
    except Exception as e:
        print(f"[ERROR] SBT execution failed: {e}")
        return False, "", str(e)


def process_chisel_project(
    directory: str,
    repo_name: str = None
) -> Dict:
    """Process a Chisel/SpinalHDL project end-to-end.
    
    Args:
        directory (str): Root directory of the Chisel/SpinalHDL project
        repo_name (str): Repository name for heuristics
        
    Returns:
        Dict: Configuration dictionary with project information
    """
    print(f"[INFO] Processing Chisel project: {directory}")
    
    # Step 1: Find Scala files
    scala_files = find_scala_files(directory)
    print(f"[INFO] Found {len(scala_files)} Scala files")
    
    if not scala_files:
        print("[ERROR] No Scala files found")
        return None
    
    # Step 2: Extract Chisel/SpinalHDL modules
    modules = extract_chisel_modules(scala_files)
    print(f"[INFO] Found {len(modules)} Chisel modules")
    
    if not modules:
        print("[ERROR] No Chisel modules found")
        return None
    
    # Step 3: Build dependency graph
    module_graph, module_graph_inverse = build_chisel_dependency_graph(modules)
    
    # Step 4: Identify top module
    top_module = find_top_module(module_graph, module_graph_inverse, modules, repo_name)
    
    if not top_module:
        print("[ERROR] Could not identify top module")
        return None
    
    print(f"[INFO] Top module: {top_module}")
    
    # Step 5: Configure build file (build.sbt or build.sc) - passing modules to find correct build file
    build_file, build_tool = configure_build_file(directory, top_module, modules)
    
    # Get the directory where build file is located - this is where we need to run the build tool
    build_directory = os.path.dirname(build_file)
    
    # Step 6: Detect HDL type (Chisel or SpinalHDL)
    hdl_type = detect_hdl_type(directory, build_file)
    print(f"[INFO] Detected HDL type: {hdl_type}")
    print(f"[INFO] Build directory: {build_directory}")
    print(f"[INFO] Build tool: {build_tool}")
    
    # Step 7: Try to find existing main Apps (get ALL candidates)
    app_candidates = find_all_main_apps(directory, top_module, hdl_type, repo_name)
    
    success = False
    verilog_file = None
    log = ""
    final_main_class = None
    final_top_module = top_module
    
    if app_candidates and len(app_candidates) > 0:
        print(f"[INFO] Found {len(app_candidates)} App candidates, trying in order...")
        
        # Try each candidate in order of score
        for idx, (score, app_path, main_class, app_name, instantiated_module) in enumerate(app_candidates):
            print(f"[INFO] Trying App {idx+1}/{len(app_candidates)}: {app_name} (score: {score}, instantiates: {instantiated_module})")
            
            # Try to run this App - use build_directory instead of directory
            success, verilog_file, log = emit_verilog(build_directory, app_path, main_class_override=main_class, build_tool=build_tool)
            
            if success:
                print(f"[SUCCESS] App {app_name} worked!")
                final_main_class = main_class
                final_top_module = instantiated_module
                break
            else:
                print(f"[WARNING] App {app_name} failed, trying next candidate...")
                # Show a snippet of the error
                if "ClassNotFoundException" in log:
                    print(f"[DEBUG] ClassNotFoundException - class may not be compiled")
                elif "error" in log.lower():
                    error_lines = [line for line in log.split('\n') if 'error' in line.lower()]
                    if error_lines:
                        print(f"[DEBUG] Error: {error_lines[0][:200]}")
        
        if not success:
            print("[WARNING] All App candidates failed, will try generating new App")
    else:
        print(f"[INFO] No existing Apps found")
    
    # Step 8: If no existing App worked, generate a new one
    if not success:
        print(f"[INFO] Generating new main App for {top_module}")
        main_app = generate_main_app(directory, top_module, modules, hdl_type)
        success, verilog_file, log = emit_verilog(build_directory, main_app, build_tool=build_tool)
        
        if not success:
            # Clean up the generated file since it didn't work
            try:
                if os.path.exists(main_app):
                    os.remove(main_app)
                    print(f"[INFO] Cleaned up failed generated App: {main_app}")
            except Exception:
                pass
        else:
            # Extract main class from generated app
            try:
                with open(main_app, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                match = re.search(r'object\s+(\w+)\s+extends\s+App', content)
                if match:
                    final_main_class = match.group(1)
                
                package_match = re.search(r'package\s+([\w.]+)', content)
                if package_match:
                    package_name = package_match.group(1)
                    final_main_class = f"{package_name}.{final_main_class}"
            except Exception:
                pass
    
    if not success:
        print("[ERROR] Failed to generate Verilog with all attempts")
        print(f"[LOG] {log}")
        return None
    if not success:
        print("[ERROR] Failed to generate Verilog with all attempts")
        print(f"[LOG] {log}")
        return None
    
    # Build configuration using the final successful values
    # Generate appropriate pre_script based on build tool
    pre_script = None
    if final_main_class:
        if build_tool == 'mill':
            # Detect mill module from build.sc
            mill_module = 'design'
            build_sc = os.path.join(directory, 'build.sc')
            if os.path.exists(build_sc):
                try:
                    with open(build_sc, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Find all modules that extend appropriate base classes
                    module_matches = re.findall(r'object\s+(\w+)\s+extends\s+(?:\w+(?:Module|NS))', content)
                    if module_matches:
                        # Prefer the last module (usually the main one that depends on others)
                        # or look for 'generator', 'design', 'main' as common names
                        for preferred in ['generator', 'design', 'main']:
                            if preferred in module_matches:
                                mill_module = preferred
                                break
                        else:
                            mill_module = module_matches[-1]  # Take the last one
                        print(f"[INFO] Detected Mill module: {mill_module}")
                except Exception:
                    pass
            pre_script = f'mill {mill_module}.runMain {final_main_class}'
        else:
            pre_script = f'sbt "runMain {final_main_class}"'
    
    config = {
        'name': repo_name or os.path.basename(directory),
        'folder': os.path.basename(directory),
        'files': [os.path.relpath(verilog_file, directory)] if verilog_file else [],
        'source_files': [os.path.relpath(path, directory) for name, path in modules],
        'top_module': final_top_module,
        'repository': "",
        'pre_script': pre_script,
        'is_simulable': success
    }
    
    return config
