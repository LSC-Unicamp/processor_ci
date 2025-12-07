"""
Bluespec SystemVerilog (BSV) Manager Module

This module provides utilities for handling Bluespec SystemVerilog projects:
- Finding and parsing BSV files
- Extracting module definitions (mkModule pattern)
- Building dependency graphs from module instantiations
- Identifying top-level modules
- Extracting interface definitions
- Compiling BSV to Verilog using bsc compiler

Bluespec Patterns:
- Module definitions: mkCore, mkALU, mkCache, etc. (mk* prefix convention)
- Module instantiations: ALU alu <- mkALU();
- Interface definitions: interface CoreIfc; ... endinterface
- Module with interface: module mkCore(CoreIfc);

Main functions:
- find_bsv_files: Locates all BSV files in a directory
- extract_bluespec_modules: Extracts module definitions (mk* pattern)
- find_module_instantiations: Finds module instantiations
- build_bluespec_dependency_graph: Builds module instantiation graph
- find_top_module: Identifies the top-level module
- extract_interfaces: Extracts interface definitions
- compile_to_verilog: Runs bsc to generate Verilog output
"""

import os
import re
import glob
import subprocess
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
    return n.endswith("if") or n.endswith("ifc") or "interface" in n


def _ensure_mapping(mapping: Any) -> Dict[str, List[str]]:
    """Normalize a graph-like input into a dict: node -> list(children/parents)."""
    out: Dict[str, List[str]] = {}
    if not mapping:
        return out
    if isinstance(mapping, dict):
        for k, v in mapping.items():
            if isinstance(v, (list, tuple)):
                out[k] = list(v)
            elif isinstance(v, str):
                out[k] = [v]
            else:
                out[k] = []
        return out
    if isinstance(mapping, (list, tuple)):
        pair_like = all(isinstance(el, (list, tuple)) and len(el) == 2 for el in mapping)
        if pair_like:
            for parent, child in mapping:
                parent_s = str(parent)
                child_s = str(child)
                if parent_s not in out:
                    out[parent_s] = []
                out[parent_s].append(child_s)
            return out
        if all(isinstance(el, (str, bytes)) for el in mapping):
            return {str(el): [] for el in mapping}
    try:
        for el in mapping:
            out[str(el)] = []
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
            if ch not in seen and ch != start:
                seen.add(ch)
                q.append(ch)
    return len(seen)


def find_bsv_files(directory: str) -> List[str]:
    """Find all Bluespec SystemVerilog files in the given directory.
    
    Args:
        directory (str): Root directory to search
        
    Returns:
        List[str]: List of absolute paths to BSV files
    """
    bsv_files = []
    
    # Common directories to exclude (test directories, build artifacts, etc.)
    exclude_dirs = ['build', 'obj', 'bdir', 'simdir', 'verilog', 'test', 'tests', '.git']
    
    for bsv_file in glob.glob(f'{directory}/**/*.bsv', recursive=True):
        # Skip files in excluded directories
        relative_path = os.path.relpath(bsv_file, directory)
        if any(excl in relative_path for excl in exclude_dirs):
            continue
            
        # Skip broken symlinks
        if os.path.islink(bsv_file) and not os.path.exists(bsv_file):
            continue
            
        bsv_files.append(os.path.abspath(bsv_file))
    
    return bsv_files


