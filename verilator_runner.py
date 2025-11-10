"""
Incremental Verilator runner - bottom-up dependency resolution.

Instead of starting with all files and removing problematic ones,
this approach starts with just the top module and incrementally adds
only the files that are actually needed based on Verilator's error messages.

Strategy:
1. Start with only the top module file
2. Run Verilator and parse errors for missing modules/packages/includes
3. Add only the files that provide those missing dependencies
4. Repeat until no more dependencies are needed or we hit a failure

This avoids the cascading exclusion problem by never adding files we don't need.
"""
from __future__ import annotations
from typing import List, Tuple, Set, Dict, Optional
import os
import re
import time
import subprocess

from core.log import print_green, print_yellow, print_red, print_blue
from core.file_manager import find_missing_modules, find_missing_module_files


def _detect_systemverilog_keyword_conflict(log_text: str) -> bool:
    """
    Detect if errors are caused by SystemVerilog reserved keywords being used as identifiers.
    Common keywords: dist, randomize, constraint, covergroup, inside, with, etc.
    
    Returns True if we should retry with plain Verilog mode.
    """
    # Pattern: syntax error, unexpected <KEYWORD>, expecting IDENTIFIER
    # This indicates the code uses a SystemVerilog keyword as an identifier
    sv_keywords = [
        'dist', 'randomize', 'constraint', 'covergroup', 'inside', 'with',
        'foreach', 'unique', 'priority', 'final', 'alias', 'matches',
        'tagged', 'extern', 'pure', 'context', 'solve', 'before', 'after'
    ]
    
    for keyword in sv_keywords:
        # Pattern: "syntax error, unexpected <keyword>, expecting IDENTIFIER"
        pattern = rf"syntax error, unexpected {keyword}, expecting IDENTIFIER"
        if re.search(pattern, log_text, re.IGNORECASE):
            print_yellow(f"[INCREMENTAL] Detected SystemVerilog keyword conflict: '{keyword}' used as identifier")
            return True
    
    return False


def _normalize_path(path: str, repo_root: str) -> str:
    """Normalize a file path to be relative to repo_root."""
    try:
        if os.path.isabs(path):
            return os.path.relpath(path, repo_root).replace("\\", "/")
        return path.replace("\\", "/")
    except Exception:
        return path.replace("\\", "/")


def _run(cmd: List[str], cwd: str, timeout: int = 300) -> Tuple[int, str]:
    """Run a command and capture output."""
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        output_lines = []
        start = time.time()
        
        while True:
            if proc.poll() is not None:
                # Process finished
                remaining = proc.stdout.read()
                if remaining:
                    output_lines.append(remaining)
                break
            
            line = proc.stdout.readline()
            if line:
                output_lines.append(line)
                print(line, end='')
            
            if time.time() - start > timeout:
                proc.kill()
                output_lines.append(f"\n[TIMEOUT] Process killed after {timeout}s\n")
                break
        
        return proc.returncode or 0, "".join(output_lines)
    except Exception as e:
        return 1, f"[EXCEPTION] {e}"


def _parse_missing_modules(log_text: str) -> List[str]:
    """Extract missing module names from Verilator errors."""
    missing = set()
    patterns = [
        r"Cannot find file containing module: '([^']+)'",
        r'Cannot find file containing module: "([^"]+)"',
        r"Can't resolve module reference: '([^']+)'",  # For "Can't resolve module reference: 'module_name'"
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing.add(m.group(1))
    return list(missing)


def _parse_missing_packages(log_text: str) -> List[str]:
    """Extract missing package names from Verilator errors."""
    missing = set()
    patterns = [
        r"Package/class '([^']+)' not found",
        r"%Error-PKGNODECL:\s*[^:]+:\d+:\d+:\s*Package/class '([^']+)' not found",
        r"Importing from missing package '([^']+)'",  # For "Importing from missing package 'pkg_name'"
        r"Can't find typedef/interface:\s*'([^']+)'",  # Typedefs often come from packages
        r"Package/class for ':: reference' not found:\s*'([^']+)'",  # For namespace reference errors
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing.add(m.group(1))
    return list(missing)


def _parse_package_scope_references(log_text: str) -> List[str]:
    """
    Extract package names from scope resolution syntax errors (pkg::identifier).
    When Verilator sees 'pkg_name::something' but pkg_name is not defined,
    it reports "syntax error, unexpected ':'" - we can detect the package name
    from the source line shown in the error.
    """
    missing = set()
    # Look for patterns like: "localparam X = pkg_name::Something"
    # The error will show the line with the :: usage
    pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)::'
    for m in re.finditer(pattern, log_text):
        pkg_name = m.group(1)
        # Filter out common non-package prefixes
        if pkg_name not in ['std', 'this', 'super', 'local']:
            missing.add(pkg_name)
    return list(missing)


def _parse_missing_includes(log_text: str) -> List[str]:
    """Extract missing include file names from Verilator errors."""
    missing = set()
    patterns = [
        r"Cannot find include file: ['\"]([^'\"]+)['\"]",
        r"can't find file \"([^\"]+)\"",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing.add(m.group(1))
    return list(missing)


def _parse_missing_interfaces(log_text: str) -> List[str]:
    """Extract missing interface names from Verilator errors."""
    missing = set()
    patterns = [
        r"Cannot find file containing interface: '([^']+)'",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing.add(m.group(1))
    return list(missing)


def _parse_included_files_with_errors(log_text: str, repo_root: str) -> List[str]:
    """
    Extract files that have typedef/package errors and are included from other files.
    These files (especially interfaces) often need to be compiled as standalone files.
    
    Pattern:
        %Error: path/to/file.sv:30:5: Can't find typedef/interface: 'TypeName'
           30 |     TypeName variable;
              |     ^~~~~~~~~
                parent/file.sv:110:1: ... note: In file included from 'parent.sv'
    
    Returns list of relative file paths that should be added to compilation.
    """
    files = set()
    # Pattern to match error in a file followed by "included from" note (with possible intervening lines)
    # Capture the file with the error
    pattern = r"%Error:\s*([a-zA-Z0-9_/.\\-]+\.sv[h]?):\d+:\d+:\s*Can't find (?:typedef/interface|package)[^\n]*(?:\n(?!%Error:)[^\n]*){0,5}?In file included from"
    
    for m in re.finditer(pattern, log_text, flags=re.MULTILINE):
        file_path = m.group(1)
        # Normalize path relative to repo_root
        rel_path = _normalize_path(file_path, repo_root)
        files.add(rel_path)
    
    return list(files)


def _parse_missing_interfaces(log_text: str) -> List[str]:
    """Extract missing interface names from Verilator errors."""
    missing = set()
    patterns = [
        r"Cannot find file containing interface: '([^']+)'",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing.add(m.group(1))
    return list(missing)


def _parse_forward_declaration_files(log_text: str, repo_root: str) -> List[str]:
    """
    Extract file paths from 'Reference before declaration' errors.
    These files contain type definitions that need to be compiled first.
    
    Example error:
        %Error: file.sv:23:14: Reference to 'bp_params_e' before declaration
            file.sv:599:5: ... Location of original declaration
    
    Returns list of relative file paths that need to be added to compilation.
    """
    files = set()
    # Pattern: ... Location of original declaration
    # Followed by filename:line:col on next line
    pattern = r"Location of original declaration\s*\n\s*(\d+)\s*\|\s*"
    
    # Alternative pattern: look for lines with file paths after "Location of" messages
    # Format:     bp_common/src/include/file.svh:599:5: ... Location of original declaration
    decl_pattern = r"^\s*([a-zA-Z0-9_/.\\-]+\.[sv]+h?):\d+:\d+:.*Location of original declaration"
    
    for m in re.finditer(decl_pattern, log_text, flags=re.MULTILINE):
        file_path = m.group(1)
        # Normalize path relative to repo_root
        rel_path = _normalize_path(file_path, repo_root)
        files.add(rel_path)
    
    return list(files)


def _parse_missing_import_packages(log_text: str) -> List[str]:
    """Extract package names from 'Import package not found' errors."""
    missing = set()
    pattern = r"Import package not found: '([^']+)'"
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        missing.add(m.group(1))
    return list(missing)


def _parse_missing_defines(log_text: str) -> List[str]:
    """
    Extract undefined macro/define names from Verilator errors.
    
    Example error:
        %Error: rtl/nox.sv:20:38: Define or directive not defined: '`M_HART_ID'
    
    Returns list of define names (without the backtick).
    """
    missing = set()
    # Pattern: Define or directive not defined: '`NAME'
    pattern = r"Define or directive not defined:\s*'`([^']+)'"
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        missing.add(m.group(1))
    return list(missing)


def _find_header_with_define(repo_root: str, define_name: str, module_graph: Dict[str, Dict]) -> List[str]:
    """
    Find header files (.vh, .svh) that define a specific macro.
    
    Searches through all header files in the repository to find files containing
    `define MACRO_NAME definitions.
    
    Args:
        repo_root: Root directory of the repository
        define_name: Name of the define to search for (without backtick)
        module_graph: Optional module graph with file information
        
    Returns:
        List of relative paths to header files that define this macro
    """
    candidates = []
    
    # Pattern to match: `define MACRO_NAME
    pattern = re.compile(rf'^\s*`define\s+{re.escape(define_name)}\b', re.IGNORECASE | re.MULTILINE)
    
    # Search through the repository for header files
    for root, dirs, files in os.walk(repo_root):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {'.git', 'obj_dir', 'build', 'sim_build', '__pycache__'}]
        
        for file in files:
            if not (file.endswith('.vh') or file.endswith('.svh') or file.endswith('.v') or file.endswith('.sv')):
                continue
            
            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if pattern.search(content):
                        # Convert to relative path
                        rel_path = os.path.relpath(full_path, repo_root)
                        candidates.append(rel_path)
                        print_yellow(f"[INCREMENTAL] Found define '{define_name}' in: {rel_path}")
            except Exception:
                continue
    
    return candidates


def _find_package_including_file(repo_root: str, include_file: str, module_graph: Dict[str, Dict]) -> List[str]:
    """
    Find package (.sv) files that include a given .svh file.
    
    When a .svh file contains typedefs used before declaration, we need to compile
    the package file that includes it, not the .svh itself.
    
    Args:
        repo_root: Repository root
        include_file: Relative path to .svh file (e.g., "bp_common/src/include/bp_common_aviary_pkgdef.svh")
        module_graph: Module dependency graph
    
    Returns:
        List of package files (.sv) that include this file
    """
    package_files: List[str] = []
    include_basename = os.path.basename(include_file)

    # Always use filesystem fallback as it's more reliable than module_graph for this use case
    # Scan the repository filesystem for .sv files that include the .svh
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in {'.git', 'obj_dir', 'build', 'out'}]
        for fname in files:
            if not fname.lower().endswith('.sv'):
                continue
            full_path = os.path.join(root, fname)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read(50000)
                    include_pattern = re.compile(rf'`include\s+["\']([^"\']*{re.escape(include_basename)})["\']', re.IGNORECASE)
                    if include_pattern.search(content) and re.search(r'^\s*package\s+\w+\s*;', content, re.MULTILINE | re.IGNORECASE):
                        rel = _normalize_path(os.path.relpath(full_path, repo_root), repo_root)
                        package_files.append(rel)
            except Exception:
                continue

    return package_files


def _find_file_declaring_module(repo_root: str, module_name: str, module_graph: Dict[str, Dict]) -> List[str]:
    """
    Find file(s) that declare a given module using the module graph.
    
    Args:
        repo_root: Repository root path
        module_name: Name of the module to find
        module_graph: Module dependency graph from config_generator_core
    
    Returns:
        List of relative paths to files declaring the module (may be empty or have multiple)
    """
    if not module_graph:
        # Fallback to file system search
        return _find_file_by_search(repo_root, module_name, "module")
    
    # Search in the module graph
    found_files = []
    for file_path, info in module_graph.items():
        if 'modules' in info and module_name in info['modules']:
            found_files.append(_normalize_path(file_path, repo_root))
    
    if found_files:
        return found_files
    
    # Module not in graph, try file search fallback
    return _find_file_by_search(repo_root, module_name, "module")


def _find_file_declaring_package(repo_root: str, package_name: str, module_graph: Dict[str, Dict]) -> List[str]:
    """Find the file(s) that declare a given package. Returns list of file paths (can be multiple for versioned packages)."""
    if not module_graph:
        return _find_file_by_search(repo_root, package_name, "package")
    
    # Search in the module graph - collect ALL files that declare this package
    found_files = []
    for file_path, info in module_graph.items():
        if 'packages' in info and package_name in info['packages']:
            rel_path = _normalize_path(file_path, repo_root)
            found_files.append(rel_path)
    
    if found_files:
        return found_files
    
    # Package not in graph, try file search fallback
    return _find_file_by_search(repo_root, package_name, "package")


def _find_file_declaring_interface(repo_root: str, interface_name: str, module_graph: Dict[str, Dict]) -> List[str]:
    """Find the file(s) that declare a given interface. Returns list of file paths."""
    if not module_graph:
        return _find_file_by_search(repo_root, interface_name, "interface")
    
    # Search in the module graph
    found_files = []
    for file_path, info in module_graph.items():
        if 'interfaces' in info and interface_name in info['interfaces']:
            found_files.append(_normalize_path(file_path, repo_root))
    
    if found_files:
        return found_files
    
    # Interface not in graph, try file search fallback
    return _find_file_by_search(repo_root, interface_name, "interface")


def _find_file_by_search(repo_root: str, symbol_name: str, symbol_type: str) -> List[str]:
    """
    Fallback: search the repository for files declaring the given symbol.
    
    Args:
        repo_root: Repository root
        symbol_name: Name of the symbol (module/package/interface)
        symbol_type: Type of symbol ("module", "package", or "interface")
    
    Returns:
        List of relative paths to files (may be empty or have multiple matches)
    """
    # Build search patterns - for modules, also try interface since Verilator
    # sometimes reports missing interfaces as missing modules
    patterns = []
    if symbol_type == "module":
        # Try both module and interface patterns
        patterns.append(re.compile(rf"^\s*module\s+{re.escape(symbol_name)}\b", re.IGNORECASE | re.MULTILINE))
        patterns.append(re.compile(rf"^\s*interface\s+{re.escape(symbol_name)}\b", re.IGNORECASE | re.MULTILINE))
    else:
        # For package and interface, use exact type
        patterns.append(re.compile(rf"^\s*{symbol_type}\s+{re.escape(symbol_name)}\b", re.IGNORECASE | re.MULTILINE))
    
    found_files = []
    
    for root, dirs, files in os.walk(repo_root):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {'.git', 'obj_dir', 'build', 'out'}]
        
        for fname in files:
            if not fname.endswith(('.sv', '.v', '.svh', '.vh')):
                continue
            
            full_path = os.path.join(root, fname)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()  # Read entire file
                    # Check if any pattern matches
                    for pattern in patterns:
                        if pattern.search(content):
                            found_files.append(_normalize_path(full_path, repo_root))
                            break  # Found in this file, no need to check other patterns
            except Exception:
                continue
    
    return found_files


def _find_package_with_typedef(repo_root: str, typedef_name: str, module_graph: Dict[str, Dict]) -> List[str]:
    """
    Find the package file(s) that contain a given typedef/struct.
    
    When Verilator reports "Can't find typedef/interface: 'TypeName'", the type might be 
    defined inside a package. This function searches for files containing the typedef and 
    determines which package declares it.
    
    Args:
        repo_root: Repository root
        typedef_name: Name of the typedef (e.g., 'BypassControll')
        module_graph: Module dependency graph
    
    Returns:
        List of file paths declaring the package containing this typedef
    """
    # Search for files containing this typedef
    # Pattern matches:
    # 1. } TypeName; (closing brace of struct/enum/union)
    # 2. typedef struct/enum/union ... TypeName;
    typedef_pattern = re.compile(
        rf'\}}\s*{re.escape(typedef_name)}\s*;'  # } TypeName;
        rf'|typedef\s+(?:struct|enum|union)\s+.*\s+{re.escape(typedef_name)}\s*;'  # typedef struct/enum/union ... TypeName;
        , 
        re.MULTILINE | re.IGNORECASE
    )
    
    package_pattern = re.compile(r'^\s*package\s+(\w+)\s*;', re.MULTILINE)
    
    found_packages = set()
    files_searched = 0
    matches_found = 0
    
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in {'.git', 'obj_dir', 'build', 'out'}]
        
        for fname in files:
            if not fname.endswith(('.sv', '.svh')):
                continue
            
            files_searched += 1
            full_path = os.path.join(root, fname)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Check if this file contains the typedef
                    if typedef_pattern.search(content):
                        matches_found += 1
                        # Find which package this typedef is in
                        pkg_match = package_pattern.search(content)
                        if pkg_match:
                            package_name = pkg_match.group(1)
                            # Now find the file declaring this package
                            pkg_files = _find_file_declaring_package(repo_root, package_name, module_graph)
                            if pkg_files:
                                found_packages.update(pkg_files)
                            else:
                                print_yellow(f"[INCREMENTAL] Found typedef '{typedef_name}' in package '{package_name}', but package file not found")
                        else:
                            print_yellow(f"[INCREMENTAL] Found typedef '{typedef_name}' in {os.path.relpath(full_path, repo_root)}, but no package declaration")
            except Exception as e:
                continue
    
    if not found_packages:
        print_yellow(f"[INCREMENTAL] Searched {files_searched} files ({matches_found} matches), typedef '{typedef_name}' package not found")
    
    return list(found_packages)