def extract_bluespec_modules(bsv_files: List[str]) -> List[Tuple[str, str]]:
    """Extract Bluespec module definitions from BSV files.
    
    Looks for patterns like:
    - module mkCore(CoreIfc);
    - module mkALU(ALUIfc);
    - module [Module] mkCore(CoreIfc);
    - (* synthesize *)
      module mkTop(TopIfc);
    
    Bluespec convention: modules start with 'mk' prefix (mkCore, mkALU, etc.)
    
    Note: Filters out modules from Unit_Test directories and Test files
    
    Args:
        bsv_files (List[str]): List of BSV file paths
        
    Returns:
        List[Tuple[str, str]]: List of (module_name, file_path) tuples
    """
    modules = []
    
    # Pattern to match Bluespec module definitions
    # Matches: module [optional_monad] mkModuleName(InterfaceName);
    # Also matches: (* synthesize *) module mkModuleName #(params) (InterfaceName);
    # The #(params) part is optional (for parameterized modules)
    module_pattern = re.compile(
        r'^\s*(?:\(\*.*?\*\)\s*)*module\s+(?:\[.*?\]\s+)?(mk\w+)',
        re.MULTILINE
    )
    
    for file_path in bsv_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Remove comments (both single-line // and multi-line /* */)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            
            # Find all module definitions
            matches = module_pattern.findall(content)
            
            for module_name in matches:
                modules.append((module_name, file_path))
                print(f"[DEBUG] Found module: {module_name} in {os.path.basename(file_path)}")
                
        except Exception as e:
            print(f"[WARNING] Error parsing {file_path}: {e}")
    
    return modules


def find_module_instantiations(file_path: str) -> Set[str]:
    """Find all module instantiations in a BSV file.
    
    Looks for patterns like:
    - ALU alu <- mkALU();
    - ALU alu <- mkALU(params);
    - let alu <- mkALU();
    - RegFile#(Addr, Data) rf <- mkRegFile();
    
    Args:
        file_path (str): Path to BSV file
        
    Returns:
        Set[str]: Set of instantiated module names (mk* modules)
    """
    instantiations = set()
    
    # Pattern to match module instantiations
    # Matches: <identifier> <- mkModuleName(...);
    instantiation_pattern = re.compile(r'<-\s*(mk\w+)\s*\(')
    
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


def extract_interfaces(bsv_files: List[str]) -> List[Tuple[str, str]]:
    """Extract interface definitions from BSV files.
    
    Looks for patterns like:
    - interface CoreIfc;
        method Action start();
        method Bit#(32) result();
      endinterface
    
    Args:
        bsv_files (List[str]): List of BSV file paths
        
    Returns:
        List[Tuple[str, str]]: List of (interface_name, file_path) tuples
    """
    interfaces = []
    
    # Pattern to match interface definitions
    interface_pattern = re.compile(
        r'^\s*interface\s+(\w+)\s*;',
        re.MULTILINE
    )
    
    for file_path in bsv_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Remove comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            
            # Find all interface definitions
            matches = interface_pattern.findall(content)
            
            for interface_name in matches:
                interfaces.append((interface_name, file_path))
                print(f"[DEBUG] Found interface: {interface_name} in {os.path.basename(file_path)}")
                
        except Exception as e:
            print(f"[WARNING] Error parsing {file_path}: {e}")
    
    return interfaces


def build_bluespec_dependency_graph(
    modules: List[Tuple[str, str]]
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build dependency graph for Bluespec modules.
    
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
                module_graph[module_name].append(inst_module)
                module_graph_inverse[inst_module].append(module_name)
                print(f"[DEBUG] {module_name} instantiates {inst_module}")
    
    return module_graph, module_graph_inverse


def find_top_module(
    module_graph: Dict[str, List[str]],
    module_graph_inverse: Dict[str, List[str]],
    modules: List[Tuple[str, str]],
    repo_name: str = None
) -> Optional[str]:
    """Identify the top-level module using sophisticated scoring algorithm.
    
    Uses the same comprehensive heuristics as config_generator.py:
    - Repository name matching (highest priority)
    - Architectural indicators (CPU, core, processor)
    - Structural analysis (parent/child relationships)
    - Negative indicators (peripherals, test benches, utilities)
    - Bluespec-specific patterns (mkTop, mkCore, mkProcessor)
    - Path-based scoring (prefer Core/Core_v2 folders over test folders)
    
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
    
    # Build module name to file mapping
    module_to_file = {}
    for module_name, file_path in modules:
        module_to_file[module_name] = file_path
    
    # Find valid candidates - use all modules as initial candidates
    candidates = list(module_graph.keys())
    
    if not candidates:
        print("[WARNING] No valid candidates found")
        return None
    
    repo_lower = (repo_name or "").lower()
    scored = []
    
    # Normalize repo name
    repo_normalized = repo_lower.replace('-', '').replace('_', '')
    
    for c in candidates:
        score = 0
        name_lower = c.lower()
        name_normalized = name_lower.replace('_', '').replace('mk', '', 1)
        
        # Get file path for this module
        mod_file = module_to_file.get(c, "")
        path_lower = mod_file.replace("\\", "/").lower() if mod_file else ""
        
        # CPU TOP MODULE DETECTION (Very High Priority) - Following config_generator.py
        cpu_top_patterns = [
            f"mk{repo_lower}top", f"mktop{repo_lower}", f"mk{repo_lower}cpu", f"mkcpu{repo_lower}",
            "mkcputop", "mkcoretop", "mkprocessortop", "mkriscvtop"
        ]
        if repo_lower:
            cpu_top_patterns.extend([f"mk{repo_lower}", f"mk{repo_lower}core", f"mkcore{repo_lower}"])
        
        for pattern in cpu_top_patterns:
            if name_lower == pattern:
                # Ensure it's not a functional unit
                if not any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu"]):
                    score += 45000
                    print(f"[DEBUG] {c}: Matches CPU top pattern '{pattern}' (+45000)")
                    break
        
        # DIRECT CORE NAME PATTERNS (high priority - we want cores, not SoCs)
        # Special case for exact "mkCore" module name - very common CPU top module pattern
        if name_lower == "mkcore":
            score += 40000
            print(f"[DEBUG] {c}: Exact mkCore match (+40000)")
        
        # Look for modules that are exactly the repo name (likely the core)
        if repo_lower and name_lower == f"mk{repo_lower}":
            score += 25000
            print(f"[DEBUG] {c}: Exact mk+repo name (+25000)")
        
        # Specific CPU core boost - give highest priority to actual core modules
        if "core" in name_lower and repo_lower:
            # Check if it's a functional unit core first - apply heavy penalty
            if any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu", "mem", "cache", "bus", "_ctrl", "ctrl_", "reg", "decode", "fetch", "exec", "forward", "hazard", "pred", "shift", "barrel", "adder", "mult", "divider", "encoder", "decoder"]):
                # Exception: don't penalize microcontroller
                if "microcontroller" not in name_lower:
                    score -= 15000
                    print(f"[DEBUG] {c}: Functional unit core penalty (-15000)")
            # Penalize subsystem cores - they're usually wrappers around the actual core
            elif "subsys" in name_lower or "subsystem" in name_lower:
                score -= 8000
                print(f"[DEBUG] {c}: Subsystem penalty (-8000)")
            # Strong boost for exact core modules like "mk{repo}_core"
            elif name_lower == f"mk{repo_lower}_core" or name_lower == f"mkcore_{repo_lower}":
                score += 25000
                print(f"[DEBUG] {c}: Exact mk{repo}_core pattern (+25000)")
            # Generic pattern: any module ending with "_core"
            elif name_lower.endswith("_core"):
                score += 20000
                print(f"[DEBUG] {c}: Ends with _core (+20000)")
            # Medium boost for modules containing both repo name and core
            elif repo_lower in name_lower and "core" in name_lower:
                score += 15000
                print(f"[DEBUG] {c}: Contains repo + core (+15000)")
        
        if "core" in name_lower:
            # Heavy penalty for functional unit cores
            if any(unit in name_lower for unit in ["fadd", "fmul", "fdiv", "fsqrt", "fpu", "div", "mul", "alu"]):
                score -= 10000
                print(f"[DEBUG] {c}: FPU/ALU core penalty (-10000)")
            # Additional penalty for other peripheral cores (but exclude microcontroller)
            elif not ("microcontroller" in name_lower) and any(unit in name_lower for unit in ["mem", "cache", "bus", "_ctrl", "ctrl_", "reg", "decode", "fetch", "exec", "forward", "hazard", "pred", "shift", "barrel", "adder", "mult", "divider", "encoder", "decoder"]):
                score -= 5000
                print(f"[DEBUG] {c}: Peripheral core penalty (-5000)")
            else:
                score += 1500
                print(f"[DEBUG] {c}: Generic core bonus (+1500)")
        
        # Architecture indicators
        if any(arch in name_lower for arch in ["riscv", "risc", "mips", "arm"]):
            score += 1000
            print(f"[DEBUG] {c}: Architecture indicator (+1000)")
        
        # Top suffix/prefix
        if name_lower.endswith("_top") or name_lower.startswith("top_") or name_lower == "mktop":
            score += 800
            print(f"[DEBUG] {c}: Top suffix/prefix (+800)")
        
        # PATH-AWARE SCORING (Critical for Flute!)
        # Strong bonus for modules in Core or Core_v2 directories
        if any(core_dir in path_lower for core_dir in ["/core/", "/core_v2/"]):
            # But not in sub-directories like /cache_config/
            if not any(subdir in path_lower for subdir in ["/cache_config/", "/debug_module/", "/near_mem"]):
                score += 35000
                print(f"[DEBUG] {c}: In Core/Core_v2 directory (+35000)")
        
        # Heavy penalty for test directories
        test_dirs = ["/test/", "/tests/", "/testbench/", "/unit_test/", "/tb/"]
        if any(test_dir in path_lower for test_dir in test_dirs):
            score -= 10000
            print(f"[DEBUG] {c}: In test directory (-10000)")
        
        # STRUCTURAL ANALYSIS
        num_parents = len(module_graph_inverse.get(c, []))
        num_children = len(module_graph.get(c, []))
        
        # Boost CPU cores (modules with few parents and "core"/"cpu"/"processor" in name)
        # These are better targets for testing than SoC tops
        is_likely_core = (num_parents >= 1 and num_parents <= 3 and 
                          any(pattern in name_lower for pattern in ['core', 'cpu', 'processor']) and
                          not any(bad in name_lower for bad in ['_top', 'top_', 'soc', 'system', 'wrapper']))
        
        if is_likely_core and num_children > 2:
            score += 25000
            print(f"[DEBUG] {c}: Likely CPU core with structure (+25000)")
        elif num_children > 10 and num_parents == 0:
            score += 1000
            print(f"[DEBUG] {c}: Many children, zero parents (+1000)")
        elif num_children > 5 and num_parents <= 1:
            score += 500
            print(f"[DEBUG] {c}: Several children, few parents (+500)")
        elif num_children > 2:
            score += 200
            print(f"[DEBUG] {c}: Some children (+200)")
        
        if num_parents == 0:
            score += 2000
            print(f"[DEBUG] {c}: Zero parents (+2000)")
        elif num_parents == 1:
            score += 1000
            print(f"[DEBUG] {c}: One parent (+1000)")
        elif num_parents == 2:
            score += 500
            print(f"[DEBUG] {c}: Two parents (+500)")
        
        if num_children >= 5:
            score += 1500
            print(f"[DEBUG] {c}: Many children ({num_children}) (+1500)")
        elif num_children >= 3:
            score += 1000
            print(f"[DEBUG] {c}: Several children ({num_children}) (+1000)")
        
        # NEGATIVE INDICATORS (following config_generator.py scoring)
        # Penalize single functional units (ALU, multiplier, divider, etc.)
        if _is_functional_unit_name(name_lower):
            score -= 12000
            print(f"[DEBUG] {c}: Functional unit name (-12000)")
        
        # Penalize micro-stage modules that are unlikely to be CPU tops
        if _is_micro_stage_name(name_lower):
            score -= 40000
            print(f"[DEBUG] {c}: Micro-stage name (-40000)")
        
        # Penalize interface-only modules
        if _is_interface_module_name(name_lower):
            score -= 12000
            print(f"[DEBUG] {c}: Interface module (-12000)")
        
        # Path-aware penalty: if the module's file lives in a micro-stage subfolder, penalize
        if path_lower:
            stage_dirs = [
                "/fetchunit/", "/fetchstage/", "/rename", "/renamelogic/", "/scheduler/", "/decode",
                "/commit", "/dispatch", "/issue", "/execute", "/integerbackend/",
                "/memorybackend/", "/fpbackend/", "/muldivunit/", "/floatingpointunit/"
            ]
            if any(sd in path_lower for sd in stage_dirs):
                score -= 15000
                print(f"[DEBUG] {c}: In micro-stage directory (-15000)")
        
        # SOC penalty - we want CPU cores, not full system-on-chip
        if "soc" in name_lower:
            score -= 5000
            print(f"[DEBUG] {c}: SoC indicator (-5000)")
        
        # Penalize peripherals
        if _is_peripheral_like_name(name_lower):
            score -= 3000
            print(f"[DEBUG] {c}: Peripheral-like name (-3000)")
        
        # Testbench detection
        if any(term in name_lower for term in ["test", "tb", "bench", "sim", "verify"]):
            score -= 5000
            print(f"[DEBUG] {c}: Testbench indicator (-5000)")
        
        # Utility/helper modules
        if any(name_lower.startswith(pat) for pat in UTILITY_PATTERNS):
            score -= 2000
            print(f"[DEBUG] {c}: Utility pattern (-2000)")
        
        # Calculate reachability as a tiebreaker
        reach = _reachable_size(module_graph, c)
        scored.append((score, reach, c))
    
    # Sort by score (descending), then by reach, then by name
    scored.sort(reverse=True, key=lambda t: (t[0], t[1], t[2]))
    
    # Filter out micro-stage and interface modules
    ranked = [c for score, _, c in scored if score > -5000]
    filtered_ranked = [c for c in ranked if not _is_micro_stage_name(c.lower()) and not _is_interface_module_name(c.lower())]
    if filtered_ranked:
        ranked = filtered_ranked
    
    if not ranked:
        print("[WARNING] All candidates filtered out")
        return None
    
    top_module = ranked[0]
    top_score = scored[0][0]
    print(f"[INFO] Selected top module: {top_module} (score: {top_score})")
    print(f"[INFO] Top 5 candidates: {[f'{c} ({s})' for s, _, c in scored[:5]]}")
    
    return top_module


def find_package_name(file_path: str) -> Optional[str]:
    """Extract package name from a BSV file.
    
    Looks for: package PackageName;
    
    Args:
        file_path (str): Path to BSV file
        
    Returns:
        Optional[str]: Package name, or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = re.match(r'^\s*package\s+(\w+)\s*;', line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    
    return None


def find_bsv_package_file(directory: str, package_name: str, bsv_files: List[str]) -> Optional[str]:
    """Find BSV file that declares a specific package.
    
    Args:
        directory (str): Root directory to search
        package_name (str): Name of the package to find
        bsv_files (List[str]): List of BSV file paths to search
        
    Returns:
        Optional[str]: Relative path to file containing the package, or None if not found
    """
    for bsv_file in bsv_files:
        try:
            with open(bsv_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Look for package declaration
                if re.search(rf'^\s*package\s+{re.escape(package_name)}\s*;', content, re.MULTILINE):
                    # Return directory containing this file (relative to project root)
                    pkg_dir = os.path.dirname(bsv_file)
                    try:
                        rel_dir = os.path.relpath(pkg_dir, directory)
                        if not rel_dir.startswith('..'):
                            return rel_dir
                    except ValueError:
                        pass
        except Exception:
            continue
    
    return None


def parse_bsc_errors(log_output: str) -> Dict[str, List[str]]:
    """Parse BSC error output to extract missing dependencies.
    
    Looks for errors like:
    - Cannot find package `PackageName'
    - Unbound type constructor `TypeName'
    - Unbound variable `VarName'
    
    Args:
        log_output (str): BSC compilation log output
        
    Returns:
        Dict with keys: 'packages', 'types', 'variables'
    """
    result = {
        'packages': [],
        'types': [],
        'variables': []
    }
    
    # Pattern: Cannot find package `PackageName'
    package_pattern = re.compile(r"Cannot find package\s+[`'](\w+)[`']", re.MULTILINE)
    for match in package_pattern.finditer(log_output):
        pkg_name = match.group(1)
        if pkg_name not in result['packages']:
            result['packages'].append(pkg_name)
    
    # Pattern: Unbound type constructor `TypeName'
    type_pattern = re.compile(r"Unbound type constructor\s+[`'](\w+)[`']", re.MULTILINE)
    for match in type_pattern.finditer(log_output):
        type_name = match.group(1)
        if type_name not in result['types']:
            result['types'].append(type_name)
    
    # Pattern: Unbound variable `VarName'
    var_pattern = re.compile(r"Unbound variable\s+[`'](\w+)[`']", re.MULTILINE)
    for match in var_pattern.finditer(log_output):
        var_name = match.group(1)
        if var_name not in result['variables']:
            result['variables'].append(var_name)
    
    return result


def find_bsv_type_definition(directory: str, type_name: str, bsv_files: List[str]) -> Optional[str]:
    """Find BSV file that defines a specific type.
    
    Searches for:
    - typedef <number> TypeName;       (numeric typedef)
    - typedef ... TypeName;             (complex typedef)
    - typedef ... TypeName#(...);       (parameterized)
    - type TypeName = ...;              (type alias)
    
    Args:
        directory (str): Root directory to search
        type_name (str): Name of the type to find
        bsv_files (List[str]): List of BSV file paths to search
        
    Returns:
        Optional[str]: Path to file containing the type definition, or None if not found
    """
    # Pattern matches various typedef formats
    patterns = [
        # typedef 64 Wd_Addr;
        re.compile(rf'^\s*typedef\s+\d+\s+{re.escape(type_name)}\s*;', re.MULTILINE),
        # typedef ... TypeName; or typedef ... TypeName#(...);
        re.compile(rf'^\s*typedef\s+.*?\s+{re.escape(type_name)}\s*(?:#\(.*?\))?\s*;', re.MULTILINE),
        # type TypeName = ...;
        re.compile(rf'^\s*type\s+{re.escape(type_name)}\s*=', re.MULTILINE)
    ]
    
    for bsv_file in bsv_files:
        try:
            with open(bsv_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for pattern in patterns:
                    if pattern.search(content):
                        return bsv_file
        except Exception:
            continue
    
    return None


def detect_required_defines(file_path: str, type_name: str) -> List[str]:
    """Detect which ifdef defines are required for a type definition.
    
    Looks for patterns like:
    `ifdef FABRIC64
    typedef 64 TypeName;
    `endif
    
    Args:
        file_path (str): Path to BSV file containing the type
        type_name (str): Name of the type to find
        
    Returns:
        List[str]: List of define names that enable this type (e.g., ['FABRIC64', 'FABRIC32'])
    """
    required_defines = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Find all sections that define this type within ifdef blocks
        # Pattern: `ifdef DEFINE_NAME ... typedef ... TypeName ... `endif
        pattern = re.compile(
            rf'`ifdef\s+(\w+).*?typedef\s+.*?\s+{re.escape(type_name)}\s*[;#].*?`endif',
            re.DOTALL | re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            define_name = match.group(1)
            if define_name not in required_defines:
                required_defines.append(define_name)
    
    except Exception:
        pass
    
    return required_defines


def find_bsv_variable_definition(directory: str, var_name: str, bsv_files: List[str]) -> Optional[str]:
    """Find BSV file that defines a specific variable or function.
    
    Searches for:
    - function ReturnType varName(...);
    - Type varName = ...;
    - module mkVarName ...;
    
    Args:
        directory (str): Root directory to search
        var_name (str): Name of the variable/function to find
        bsv_files (List[str]): List of BSV file paths to search
        
    Returns:
        Optional[str]: Path to file containing the definition, or None if not found
    """
    # Pattern matches function or variable declarations
    patterns = [
        re.compile(rf'^\s*function\s+.*?\s+{re.escape(var_name)}\s*\(', re.MULTILINE),
        re.compile(rf'^\s*\w+\s+{re.escape(var_name)}\s*=', re.MULTILINE),
        re.compile(rf'^\s*module\s+{re.escape(var_name)}', re.MULTILINE)
    ]
    
    for bsv_file in bsv_files:
        try:
            with open(bsv_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for pattern in patterns:
                    if pattern.search(content):
                        return bsv_file
        except Exception:
            continue
    
    return None


def _try_compile_with_iterations(
    directory: str,
    top_module: str,
    top_module_file: str,
    bsv_files: List[str],
    timeout: int,
    search_paths: List[str] = None,
    max_iterations: int = 15
) -> Tuple[bool, str, str]:
    """Try to compile a specific candidate file with full iterative dependency resolution.
    
    Similar to Verilator's incremental compilation - tries to resolve dependencies
    at each error until success or no more progress can be made.
    
    Args:
        directory: Root directory of the project
        top_module: Name of the top module
        top_module_file: Specific file to try compiling
        bsv_files: List of all BSV files
        timeout: Timeout in seconds
        search_paths: Optional additional search paths
        max_iterations: Maximum number of iterations to try
        
    Returns:
        Tuple[bool, str, str]: (success, verilog_file_path, log_output)
    """
    # Get the directory containing the top module - this should be searched first
    top_module_dir = os.path.dirname(top_module_file)
    top_module_rel_dir = None
    try:
        top_module_rel_dir = os.path.relpath(top_module_dir, directory)
    except ValueError:
        pass
    
    # Discover all unique directories containing BSV files for package search paths
    bsv_directories = set()
    for bsv_file in bsv_files:
        bsv_dir = os.path.dirname(bsv_file)
        # Make relative to project directory
        try:
            rel_dir = os.path.relpath(bsv_dir, directory)
            if not rel_dir.startswith('..'):  # Only include subdirectories
                bsv_directories.add(rel_dir)
        except ValueError:
            pass
    
    # Build initial search path (top-down approach)
    # Start with minimal paths and add more as we discover dependencies
    search_path_components = []
    
    # Add top module directory first (highest priority)
    if top_module_rel_dir:
        search_path_components.append(top_module_rel_dir)
    
    # Add user-provided search paths
    if search_paths:
        search_path_components.extend(search_paths)
    
    # Add standard library
    search_path_components.append('%/Libraries')
    
    # Store all available BSV directories for later dependency resolution
    # We'll add these incrementally as needed, not all at once
    
    # Prepare bsc command
    cmd = [
        'bsc',
        '-verilog',
        '-g', top_module,
        '-u',
        '-aggressive-conditions'
    ]
    
    # Join all paths with colon
    full_search_path = ':'.join(search_path_components)
    cmd.extend(['-p', full_search_path])
    cmd.append(top_module_file)
    
    # Iterative compilation: try to resolve missing packages (like Verilator's incremental)
    added_paths = set(search_path_components)
    attempted_packages = set()
    defines = []  # Track compiler defines (-D flags)
    last_log = ""
    
    for iteration in range(max_iterations):
        try:
            result = subprocess.run(
                cmd,
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            log_output = result.stdout + result.stderr
            last_log = log_output
            
            # Check for success
            if result.returncode == 0:
                verilog_file = f"{top_module}.v"
                print(f"[INFO] ✓ Compilation successful after {iteration + 1} iteration(s)!")
                return (True, verilog_file, log_output)
            
            # Parse errors to find missing dependencies
            errors = parse_bsc_errors(log_output)
            missing_packages = errors['packages']
            missing_types = errors['types']
            missing_vars = errors['variables']
            
            # Print status
            total_missing = len(missing_packages) + len(missing_types) + len(missing_vars)
            print(f"[INFO] Iteration {iteration + 1}/{max_iterations}: Missing {len(missing_packages)} packages, {len(missing_types)} types, {len(missing_vars)} variables")
            
            # Check if we have any dependencies to resolve
            if total_missing == 0:
                # No resolvable errors found
                if iteration == 0:
                    print(f"[DEBUG] bsc output:\n{log_output}")
                return (False, "", f"bsc compilation failed (no resolvable dependencies):\n{log_output}")
            
            # Try to find and add missing dependencies
            added_something = False
            
            # First resolve missing packages
            for pkg_name in missing_packages:
                # Skip if we already attempted this package
                if pkg_name in attempted_packages:
                    continue
                
                attempted_packages.add(pkg_name)
                print(f"[INFO] Looking for missing package: {pkg_name}")
                
                pkg_dir = find_bsv_package_file(directory, pkg_name, bsv_files)
                
                if pkg_dir and pkg_dir not in added_paths:
                    print(f"[INFO] + Adding package directory: {pkg_dir} (provides '{pkg_name}')")
                    added_paths.add(pkg_dir)
                    added_something = True
                elif not pkg_dir:
                    print(f"[WARNING] ! Could not find package: {pkg_name}")
            
            # Try to resolve missing types (search for typedef in BSV files)
            for type_name in missing_types:
                if type_name in attempted_packages:
                    continue
                
                attempted_packages.add(type_name)
                print(f"[INFO] Looking for type definition: {type_name}")
                
                # Search all BSV files for typedef declarations
                type_file = find_bsv_type_definition(directory, type_name, bsv_files)
                
                if type_file:
                    type_dir = os.path.dirname(type_file)
                    try:
                        rel_dir = os.path.relpath(type_dir, directory)
                        if not rel_dir.startswith('..') and rel_dir not in added_paths:
                            print(f"[INFO] + Adding directory: {rel_dir} (defines '{type_name}')")
                            added_paths.add(rel_dir)
                            added_something = True
                        elif rel_dir in added_paths:
                            # Type is defined in a directory already in search path
                            # Check if it requires conditional compilation defines
                            required_defines = detect_required_defines(type_file, type_name)
                            if required_defines:
                                print(f"[INFO] Type '{type_name}' requires one of these defines: {', '.join(required_defines)}")
                                print(f"[INPUT] Which define should be used? [{'/'.join(required_defines)}]:", end=' ')
                                
                                # Get user input
                                try:
                                    user_choice = input().strip()
                                    if user_choice in required_defines:
                                        print(f"[INFO] + Adding define: -D {user_choice}")
                                        defines.append(user_choice)
                                        added_something = True
                                    else:
                                        print(f"[WARNING] Invalid choice '{user_choice}', using default: {required_defines[0]}")
                                        defines.append(required_defines[0])
                                        added_something = True
                                except EOFError:
                                    # Non-interactive mode, use first define
                                    print(f"{required_defines[0]}")
                                    print(f"[INFO] + Adding define: -D {required_defines[0]} (non-interactive)")
                                    defines.append(required_defines[0])
                                    added_something = True
                            else:
                                print(f"[INFO] Type '{type_name}' found in {rel_dir} (already in search path)")
                    except ValueError:
                        pass
                else:
                    print(f"[WARNING] ! Could not find type: {type_name}")
            
            # Try to resolve missing variables (search for definitions)
            for var_name in missing_vars:
                if var_name in attempted_packages:
                    continue
                
                attempted_packages.add(var_name)
                print(f"[INFO] Looking for variable definition: {var_name}")
                
                # Search all BSV files for variable/function declarations
                var_file = find_bsv_variable_definition(directory, var_name, bsv_files)
                
                if var_file:
                    var_dir = os.path.dirname(var_file)
                    try:
                        rel_dir = os.path.relpath(var_dir, directory)
                        if not rel_dir.startswith('..') and rel_dir not in added_paths:
                            print(f"[INFO] + Adding directory: {rel_dir} (defines '{var_name}')")
                            added_paths.add(rel_dir)
                            added_something = True
                        elif rel_dir in added_paths:
                            print(f"[INFO] Variable '{var_name}' found in {rel_dir} (already in search path)")
                            # Variable exists but still getting error - might be ifdef or other issue
                            # Continue iteration to see if other errors can be resolved
                    except ValueError:
                        pass
                else:
                    print(f"[WARNING] ! Could not find variable: {var_name}")
            
            if not added_something:
                # Couldn't resolve any new packages
                print(f"[INFO] No new dependencies resolved, stopping iteration")
                print(f"[INFO] ")
                print(f"[INFO] This project requires manual configuration:")
                print(f"[INFO]   1. Check project README/Makefile for required defines")
                print(f"[INFO]   2. Look for ifdef blocks that need compiler flags (e.g., -D FABRIC64)")
                print(f"[INFO]   3. Some modules may need explicit package imports in source code")
                print(f"[INFO]   4. The project may require a specific build system (make, etc.)")
                print(f"[INFO] ")
                print(f"[INFO] Current defines used: {defines if defines else '(none)'}")
                print(f"[INFO] Search paths: {len(added_paths)} directories")
                return (False, "", f"bsc compilation failed (unresolvable dependencies):\n{log_output}")
            
            # Rebuild command with new search paths and defines
            full_search_path = ':'.join(sorted(added_paths))
            cmd = [
                'bsc',
                '-verilog',
                '-g', top_module,
                '-u',
                '-aggressive-conditions'
            ]
            
            # Add compiler defines
            for define in defines:
                cmd.extend(['-D', define])
            
            # Add search path and source file
            cmd.extend(['-p', full_search_path, top_module_file])
            
        except subprocess.TimeoutExpired:
            return (False, "", f"Compilation timed out after {timeout} seconds")
        except Exception as e:
            return (False, "", f"Error running bsc: {e}")
    
    # Hit max iterations
    print(f"[INFO] Exhausted {max_iterations} iterations without successful compilation")
    print(f"[INFO] ")
    print(f"[INFO] Resolution summary:")
    print(f"[INFO]   - Defines added: {len(defines)} ({', '.join(defines) if defines else 'none'})")
    print(f"[INFO]   - Directories added: {len(added_paths)}")
    print(f"[INFO]   - Iterations completed: {iteration}")
    print(f"[INFO] ")
    return (False, "", f"bsc compilation failed after {max_iterations} iterations:\n{last_log}")


def compile_to_verilog(
    directory: str,
    top_module: str,
    bsv_files: List[str],
    timeout: int = 300,
    search_paths: List[str] = None
) -> Tuple[bool, str, str]:
    """Compile Bluespec to Verilog using bsc compiler.
    
    The bsc command structure:
    bsc -verilog -g <top_module> [search_paths] <file_with_top_module>
    
    Args:
        directory (str): Root directory of the project
        top_module (str): Name of the top module (e.g., mkCore)
        bsv_files (List[str]): List of BSV file paths
        timeout (int): Timeout in seconds for compilation
        search_paths (List[str]): Optional additional search paths
        
    Returns:
        Tuple[bool, str, str]: (success, verilog_file_path, log_output)
    """
    print(f"[INFO] Compiling Bluespec to Verilog: {top_module}")
    
    # Find the file containing the top module
    # Need to handle both:
    # - module mkCore(Interface);
    # - module mkCore #(params) (Interface);
    top_module_file = None
    top_module_candidates = []
    
    for file_path in bsv_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Check if this file contains the top module definition
                # Allow optional #(...) parameters between module name and interface
                # Use [\s\S] instead of . to match across newlines
                # Pattern matches: module mkCore
                #                     #(params)
                #                     (Interface);
                pattern = rf'module\s+{re.escape(top_module)}(?:\s*#\s*\([^)]*\))?'
                if re.search(pattern, content, re.DOTALL):
                    top_module_candidates.append(file_path)
        except Exception:
            continue
    
    if not top_module_candidates:
        return (False, "", f"Could not find file containing module {top_module}")
    
    # If only one candidate, use it directly
    if len(top_module_candidates) == 1:
        top_module_file = top_module_candidates[0]
        print(f"[INFO] Top module found in: {top_module_file}")
    else:
        # Multiple candidates found - try each one until one succeeds (like Verilator)
        print(f"[INFO] Found {len(top_module_candidates)} files containing '{top_module}', trying each...")
        
        # Sort candidates by preference: Core/Core_v2 directories first
        def score_candidate(candidate):
            path_lower = candidate.lower().replace('\\', '/')
            score = 0
            if '/core/' in path_lower or '/core_v2/' in path_lower:
                # But not subdirectories like /cache_config/
                if not any(subdir in path_lower for subdir in ['/cache_config/', '/debug_module/', '/near_mem']):
                    score += 100
            # Prefer shorter paths (likely more direct)
            score -= path_lower.count('/')
            return score
        
        sorted_candidates = sorted(top_module_candidates, key=score_candidate, reverse=True)
        
        successful_result = None
        
        for idx, candidate in enumerate(sorted_candidates):
            print(f"[INFO]   Trying candidate {idx+1}/{len(sorted_candidates)}: {candidate}")
            
            # Try to compile this candidate with full iterative dependency resolution
            result = _try_compile_with_iterations(
                directory, top_module, candidate, bsv_files, timeout, search_paths, max_iterations=15
            )
            
            if result[0]:  # Success
                print(f"[INFO]   ✓ Candidate {idx+1} compiled successfully!")
                return result
            else:
                # Check error type
                error_msg = result[2]
                if "Cannot find package" in error_msg or "Unbound" in error_msg:
                    print(f"[INFO]   ✗ Candidate {idx+1} has unresolvable dependency errors")
                    # Store as potential fallback
                    if not successful_result:
                        successful_result = result
                else:
                    print(f"[INFO]   ✗ Candidate {idx+1} has fatal errors")
        
        # All candidates failed, return the last result (or first with dependency errors)
        if successful_result:
            return successful_result
        
        return (False, "", f"All {len(sorted_candidates)} candidates for '{top_module}' failed to compile")
    
    # Single candidate path - use the helper function with full iteration
    return _try_compile_with_iterations(directory, top_module, top_module_file, bsv_files, timeout, search_paths, max_iterations=15)


def process_bluespec_project(
    directory: str,
    repo_name: str = None
) -> Dict:
    """Process a Bluespec project end-to-end.
    
    Args:
        directory (str): Root directory of the Bluespec project
        repo_name (str): Repository name for heuristics
        
    Returns:
        Dict: Configuration dictionary with project information
    """
    print(f"[INFO] Processing Bluespec project: {directory}")
    
    # Step 1: Find BSV files
    bsv_files = find_bsv_files(directory)
    print(f"[INFO] Found {len(bsv_files)} BSV files")
    
    if not bsv_files:
        return {'error': 'No BSV files found'}
    
    # Step 2: Extract Bluespec modules
    modules = extract_bluespec_modules(bsv_files)
    print(f"[INFO] Found {len(modules)} Bluespec modules")
    
    if not modules:
        return {'error': 'No Bluespec modules found'}
    
    # Step 3: Extract interfaces (for documentation)
    interfaces = extract_interfaces(bsv_files)
    print(f"[INFO] Found {len(interfaces)} interfaces")
    
    # Step 4: Build dependency graph
    module_graph, module_graph_inverse = build_bluespec_dependency_graph(modules)
    
    # Step 5: Identify top module
    top_module = find_top_module(module_graph, module_graph_inverse, modules, repo_name)
    
    if not top_module:
        return {'error': 'Could not identify top module'}
    
    print(f"[INFO] Top module: {top_module}")
    
    # Step 6: Compile to Verilog
    success, verilog_file, log = compile_to_verilog(directory, top_module, bsv_files)
    
    # Generate pre_script for bsc compilation
    # Find the file containing the top module
    top_module_file = None
    for name, path in modules:
        if name == top_module:
            top_module_file = os.path.relpath(path, directory)
            break
    
    pre_script = None
    if top_module_file:
        # Generate bsc command that will be run before simulation
        # This allows re-compilation if source files change
        pre_script = f'bsc -verilog -g {top_module} -u -aggressive-conditions -p .:%/Libraries {top_module_file}'
    
    if not success:
        print(f"[ERROR] Failed to compile to Verilog:\n{log}")
        return {
            'name': repo_name or os.path.basename(directory),
            'folder': os.path.basename(directory),
            'files': [],
            'source_files': [os.path.relpath(path, directory) for name, path in modules],
            'top_module': top_module,
            'repository': "",
            'pre_script': pre_script,
            'is_simulable': False,
            'error': f'Compilation failed: {log}'
        }
    
    # Build configuration
    config = {
        'name': repo_name or os.path.basename(directory),
        'folder': os.path.basename(directory),
        'files': [os.path.relpath(verilog_file, directory)] if verilog_file else [],
        'source_files': [os.path.relpath(path, directory) for name, path in modules],
        'top_module': top_module,
        'repository': "",
        'pre_script': pre_script,
        'interfaces': [name for name, _ in interfaces],
        'is_simulable': success
    }
    
    return config