def _find_include_file(repo_root: str, include_name: str, current_includes: Set[str]) -> Optional[str]:
    """
    Find an include file by searching include directories.
    
    Returns the include directory containing the file (to be added to -I flags).
    """
    # First check existing include directories
    for inc_dir in current_includes:
        full_inc_dir = os.path.join(repo_root, inc_dir) if not os.path.isabs(inc_dir) else inc_dir
        potential_file = os.path.join(full_inc_dir, include_name)
        if os.path.exists(potential_file):
            return inc_dir
    
    # Search the entire repository
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in {'.git', 'obj_dir', 'build', 'out'}]
        
        if include_name in files:
            rel_dir = _normalize_path(root, repo_root)
            return rel_dir
    
    return None


def _is_pkg_file(path: str) -> bool:
    """Heuristic: treat files that define packages as package files.
    Common convention is *_pkg.sv or *_pkg.svh. Many repos also use *_types.sv or *_config*.sv.
    Also catch paths with '/pkg/' in them.
    """
    p = path.lower()
    base = os.path.basename(p)
    return (
        base.endswith("_pkg.sv")
        or base.endswith("_pkg.svh")
        or base.endswith("_types.sv")
        or base.endswith("types.sv")
        or base.endswith("_types.svh")
        or base.endswith("types.svh")
        or base.endswith("_config.sv")
        or base.endswith("_config.svh")
        or "config_and_types" in base
        or "/pkg/" in p.replace("\\", "/")
    )


def _order_sv_files(files: List[str], repo_root: str | None = None) -> List[str]:
    """Order SV files generically so that package providers compile before importers.

    Generic algorithm:
    - Detect which of the given files declare a SystemVerilog package.
    - Parse "import <pkg>::*;" and similar forms in all files to build a dependency graph
      between files via package usage.
    - Detect explicit ordering constraints via `ifdef/`ifndef with `error directives.
    - Topologically sort files so that package definitions appear before files that import them.
    - Fall back to a heuristic (package-like files first) when content can't be read.
    """

    if not repo_root:
        # Fallback: simple, generic package-first ordering without hard-coded names
        indexed = list(enumerate(files))
        indexed.sort(key=lambda t: (0 if _is_pkg_file(t[1]) else 1, t[0]))
        return [f for _i, f in indexed]

    # Build mapping: package name -> file declaring it (within the provided file set)
    pkg_decl_re = re.compile(r"^\s*package\s+(\w+)\s*;", re.IGNORECASE | re.MULTILINE)
    import_re = re.compile(r"^\s*import\s+([a-zA-Z_]\w*)\s*::\s*\*\s*;", re.IGNORECASE | re.MULTILINE)
    # Also catch inline/import lists: import a::*, b::*;
    import_list_re = re.compile(r"^\s*import\s+([^;]+);", re.IGNORECASE | re.MULTILINE)
    # Detect namespace references like package_name::type_name
    namespace_ref_re = re.compile(r"\b([a-zA-Z_]\w+)::[a-zA-Z_]\w+", re.MULTILINE)
    # Detect explicit ordering constraints: `ifdef DEFINE + `error means this file must come before files defining DEFINE
    ifdef_error_re = re.compile(r"^\s*`ifdef\s+(\w+)\s*\n\s*`error", re.IGNORECASE | re.MULTILINE)
    # Detect define declarations
    define_re = re.compile(r"^\s*`define\s+(\w+)", re.IGNORECASE | re.MULTILINE)
    # Detect typedef declarations (enum, struct, union) - these need to be compiled before use
    typedef_re = re.compile(r"^\s*}\s*(\w+)\s*;", re.IGNORECASE | re.MULTILINE)  # } type_name;
    # Detect parameter type usage: parameter TYPE_NAME param_name = ...
    param_type_re = re.compile(r"^\s*#?\s*\(\s*parameter\s+([a-zA-Z_]\w+)\s+", re.IGNORECASE | re.MULTILINE)

    file_to_imports: Dict[str, Set[str]] = {f: set() for f in files}
    pkg_to_file: Dict[str, str] = {}
    # Map: define name -> file that defines it
    define_to_file: Dict[str, str] = {}
    # Map: file -> set of defines it requires to NOT be defined yet (must come before definer)
    file_to_forbidden_defines: Dict[str, Set[str]] = {f: set() for f in files}
    # Map: typedef name -> file that defines it
    typedef_to_file: Dict[str, str] = {}
    # Map: file -> set of typedefs it uses as parameter types
    file_to_param_types: Dict[str, Set[str]] = {f: set() for f in files}

    def _read(rel_path: str) -> str:
        p = os.path.join(repo_root, rel_path)
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                return fh.read()
        except Exception:
            return ""

    # Track any files that declare a package (provider files)
    provider_files: Set[str] = set()

    for f in files:
        text = _read(f)
        if not text:
            continue
        # Package declarations in this file
        for m in pkg_decl_re.finditer(text):
            pkg = m.group(1)
            # only first package per file is considered for mapping
            if pkg and pkg not in pkg_to_file:
                pkg_to_file[pkg] = f
                provider_files.add(f)
                break
        # Define declarations in this file
        for m in define_re.finditer(text):
            define = m.group(1)
            if define and define not in define_to_file:
                define_to_file[define] = f
        # Typedef declarations in this file (enum, struct, union)
        for m in typedef_re.finditer(text):
            typedef = m.group(1)
            if typedef and typedef not in typedef_to_file:
                typedef_to_file[typedef] = f
        # Explicit ordering constraints: ifdef + error means must come before definer
        for m in ifdef_error_re.finditer(text):
            define = m.group(1)
            if define:
                file_to_forbidden_defines[f].add(define)
        # Parameter type usage: #(parameter TYPE_NAME param_name = ...)
        for m in param_type_re.finditer(text):
            param_type = m.group(1)
            # Filter out built-in types and common parameter patterns
            if param_type not in ['int', 'integer', 'logic', 'bit', 'reg', 'wire', 'real', 'string', 'signed', 'unsigned']:
                file_to_param_types[f].add(param_type)
    # Collect imports per file
    for f in files:
        text = _read(f)
        if not text:
            continue
        # Fast path for common form
        for m in import_re.finditer(text):
            file_to_imports[f].add(m.group(1))
        # Handle list imports (import a::*, b::c, d::*;)
        for m in import_list_re.finditer(text):
            part = m.group(1)
            # Split by comma and extract package names before '::'
            for seg in part.split(','):
                seg = seg.strip()
                if '::' in seg:
                    pkg = seg.split('::', 1)[0].strip()
                    if re.match(r"^[a-zA-Z_]\w*$", pkg):
                        file_to_imports[f].add(pkg)
        # Detect namespace references (package_name::identifier)
        # This catches cases where packages are used without explicit import
        for m in namespace_ref_re.finditer(text):
            pkg = m.group(1)
            # Only consider it if the package exists in our file set
            # and it's not a common false positive (like $unit::, etc.)
            if pkg not in ['$unit', 'std', 'this', 'super', 'local'] and pkg in pkg_to_file:
                file_to_imports[f].add(pkg)

    # Build graph: edge from provider file -> importer file
    nodes = list(files)
    index_map = {f: i for i, f in enumerate(nodes)}  # for stable tie-breaks
    adj: Dict[str, Set[str]] = {f: set() for f in nodes}
    indeg: Dict[str, int] = {f: 0 for f in nodes}

    # Add edges for package imports
    for f, imports in file_to_imports.items():
        for pkg in imports:
            provider = pkg_to_file.get(pkg)
            if provider and provider != f:
                if f not in adj[provider]:
                    adj[provider].add(f)
                    indeg[f] += 1

    # Add edges for explicit ordering constraints (ifdef + error)
    # If file A checks ifdef DEFINE and errors, and file B defines DEFINE,
    # then A must come before B: add edge A -> B
    for f, forbidden in file_to_forbidden_defines.items():
        for define in forbidden:
            definer = define_to_file.get(define)
            if definer and definer != f:
                if definer not in adj[f]:
                    adj[f].add(definer)
                    indeg[definer] += 1

    # Add edges for typedef dependencies
    # If file A uses a typedef as a parameter type, and file B defines that typedef,
    # then B must come before A: add edge B -> A
    for f, param_types in file_to_param_types.items():
        for typedef in param_types:
            definer = typedef_to_file.get(typedef)
            if definer and definer != f:
                if f not in adj[definer]:
                    adj[definer].add(f)
                    indeg[f] += 1

    # Kahn's algorithm for topo sort, preserving original order among equals
    zero_indeg = sorted([n for n in nodes if indeg[n] == 0], key=lambda x: index_map[x])
    ordered: List[str] = []
    while zero_indeg:
        n = zero_indeg.pop(0)
        ordered.append(n)
        for m in sorted(adj[n], key=lambda x: index_map[x]):
            indeg[m] -= 1
            if indeg[m] == 0:
                zero_indeg.append(m)
                zero_indeg.sort(key=lambda x: index_map[x])

    if len(ordered) != len(nodes):
        # Cycle or unreadable content; append remaining by original order to avoid loss
        remaining = [n for n in nodes if n not in ordered]
        remaining.sort(key=lambda x: index_map[x])
        ordered.extend(remaining)

    # As a final gentle nudge, ensure actual package-declaring files (by content)
    # appear as early as possible without violating the topo order: stable partition.
    # If we failed to read contents (empty provider set), fallback to filename heuristics.
    if not provider_files:
        pkg_like = [f for f in ordered if _is_pkg_file(f)]
        non_pkg = [f for f in ordered if not _is_pkg_file(f)]
        return pkg_like + non_pkg
    else:
        pkg_like = [f for f in ordered if f in provider_files]
        non_pkg = [f for f in ordered if f not in provider_files]
        return pkg_like + non_pkg


def _has_sv_keyword_as_identifier(repo_root: str, files: List[str]) -> bool:
    """
    Check if files use SystemVerilog keywords as identifiers (like block labels, variable names, etc.).
    Common problematic keywords: dist, randomize, constraint, etc.
    """
    import re
    
    # SystemVerilog keywords that might be used as identifiers in Verilog code
    # Note: 'bit' and 'logic' are removed since they're fundamental SV types and often used correctly
    # Note: 'with' is removed since it matches comments too often
    sv_keywords = ['dist', 'randomize', 'constraint', 'covergroup', 'coverpoint', 
                   'bins', 'illegal_bins', 'ignore_bins', 'cross', 
                   'matches', 'inside', 'tagged', 'priority', 'unique']
    
    # Pattern to detect keyword used as identifier (e.g., "begin:dist", "wire dist", "reg [7:0] bit", etc.)
    identifier_patterns = [
        re.compile(r'\bbegin\s*:\s*(' + '|'.join(sv_keywords) + r')\b', re.I),  # begin:keyword
        re.compile(r'\b(wire|reg|logic|input|output|inout)(\s+\[[^\]]+\])?\s+(' + '|'.join(sv_keywords) + r')\b', re.I),  # wire keyword or reg [N:0] keyword
        re.compile(r'\bparameter\s+(' + '|'.join(sv_keywords) + r')\s*=', re.I),  # parameter keyword =
    ]
    
    print_blue(f"[KEYWORD CHECK] Checking {len(files)} files for SV keywords as identifiers")
    for file_rel in files:
        file_path = os.path.join(repo_root, file_rel) if not os.path.isabs(file_rel) else file_rel
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for pattern in identifier_patterns:
                    match = pattern.search(content)
                    if match:
                        print_yellow(f"[KEYWORD CHECK] FOUND SV keyword in {file_rel}: {match.group(0)}")
                        return True
        except Exception:
            continue
    
    return False


def _detect_language_for_files(repo_root: str, files: List[str], module_graph: Dict[str, Dict] = None, include_dirs: Set[str] = None) -> str:
    """
    Detect the appropriate language version for the given files.
    This checks for SystemVerilog features (logic, interface, always_ff, etc.) in the actual files.
    Also checks for SystemVerilog keywords used as identifiers, which requires Verilog mode.
    
    Order matters: Check for SV features FIRST, then check for keyword conflicts.
    This way, files with legitimate SV features get SV mode even if they use keywords as identifiers.
    
    If module_graph is provided, also checks all dependency files (recursively).
    If include_dirs is provided, also checks all .v/.sv files in those directories.
    """
    import re
    
    # Collect all files to check: direct files + dependencies from module graph + files in include dirs
    files_to_check = set(files)
    
    if module_graph:
        # For each file in our compilation list, add all its dependencies
        def collect_dependencies(file_path: str, visited: Set[str]):
            if file_path in visited:
                return
            visited.add(file_path)
            
            if file_path in module_graph:
                info = module_graph[file_path]
                # Add files from dependencies (modules, includes, etc.)
                for dep_file in info.get('files', []):
                    if dep_file not in visited:
                        files_to_check.add(dep_file)
                        collect_dependencies(dep_file, visited)
        
        visited = set()
        for file_path in files:
            collect_dependencies(file_path, visited)
    
    # Add all .v/.sv files from include directories
    if include_dirs:
        for inc_dir in include_dirs:
            full_inc_dir = os.path.join(repo_root, inc_dir) if not os.path.isabs(inc_dir) else inc_dir
            if os.path.isdir(full_inc_dir):
                try:
                    for file in os.listdir(full_inc_dir):
                        if file.endswith(('.v', '.sv', '.svh')):
                            # Use relative path from repo_root
                            rel_path = os.path.join(inc_dir, file) if not os.path.isabs(inc_dir) else os.path.join(full_inc_dir, file)
                            files_to_check.add(rel_path)
                except Exception:
                    pass
    
    # Also scan all .v/.sv files in the same directories as files we're compiling
    # This catches cases where files in the same directory might use SV keywords but aren't in the initial list
    scanned_dirs = set()
    initial_file_count = len(files_to_check)
    for file_rel in list(files_to_check):
        file_dir = os.path.dirname(file_rel)
        if file_dir and file_dir not in scanned_dirs:
            scanned_dirs.add(file_dir)
            full_dir = os.path.join(repo_root, file_dir) if not os.path.isabs(file_dir) else file_dir
            if os.path.isdir(full_dir):
                try:
                    dir_files = []
                    for file in os.listdir(full_dir):
                        if file.endswith(('.v', '.sv', '.svh')):
                            rel_path = os.path.join(file_dir, file) if file_dir else file
                            if rel_path not in files_to_check:
                                dir_files.append(file)
                            files_to_check.add(rel_path)
                    if dir_files:
                        print_blue(f"[LANG DETECT]   Dir {file_dir}: added {dir_files}")
                except Exception:
                    pass
    
    # FIRST: Check for keyword conflicts (highest priority)
    # Plain Verilog code using SV keywords as identifiers must use Verilog mode
    has_keyword_conflict = _has_sv_keyword_as_identifier(repo_root, list(files_to_check))
    if has_keyword_conflict:
        return "1364-2005"
    
    # SECOND: Check for SystemVerilog features
    # If no keyword conflicts but has SV features, use SystemVerilog mode
    has_sv_features = False
    has_logic_keyword = False
    has_interface = False
    has_always_ff = False
    
    print_blue(f"[LANG DETECT] No keyword conflicts, checking {len(files_to_check)} files for SV features...")
    
    # Patterns for SystemVerilog features
    sv_patterns = {
        'logic': re.compile(r'\blogic\b', re.I),
        'interface': re.compile(r'\binterface\b|\bmodport\b', re.I),
        'always_ff': re.compile(r'\balways_ff\b|\balways_comb\b|\balways_latch\b', re.I),
        'class': re.compile(r'\bclass\b', re.I),
        'typedef_struct': re.compile(r'\btypedef\s+(enum|struct|union)', re.I),
    }
    
    for file_rel in files_to_check:
        file_path = os.path.join(repo_root, file_rel) if not os.path.isabs(file_rel) else file_rel
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Check for SystemVerilog features
                if sv_patterns['logic'].search(content):
                    has_logic_keyword = True
                    has_sv_features = True
                if sv_patterns['interface'].search(content):
                    has_interface = True
                    has_sv_features = True
                if sv_patterns['always_ff'].search(content):
                    has_always_ff = True
                    has_sv_features = True
                if sv_patterns['class'].search(content):
                    has_sv_features = True
                if sv_patterns['typedef_struct'].search(content):
                    has_sv_features = True
                    
        except Exception as e:
            continue
    
    # If we found SV features, use SystemVerilog mode
    if has_sv_features:
        return "1800-2023"
    
    print_blue(f"[LANG DETECT] No SV features found either")
    # Check file extensions
    has_sv_ext = any(f.endswith(('.sv', '.svh')) for f in files_to_check)
    if has_sv_ext:
        return "1800-2023"
    
    return "1364-2005"  # Default to Verilog-2005


def _build_verilator_cmd(
    repo_root: str,
    files: List[str],
    include_dirs: Set[str],
    top_module: str,
    language_version: str = "1800-2023",
    extra_flags: List[str] = None,
    module_graph: Dict[str, Dict] = None
) -> List[str]:
    """Build the Verilator command line."""
    cmd = [
        "verilator",
        "--lint-only",
        "-Wall",
        "--no-timing",
        "-Wno-PROCASSWIRE",
        "--relative-includes",
        "-DEN_EXCEPT",
        "-DEN_RVZICSR",
    ]
    
    # Dynamically detect language for current file set AND their dependencies from module graph
    # Also check files in include directories
    detected_lang = _detect_language_for_files(repo_root, files, module_graph, include_dirs)
    
    # Always set the language version
    cmd.extend(["--language", detected_lang])
    
    # Additionally, if SystemVerilog features detected, add --sv flag
    if detected_lang.startswith("1800"):
        cmd.append("--sv")
    
    # Top module
    if top_module:
        cmd.extend(["--top-module", top_module])
    
    # Include directories
    for inc_dir in sorted(include_dirs):
        cmd.append(f"-I{inc_dir}")
    
    # Extra flags
    if extra_flags:
        cmd.extend(extra_flags)
    
    # Files - filter out .h files (they should be in include dirs, not compiled directly)
    # .h files in Verilog/SystemVerilog are typically config headers that need preprocessing
    compilable_files = [f for f in files if not f.endswith('.h')]
    
    # Use topological sorting to ensure packages come before importers
    ordered_files = _order_sv_files(compilable_files, repo_root)
    cmd.extend(ordered_files)
    
    return cmd


def _try_package_candidates(
    pkg_name: str,
    pkg_files: List[str],
    current_files: List[str],
    current_includes: Set[str],
    repo_root: str,
    top_module: str,
    language_version: str,
    extra_flags: List[str],
    timeout: int
) -> Optional[str]:
    """
    Try multiple package file candidates and select the best one based on scoring.
    
    Returns: The best package file path, or None if no candidate resolves the package.
    """
    if len(pkg_files) == 1:
        return pkg_files[0]
    
    print_yellow(f"[INCREMENTAL] Found {len(pkg_files)} candidates for package '{pkg_name}', trying each...")
    
    best_candidate = None
    best_score = None
    
    for idx, pkg_file in enumerate(pkg_files):
        if pkg_file in current_files:
            print_yellow(f"[INCREMENTAL]   Candidate {idx+1}/{len(pkg_files)}: {pkg_file} (already in file list)")
            return pkg_file
        
        # Try this candidate
        print_yellow(f"[INCREMENTAL]   Trying candidate {idx+1}/{len(pkg_files)}: {pkg_file}")
        test_files = current_files + [pkg_file]
        test_includes = current_includes.copy()
        
        # Add its directory as include
        pkg_dir = os.path.dirname(pkg_file)
        if pkg_dir:
            test_includes.add(pkg_dir)
        
        # Test compile with this candidate
        test_cmd = _build_verilator_cmd(repo_root, test_files, test_includes, top_module, language_version, extra_flags)
        test_rc, test_output = _run(test_cmd, repo_root, timeout)
        
        # Check if this candidate resolved the package error
        package_not_found = f"Cannot find file containing package: '{pkg_name}'" in test_output or \
                           f"Can't find package '{pkg_name}'" in test_output
        
        if not package_not_found:
            # Count errors that indicate wrong package version (can't be auto-resolved)
            undefined_vars = test_output.count("Can't find definition of variable:")
            unexpected_identifiers = test_output.count("syntax error, unexpected IDENTIFIER")
            
            # Parse remaining dependencies (just for reporting, not scoring)
            remaining_modules = _parse_missing_modules(test_output)
            remaining_packages = _parse_missing_packages(test_output)
            remaining_other = len(_parse_missing_includes(test_output)) + len(_parse_missing_interfaces(test_output))
            
            # Score: (compiles, fewer undefined vars, fewer unexpected identifiers)
            # Don't penalize missing modules/packages - those can be resolved in next iterations
            candidate_score = (
                test_rc == 0,  # True > False, so compiling is best
                -undefined_vars,  # Penalize undefined variables (missing constants)
                -unexpected_identifiers,  # Penalize unexpected identifiers (missing typedefs)
            )
            
            if test_rc == 0:
                # Perfect - compiles successfully
                print_green(f"[INCREMENTAL]   ✓ Candidate {idx+1} works perfectly for '{pkg_name}' (compiles)")
                return pkg_file
            else:
                # Package found but has errors - score it
                deps_msg = f"undef={undefined_vars}, unexpected={unexpected_identifiers}, modules={len(remaining_modules)}, packages={len(remaining_packages)}, other={remaining_other}"
                # Use different symbols based on error severity
                if undefined_vars > 10 or unexpected_identifiers > 5:
                    symbol = "⚠"  # High error count - likely wrong version
                elif undefined_vars > 0 or unexpected_identifiers > 0:
                    symbol = "~"  # Some errors - might be version mismatch
                else:
                    symbol = "✓"  # No version errors - likely good
                print_yellow(f"[INCREMENTAL]   {symbol} Candidate {idx+1} resolves '{pkg_name}' but has errors: {deps_msg}")
                if best_score is None or candidate_score > best_score:
                    best_candidate = pkg_file
                    best_score = candidate_score
        else:
            print_yellow(f"[INCREMENTAL]   ✗ Candidate {idx+1} didn't resolve '{pkg_name}'")
    
    # Report which candidate was selected
    if best_candidate:
        best_idx = pkg_files.index(best_candidate) + 1
        print_green(f"[INCREMENTAL] → Selected candidate {best_idx}/{len(pkg_files)} for '{pkg_name}': {os.path.basename(best_candidate)}")
    
    return best_candidate


def _try_module_candidates(
    mod_name: str,
    mod_files: List[str],
    current_files: List[str],
    current_includes: Set[str],
    repo_root: str,
    top_module: str,
    language_version: str,
    extra_flags: List[str],
    timeout: int,
    module_graph: Dict
) -> Tuple[Optional[str], List[str]]:
    """
    Try multiple module file candidates with dependency resolution mini-loop.
    
    Returns: (best_module_file, dependencies_to_add) or (None, []) if no candidate works.
    """
    if len(mod_files) == 1:
        return mod_files[0], []
    
    print_yellow(f"[INCREMENTAL] Found {len(mod_files)} candidates for module '{mod_name}', trying each...")
    
    best_candidate = None
    best_candidate_deps = []
    
    for idx, mod_file in enumerate(mod_files):
        if mod_file in current_files:
            print_yellow(f"[INCREMENTAL]   Candidate {idx+1}/{len(mod_files)}: {mod_file} (already in file list)")
            return mod_file, []
        
        # Try this candidate with dependency resolution
        print_yellow(f"[INCREMENTAL]   Trying candidate {idx+1}/{len(mod_files)}: {mod_file}")
        test_files = current_files + [mod_file]
        test_includes = current_includes.copy()
        candidate_added_deps = []
        
        # Add its directory as include
        mod_dir = os.path.dirname(mod_file)
        if mod_dir:
            test_includes.add(mod_dir)
        
        # Mini-loop: Try to resolve packages/includes for this candidate
        max_mini_iterations = 3
        for mini_iter in range(max_mini_iterations):
            test_cmd = _build_verilator_cmd(repo_root, test_files, test_includes, top_module, language_version, extra_flags, module_graph)
            test_rc, test_output = _run(test_cmd, repo_root, timeout)
            
            # Check if the ORIGINAL module reference error is resolved
            module_not_found = f"Cannot find file containing module: '{mod_name}'" in test_output or \
                              f"Can't resolve module reference to '{mod_name}'" in test_output or \
                              f"Can't resolve module reference: '{mod_name}'" in test_output
            
            if module_not_found:
                # Original error still present - this candidate doesn't provide the module
                print_yellow(f"[INCREMENTAL]     Module '{mod_name}' not found in candidate {idx+1}")
                break
            
            # CRITICAL: Module reference is resolved! Even if there are other errors,
            # this candidate successfully provides the module we're looking for.
            # Check what kind of remaining errors we have:
            missing_pkgs_local = _parse_missing_packages(test_output)
            missing_incs_local = _parse_missing_includes(test_output)
            undefined_vars = test_output.count("Can't find definition of variable:")
            missing_typedefs = test_output.count("Can't find typedef/interface:")
            
            # If no dependency errors remain, this candidate is perfect
            if not missing_pkgs_local and not missing_incs_local and undefined_vars == 0 and missing_typedefs == 0:
                if test_rc == 0:
                    print_green(f"[INCREMENTAL]   ✓ Candidate {idx+1} works perfectly for '{mod_name}' (compiles)")
                    return mod_file, candidate_added_deps
                else:
                    # Module resolved, no dependency errors, but has other errors (e.g., PINNOTFOUND)
                    print_green(f"[INCREMENTAL]   ✓ Candidate {idx+1} resolves '{mod_name}' (module found, other errors present)")
                    if best_candidate is None:
                        best_candidate = mod_file
                        best_candidate_deps = candidate_added_deps
                    break
            
            # Module is resolved but has dependency errors - try to fix them in mini-loop
            if mini_iter == 0:
                deps_msg = f"packages={len(missing_pkgs_local)}, includes={len(missing_incs_local)}, undef_vars={undefined_vars}, typedefs={missing_typedefs}"
                print_yellow(f"[INCREMENTAL]     Mini-loop iter {mini_iter+1}: Candidate {idx+1} resolves module but has deps: {deps_msg}")
            
            # Try to resolve missing packages/includes
            resolved_something = False
            
            for pkg_name in missing_pkgs_local:
                pkg_files = _find_file_declaring_package(repo_root, pkg_name, module_graph)
                if pkg_files:
                    # Just add the first one (or we could do sub-iteration here too)
                    pkg_file = pkg_files[0]
                    if pkg_file not in test_files:
                        test_files.append(pkg_file)
                        candidate_added_deps.append(pkg_file)
                        resolved_something = True
                        print_yellow(f"[INCREMENTAL]     Mini-loop: Added package {pkg_file} for '{pkg_name}'")
            
            for inc_name in missing_incs_local:
                inc_dir = _find_include_file(repo_root, inc_name, test_includes)
                if inc_dir and inc_dir not in test_includes:
                    test_includes.add(inc_dir)
                    resolved_something = True
                    print_yellow(f"[INCREMENTAL]     Mini-loop: Added include {inc_dir} for '{inc_name}'")
            
            if not resolved_something:
                # Can't resolve any more dependencies
                if undefined_vars > 0 or missing_typedefs > 0:
                    print_yellow(f"[INCREMENTAL]     Candidate {idx+1} has version incompatibility (undef_vars={undefined_vars}, missing_typedefs={missing_typedefs})")
                else:
                    print_yellow(f"[INCREMENTAL]     Candidate {idx+1} has unresolvable dependencies")
                
                # IMPORTANT: Even if we couldn't resolve all dependencies, if the ORIGINAL
                # module reference error is gone AND there are no PINNOTFOUND errors,
                # this candidate is still valid!
                # Re-check one more time if the module is resolved
                test_cmd = _build_verilator_cmd(repo_root, test_files, test_includes, top_module, language_version, extra_flags, module_graph)
                test_rc, test_output = _run(test_cmd, repo_root, timeout)
                module_still_missing = f"Can't resolve module reference to '{mod_name}'" in test_output or \
                                      f"Can't resolve module reference: '{mod_name}'" in test_output or \
                                      f"Cannot find file containing module: '{mod_name}'" in test_output
                
                # Check for PINNOTFOUND errors - these indicate wrong module version/interface
                pin_errors = test_output.count("PINNOTFOUND")
                
                if not module_still_missing and pin_errors == 0:
                    # Module IS resolved without pin errors - good candidate!
                    print_green(f"[INCREMENTAL]   ✓ Candidate {idx+1} resolves '{mod_name}' (module found, some dependencies unresolved)")
                    if best_candidate is None:
                        best_candidate = mod_file
                        best_candidate_deps = candidate_added_deps
                elif not module_still_missing and pin_errors > 0:
                    # Module found but has pin errors - wrong version
                    print_yellow(f"[INCREMENTAL]     Candidate {idx+1} resolves '{mod_name}' but has {pin_errors} pin errors (likely wrong version)")
                
                break  # Exit mini-loop, try next candidate if needed
        
        # After mini-loop, check if this candidate succeeded
        if best_candidate == mod_file:
            break  # Found a good candidate, stop trying others
    
    return best_candidate, best_candidate_deps


def compile_incremental(
    repo_root: str,
    top_module: str,
    top_module_file: str,
    module_graph: Dict[str, Dict],
    language_version: str = "1800-2023",
    extra_flags: List[str] = None,
    max_iterations: int = 20,
    timeout: int = 300,
) -> Tuple[int, str, List[str], Set[str]]:
    """
    Incrementally build the file list by starting with the top module
    and adding dependencies as Verilator reports them.
    
    Args:
        repo_root: Repository root directory
        top_module: Name of the top module
        top_module_file: Relative path to the file containing the top module
        module_graph: Module dependency graph from config_generator_core
        language_version: Verilog/SystemVerilog version
        extra_flags: Additional Verilator flags
        max_iterations: Maximum number of iterations to try
        timeout: Timeout for each Verilator run
    
    Returns:
        (return_code, log, final_files, final_include_dirs)
    """
    # Convert repo_root to absolute path for consistent path operations
    repo_root = os.path.abspath(repo_root)
    
    print_green(f"[INCREMENTAL] Starting incremental compilation for top module: {top_module}")
    print_green(f"[INCREMENTAL] Top module file: {top_module_file}")
    print_yellow(f"[INCREMENTAL] Repo root (absolute): {repo_root}")
    
    # Start with just the top module file
    current_files = [top_module_file]
    current_includes: Set[str] = set()
    
    # Add the directory containing the top module as an include directory
    top_dir = os.path.dirname(top_module_file)
    if top_dir:
        current_includes.add(top_dir)
    
    # Scan for .h files in the module graph and add their directories as includes
    # .h files are typically config headers that should be accessible via `include directives
    for file_path, info in module_graph.items():
        if file_path.endswith('.h'):
            h_dir = os.path.dirname(file_path)
            if h_dir:
                current_includes.add(h_dir)
                print_yellow(f"[INCREMENTAL] Auto-adding .h file directory to includes: {h_dir}")
    
    # Track what we've already tried to add to avoid infinite loops
    attempted_modules: Set[str] = set()
    attempted_packages: Set[str] = set()
    attempted_interfaces: Set[str] = set()
    attempted_includes: Set[str] = set()
    
    # Track error counts to detect progress even when no files are added
    prev_error_count = float('inf')
    
    last_log = ""
    
    for iteration in range(max_iterations):
        print_yellow(f"[INCREMENTAL] Iteration {iteration + 1}/{max_iterations} | files={len(current_files)} includes={len(current_includes)}")
        
        # Order files before compilation to ensure packages come before importers
        current_files = _order_sv_files(current_files, repo_root)
        
        # Build and run Verilator command
        cmd = _build_verilator_cmd(
            repo_root,
            current_files,
            current_includes,
            top_module,
            language_version,
            extra_flags,
            module_graph
        )
        
        print_blue(f"[INCREMENTAL] Files: {', '.join(current_files)}")
        
        rc, output = _run(cmd, repo_root, timeout)
        last_log = output
        
        # Check for SystemVerilog keyword conflicts on first iteration
        # If detected and we're using SystemVerilog mode, retry with plain Verilog
        if iteration == 0 and (rc != 0 or "%Error:" in output):
            if _detect_systemverilog_keyword_conflict(output):
                # Check if we're using SystemVerilog mode
                if "--sv" in cmd or "--language 1800" in " ".join(cmd):
                    print_yellow("[INCREMENTAL] SystemVerilog keyword conflict detected, retrying with Verilog mode")
                    # Override language to Verilog 2005
                    language_version = "1364-2005"
                    # Rebuild command with Verilog mode
                    cmd = _build_verilator_cmd(
                        repo_root,
                        current_files,
                        current_includes,
                        top_module,
                        language_version,
                        extra_flags,
                        module_graph
                    )
                    print_blue(f"[INCREMENTAL] Retrying with Verilog mode")
                    rc, output = _run(cmd, repo_root, timeout)
                    last_log = output
        
        # Check if compilation is actually successful (rc==0 AND no errors in output)
        # Note: -Wno-fatal can make Verilator return 0 even with errors
        has_errors = "%Error:" in output or "error:" in output.lower()
        
        if rc == 0 and not has_errors:
            # Print the effective language version for config_generator to parse
            mode_name = "sv" if language_version.startswith("1800") else "verilog"
            print(f"[LANG-EFFECTIVE] {language_version} mode={mode_name}")
            print_green(f"[INCREMENTAL] ✓ Compilation successful after {iteration + 1} iterations!")
            print_green(f"[INCREMENTAL] Final file count: {len(current_files)}")
            print_green(f"[INCREMENTAL] Final include dirs: {len(current_includes)}")
            # Order files topologically before returning (packages before importers)
            ordered_files = _order_sv_files(current_files, repo_root)
            return 0, output, ordered_files, current_includes
        
        # Parse errors to find missing dependencies
        missing_modules = _parse_missing_modules(output)
        missing_packages = _parse_missing_packages(output)
        missing_includes = _parse_missing_includes(output)
        missing_interfaces = _parse_missing_interfaces(output)
        forward_decl_files = _parse_forward_declaration_files(output, repo_root)
        missing_import_packages = _parse_missing_import_packages(output)
        missing_defines = _parse_missing_defines(output)
        included_files_with_errors = _parse_included_files_with_errors(output, repo_root)
        
        # Also detect packages referenced with :: syntax (e.g., pkg_name::constant)
        package_scope_refs = _parse_package_scope_references(output)
        for pkg_ref in package_scope_refs:
            if pkg_ref not in missing_import_packages:
                missing_import_packages.append(pkg_ref)
        
        print_yellow(f"[INCREMENTAL] Missing: modules={len(missing_modules)} packages={len(missing_packages)} includes={len(missing_includes)} interfaces={len(missing_interfaces)} forward_decls={len(forward_decl_files)} import_pkgs={len(missing_import_packages)} defines={len(missing_defines)} included_files={len(included_files_with_errors)}")
        
        # Track if we made any progress this iteration
        added_something = False
        
        # IMPORTANT: Process dependencies in order of specificity:
        # 0. Forward declaration files (files with type definitions that must come first)
        # 1. Import packages (package files that are imported)
        # 2. Packages (define types and constants needed by everything else)
        # 3. Includes (header files)
        # 4. Interfaces (interface definitions)
        # 5. Modules last (can now pick correct version based on packages)
        
        # Add files that contain forward declarations (type definitions used before declaration)
        for fwd_file in forward_decl_files:
            # If it's a .svh include file, find the package that includes it
            if fwd_file.endswith('.svh') or fwd_file.endswith('.vh'):
                pkg_files = _find_package_including_file(repo_root, fwd_file, module_graph)
                for pkg_file in pkg_files:
                    if pkg_file not in current_files:
                        print_green(f"[INCREMENTAL] + Adding package file: {pkg_file} (includes '{os.path.basename(fwd_file)}' with type definitions)")
                        current_files.append(pkg_file)
                        added_something = True
                        pkg_dir = os.path.dirname(pkg_file)
                        if pkg_dir and pkg_dir not in current_includes:
                            current_includes.add(pkg_dir)
                if not pkg_files:
                    print_yellow(f"[INCREMENTAL] ! Could not find package including {fwd_file}")
            # If it's a .sv file, add it directly
            elif fwd_file.endswith('.sv') and fwd_file not in current_files:
                print_green(f"[INCREMENTAL] + Adding forward declaration file: {fwd_file} (contains type definitions)")
                current_files.append(fwd_file)
                added_something = True
                # Add its directory as include
                fwd_dir = os.path.dirname(fwd_file)
                if fwd_dir and fwd_dir not in current_includes:
                    current_includes.add(fwd_dir)
        
        # Add files that have typedef/package errors when included (typically interfaces)
        # These need to be compiled as standalone files before the files that include them
        for inc_file in included_files_with_errors:
            if inc_file not in current_files:
                print_green(f"[INCREMENTAL] + Adding included file as standalone: {inc_file} (has typedef/package errors when included)")
                current_files.append(inc_file)
                added_something = True
                # Add its directory as include
                inc_dir = os.path.dirname(inc_file)
                if inc_dir and inc_dir not in current_includes:
                    current_includes.add(inc_dir)
        
        # Add files for missing import packages (explicit import statements)
        for pkg_name in missing_import_packages:
            if pkg_name in attempted_packages:
                continue
            
            attempted_packages.add(pkg_name)
            pkg_files = _find_file_declaring_package(repo_root, pkg_name, module_graph)
            
            if pkg_files:
                # Convert to list if single file
                if not isinstance(pkg_files, list):
                    pkg_files = [pkg_files]
                
                # If multiple candidates, test them to find the best one
                if len(pkg_files) > 1:
                    best_candidate = _try_package_candidates(
                        pkg_name, pkg_files, current_files, current_includes,
                        repo_root, top_module, language_version, extra_flags, timeout
                    )
                    if best_candidate and best_candidate not in current_files:
                        print_green(f"[INCREMENTAL] + Adding import package file: {best_candidate} (provides '{pkg_name}')")
                        current_files.append(best_candidate)
                        added_something = True
                        pkg_dir = os.path.dirname(best_candidate)
                        if pkg_dir and pkg_dir not in current_includes:
                            current_includes.add(pkg_dir)
                else:
                    # Single candidate, add directly
                    pkg_file = pkg_files[0]
                    if pkg_file not in current_files:
                        print_green(f"[INCREMENTAL] + Adding import package file: {pkg_file} (provides '{pkg_name}')")
                        current_files.append(pkg_file)
                        added_something = True
                        pkg_dir = os.path.dirname(pkg_file)
                        if pkg_dir and pkg_dir not in current_includes:
                            current_includes.add(pkg_dir)
            else:
                print_red(f"[INCREMENTAL] ✗ Cannot find file for import package: {pkg_name}")
        
        # Add header files for missing defines
        for define_name in missing_defines:
            if define_name in attempted_packages:  # Reuse attempted set to avoid duplicates
                continue
            
            attempted_packages.add(define_name)
            header_files = _find_header_with_define(repo_root, define_name, module_graph)
            
            if header_files:
                for header_file in header_files:
                    if header_file not in current_files:
                        print_green(f"[INCREMENTAL] + Adding header file: {header_file} (defines '`{define_name}')")
                        current_files.append(header_file)
                        added_something = True
                        # Add the directory containing the header to includes
                        header_dir = os.path.dirname(header_file)
                        
                        # If the file is in a subdirectory of 'include', 'inc', or 'includes', use the parent include dir
                        # Example: .bender/.../include/common_cells/file.svh -> use .bender/.../include/
                        parts = header_dir.split(os.sep)
                        if 'include' in parts or 'inc' in parts or 'includes' in parts:
                            # Find the last occurrence of include/inc/includes
                            for i in range(len(parts) - 1, -1, -1):
                                if parts[i] in ['include', 'inc', 'includes']:
                                    header_dir = os.sep.join(parts[:i+1])
                                    break
                        
                        if header_dir and header_dir not in current_includes:
                            current_includes.add(header_dir)
                            print_green(f"[INCREMENTAL] + Adding include dir: {header_dir} (for define '`{define_name}')")
            else:
                print_yellow(f"[INCREMENTAL] ! Cannot find header file defining: `{define_name}")
        
        # Add files for missing packages
        # Strategy: First add all unique packages (single file), then test duplicates with better context
        unique_packages = {}  # pkg_name -> file
        duplicate_packages = {}  # pkg_name -> [files]
        
        for pkg_name in missing_packages:
            if pkg_name in attempted_packages:
                continue
            
            attempted_packages.add(pkg_name)
            pkg_files = _find_file_declaring_package(repo_root, pkg_name, module_graph)
            
            # If not found as a package declaration, it might be a typedef inside a package
            if not pkg_files:
                print_yellow(f"[INCREMENTAL] '{pkg_name}' not found as package, searching for typedef...")
                pkg_files = _find_package_with_typedef(repo_root, pkg_name, module_graph)
            
            if not pkg_files:
                print_red(f"[INCREMENTAL] ✗ Cannot find file for package/typedef: {pkg_name}")
                continue
            
            if len(pkg_files) == 1:
                unique_packages[pkg_name] = pkg_files[0]
            else:
                duplicate_packages[pkg_name] = pkg_files
        
        # First pass: Add all unique packages (no ambiguity)
        for pkg_name, pkg_file in unique_packages.items():
            if pkg_file not in current_files:
                print_green(f"[INCREMENTAL] + Adding package file: {pkg_file} (provides '{pkg_name}')")
                current_files.append(pkg_file)
                pkg_dir = os.path.dirname(pkg_file)
                if pkg_dir and pkg_dir not in current_includes:
                    current_includes.add(pkg_dir)
                added_something = True
        
        # Second pass: Test duplicate packages with all unique packages already in place
        for pkg_name, pkg_files in duplicate_packages.items():
            # Try candidates and get the best one
            best_candidate = _try_package_candidates(
                pkg_name, pkg_files, current_files, current_includes,
                repo_root, top_module, language_version, extra_flags, timeout
            )
            
            # Use the best candidate
            if best_candidate and best_candidate not in current_files:
                current_files.append(best_candidate)
                pkg_dir = os.path.dirname(best_candidate)
                if pkg_dir and pkg_dir not in current_includes:
                    current_includes.add(pkg_dir)
                print_green(f"[INCREMENTAL] + Adding package file: {best_candidate} (provides '{pkg_name}')")
                added_something = True
            elif not best_candidate and pkg_files:
                # No candidate worked, just add the first one as fallback
                fallback = pkg_files[0]
                if fallback not in current_files:
                    print_yellow(f"[INCREMENTAL] + Adding package file (fallback): {fallback} (provides '{pkg_name}')")
                    current_files.append(fallback)
                    pkg_dir = os.path.dirname(fallback)
                    if pkg_dir and pkg_dir not in current_includes:
                        current_includes.add(pkg_dir)
                    added_something = True
        
        # Add files for missing interfaces
        for if_name in missing_interfaces:
            if if_name in attempted_interfaces:
                continue
            
            attempted_interfaces.add(if_name)
            if_files = _find_file_declaring_interface(repo_root, if_name, module_graph)
            
            # Handle both single file and list of files
            if isinstance(if_files, str):
                if_files = [if_files] if if_files else []
            
            if if_files:
                # Try all candidate files for this interface
                added_for_this_interface = False
                for if_file in if_files:
                    if if_file not in current_files:
                        if not added_for_this_interface:
                            if len(if_files) > 1:
                                print_green(f"[INCREMENTAL] + Adding {len(if_files)} candidate files for interface '{if_name}': {', '.join(if_files)}")
                            else:
                                print_green(f"[INCREMENTAL] + Adding interface file: {if_file} (provides '{if_name}')")
                            added_for_this_interface = True
                        
                        current_files.append(if_file)
                        added_something = True
                        
                        # Also add its directory as an include dir
                        if_dir = os.path.dirname(if_file)
                        if if_dir and if_dir not in current_includes:
                            current_includes.add(if_dir)
            else:
                print_red(f"[INCREMENTAL] ✗ Cannot find file for interface: {if_name}")
        
        # Add include directories for missing includes
        for inc_name in missing_includes:
            if inc_name in attempted_includes:
                continue
            
            attempted_includes.add(inc_name)
            inc_dir = _find_include_file(repo_root, inc_name, current_includes)
            
            if inc_dir and inc_dir not in current_includes:
                print_green(f"[INCREMENTAL] + Adding include dir: {inc_dir} (provides '{inc_name}')")
                current_includes.add(inc_dir)
                added_something = True
            else:
                if not inc_dir:
                    print_red(f"[INCREMENTAL] ✗ Cannot find include file: {inc_name}")
        
        # Process modules with dependency resolution (LAST - after packages are resolved)
        for mod_name in missing_modules:
            if mod_name in attempted_modules:
                continue
            
            attempted_modules.add(mod_name)
            mod_files = _find_file_declaring_module(repo_root, mod_name, module_graph)
            
            if not mod_files:
                print_red(f"[INCREMENTAL] ✗ Cannot find file for module: {mod_name}")
                continue
            
            # Try candidates and get the best one with its dependencies
            best_candidate, candidate_deps = _try_module_candidates(
                mod_name, mod_files, current_files, current_includes,
                repo_root, top_module, language_version, extra_flags, timeout, module_graph
            )
            
            # Use the best candidate and its dependencies
            if best_candidate and best_candidate not in current_files:
                current_files.append(best_candidate)
                mod_dir = os.path.dirname(best_candidate)
                if mod_dir and mod_dir not in current_includes:
                    current_includes.add(mod_dir)
                print_green(f"[INCREMENTAL] + Adding module file: {best_candidate} (provides '{mod_name}')")
                
                # Add any dependencies we resolved for this candidate
                for dep_file in candidate_deps:
                    if dep_file not in current_files:
                        current_files.append(dep_file)
                        print_green(f"[INCREMENTAL] + Adding dependency: {dep_file}")
                
                added_something = True
            elif not best_candidate and mod_files:
                # None worked, use the first one as fallback
                fallback = mod_files[0]
                if fallback not in current_files:
                    current_files.append(fallback)
                    mod_dir = os.path.dirname(fallback)
                    if mod_dir and mod_dir not in current_includes:
                        current_includes.add(mod_dir)
                    print_yellow(f"[INCREMENTAL] + Adding module file (fallback): {fallback} (provides '{mod_name}')")
                    added_something = True
        
        # Calculate current error count (total missing dependencies)
        current_error_count = (
            len(missing_modules) + len(missing_packages) + len(missing_includes) +
            len(missing_interfaces) + len(forward_decl_files) + len(missing_import_packages) +
            len(missing_defines) + len(included_files_with_errors)
        )
        
        # Check if we're stuck (no files added AND error count didn't decrease)
        made_progress = added_something or (current_error_count < prev_error_count)
        
        if not made_progress:
            print_red(f"[INCREMENTAL] ✗ No progress made in iteration {iteration + 1}")
            print_red(f"[INCREMENTAL] Still have unresolved dependencies:")
            if missing_modules:
                print_red(f"  - Modules: {', '.join(missing_modules)}")
            if missing_packages:
                print_red(f"  - Packages: {', '.join(missing_packages)}")
            if missing_includes:
                print_red(f"  - Includes: {', '.join(missing_includes)}")
            if missing_interfaces:
                print_red(f"  - Interfaces: {', '.join(missing_interfaces)}")
            
            # If rc==0 but has errors, it means we can't auto-resolve (e.g., typos in code)
            if rc == 0 and has_errors:
                print_red(f"[INCREMENTAL] ✗ Compilation has errors but dependencies seem resolved")
                print_red(f"[INCREMENTAL] This may indicate typos or other issues in the source code")
                rc = 1  # Force failure
            break
        
        # Update prev_error_count for next iteration
        prev_error_count = current_error_count
    
    print_red(f"[INCREMENTAL] ✗ Failed to achieve clean compilation after {max_iterations} iterations")
    # Order files topologically before returning (packages before importers)
    ordered_files = _order_sv_files(current_files, repo_root)
    return rc, last_log, ordered_files, current_includes
