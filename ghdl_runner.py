"""
Incremental GHDL runner - bottom-up dependency resolution for VHDL.

Similar to verilator_runner_incremental.py, this approach starts with just the 
top entity and incrementally adds only the files that are actually needed based 
on GHDL's error messages.

Strategy:
1. Start with only the top entity file
2. Run GHDL and parse errors for missing entities/packages
3. Add only the files that provide those missing dependencies
4. Repeat until no more dependencies are needed or we hit a failure

Key differences from Verilator:
- VHDL is strictly order-dependent: packages must come before entities that use them
- Use --std=08 (VHDL-2008) always
- GHDL uses work library concept
- Entity/package resolution is stricter
"""
from __future__ import annotations
from typing import List, Tuple, Set, Dict, Optional
import os
import re
import subprocess
import tempfile
import shutil
import time

from core.log import print_green, print_yellow, print_red, print_blue


def _run(cmd: List[str], cwd: str, timeout: int) -> Tuple[int, str]:
    """Run a command and stream output to terminal in real-time."""
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
                    print(remaining, end='')
                break
            
            line = proc.stdout.readline()
            if line:
                output_lines.append(line)
                print(line, end='')
            
            if time.time() - start > timeout:
                proc.kill()
                output_lines.append(f"\n[TIMEOUT] GHDL command killed after {timeout}s\n")
                print(f"\n[TIMEOUT] GHDL command killed after {timeout}s\n")
                break
        
        return proc.returncode or 0, "".join(output_lines)
    except Exception as e:
        error_msg = f"[EXCEPTION] {e}"
        print(error_msg)
        return 1, error_msg


def _normalize_path(path: str, repo_root: str) -> str:
    """Normalize a path to be relative to repo_root."""
    if os.path.isabs(path):
        try:
            return os.path.relpath(path, repo_root)
        except ValueError:
            return path
    return path


def _parse_missing_entities(log_text: str) -> List[str]:
    """Parse GHDL output for missing entity errors.
    
    We need to distinguish entities from packages. GHDL uses "unit X not found"
    for both. Key distinction:
    - If the SAME line has "entity <lib>.X" -> it's an entity
    - If same/previous line has "use <lib>.X" -> it's a package
    
    Example entity error:
    rtl/core/neorv32_cpu.vhd:192:45:error: unit "neorv32_cpu_frontend" not found in library "neorv32"
      neorv32_cpu_frontend_inst: entity neorv32.neorv32_cpu_frontend
                                                ^
    """
    missing = set()
    
    # Split into lines to check context
    lines = log_text.split('\n')
    for i, line in enumerate(lines):
        # Look for "unit "X" not found in library" errors (any library)
        match = re.search(r'unit "([^"]+)" not found in library "[^"]+"', line)
        if match:
            unit_name = match.group(1)
            
            # Check context: look at next few lines (error context shown after error line)
            is_entity = False
            is_package = False
            
            # Check the next 1-3 lines for the source code line that caused the error
            for offset in range(1, min(4, len(lines) - i)):
                next_line = lines[i + offset].lower() if i + offset < len(lines) else ""
                
                # If we see "entity <lib>.<name>" it's an entity instantiation
                if 'entity ' in next_line and unit_name.lower() in next_line:
                    is_entity = True
                    break
                
                # If we see "use <lib>.<name>" it's a package import
                if 'use ' in next_line and unit_name.lower() in next_line:
                    is_package = True
                    break
                
                # Stop if we hit the next error (but not caret - that's expected)
                if 'error:' in next_line:
                    break
            
            # Also check previous line for "use" statements
            if not is_entity and i > 0:
                prev_line = lines[i - 1].lower()
                if 'use ' in prev_line and unit_name.lower() in prev_line:
                    is_package = True
            
            # If it's identified as entity (not package), add it
            if is_entity and not is_package:
                if unit_name.lower() not in ['std', 'ieee', 'work', 'std_logic', 'std_logic_vector']:
                    missing.add(unit_name)
    
    # Also check for explicit entity errors
    entity_patterns = [
        r'entity "([^"]+)" not found',
        r"entity '([^']+)' not found",
        r'cannot find entity "([^"]+)"',
        r"cannot find entity '([^']+)'",
        r'no declaration for "([^"]+)"',  # GHDL "no declaration" errors
    ]
    for pat in entity_patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            entity_name = m.group(1)
            if entity_name.lower() not in ['std', 'ieee', 'work']:
                missing.add(entity_name)
    
    # Also check for elaboration errors: "instance X of component Y is not bound"
    # This catches direct instantiations of missing entities
    elab_pattern = r'instance\s+"[^"]+"\s+of\s+component\s+"([^"]+)"\s+is\s+not\s+bound'
    for m in re.finditer(elab_pattern, log_text, flags=re.IGNORECASE):
        entity_name = m.group(1)
        if entity_name.lower() not in ['std', 'ieee', 'work']:
            missing.add(entity_name)
    
    return list(missing)


def _parse_missing_packages(log_text: str) -> List[str]:
    """Parse GHDL output for missing package errors.
    
    GHDL reports missing packages as:
    - unit "package_name" not found in library "work"
    - unit "package_name" not found in library "custom_lib"
    
    We need to distinguish these from entity errors by checking context.
    """
    missing = set()
    patterns = [
        # Pattern for any library (work, custom, etc): unit "X" not found in library "Y"
        r'unit "([^"]+)" not found in library "[^"]+"',
        # Backup patterns
        r'package "([^"]+)" not found',
        r"package '([^']+)' not found",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            pkg_name = m.group(1)
            # Filter out IEEE/STD libraries
            if pkg_name.lower() not in ['std', 'ieee', 'work', 'std_logic_1164', 'numeric_std']:
                missing.add(pkg_name)
    return list(missing)


def _normalize_file_path(file_path: str, repo_name: str) -> str:
    """Normalize file path by removing temp/reponame/ prefix if present."""
    if file_path.startswith(f"temp/{repo_name}/"):
        return file_path.replace(f"temp/{repo_name}/", "")
    return file_path


def _detect_custom_library(repo_root: str, files: List[str]) -> Optional[str]:
    """Detect if files use a custom library name instead of 'work'.
    
    Scans the first few files to check for 'library <name>;' declarations
    where <name> is not ieee/std/work.
    
    Returns: custom library name or None if using default 'work'
    """
    custom_libs = set()
    
    for file_path in files[:min(5, len(files))]:  # Check first 5 files
        full_path = os.path.join(repo_root, file_path) if not os.path.isabs(file_path) else file_path
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read(5000)  # Read first 5KB
                # Look for: library <name>;
                for match in re.finditer(r'^\s*library\s+(\w+)\s*;', content, flags=re.IGNORECASE | re.MULTILINE):
                    lib_name = match.group(1).lower()
                    # Ignore standard libraries
                    if lib_name not in ['ieee', 'std', 'work']:
                        custom_libs.add(lib_name)
        except Exception:
            continue
    
    # If we found a consistent custom library name, return it
    if len(custom_libs) == 1:
        custom_lib = custom_libs.pop()
        print_blue(f"[GHDL-INCREMENTAL] Detected custom library name: {custom_lib}")
        return custom_lib
    
    return None


def _search_repo_for_declaration(repo_root: str, symbol_name: str, symbol_type: str, repo_name: str = None) -> List[str]:
    """
    Search the entire repository for files declaring a specific symbol (entity or package).
    
    Args:
        repo_root: Repository root directory
        symbol_name: Name of the symbol to find
        symbol_type: "entity" or "package"
        repo_name: Repository name for path normalization
    
    Returns:
        List of relative file paths that declare the symbol
    """
    candidates = []
    symbol_lower = symbol_name.lower()
    
    # Pattern to match: "entity <name> is" or "package <name> is"
    pattern = re.compile(rf'^\s*{symbol_type}\s+{re.escape(symbol_name)}\s+is\b', 
                        flags=re.IGNORECASE | re.MULTILINE)
    
    # Walk through all VHDL files in repo
    for root, dirs, files in os.walk(repo_root):
        for file in files:
            if not file.lower().endswith(('.vhd', '.vhdl')):
                continue
            
            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()  # Read entire file to ensure we find all symbol declarations
                    if pattern.search(content):
                        # Convert to relative path
                        rel_path = os.path.relpath(full_path, repo_root)
                        # Normalize path
                        rel_path = _normalize_file_path(rel_path, repo_name) if repo_name else rel_path
                        candidates.append(rel_path)
                        print_yellow(f"[GHDL-INCREMENTAL] Found {symbol_type} '{symbol_name}' in: {rel_path}")
            except Exception:
                continue
    
    return candidates


def _find_file_declaring_entity(repo_root: str, entity_name: str, modules: List[Tuple[str, str]], repo_name: str = None) -> List[str]:
    """Find files that declare a specific entity.
    
    Args:
        repo_root: Repository root directory
        entity_name: Name of the entity to find
        modules: List of (module_name, file_path) tuples
        repo_name: Repository name for path normalization
    
    Returns:
        List of file paths that might contain the entity
    """
    candidates = []
    entity_lower = entity_name.lower()
    
    # First check modules list for exact matches (fast path)
    for mod_name, file_path in modules:
        if mod_name.lower() == entity_lower:
            normalized_path = _normalize_file_path(file_path, repo_name) if repo_name else file_path
            candidates.append(normalized_path)
    
    # If not found in modules, search entire repository
    if not candidates:
        candidates = _search_repo_for_declaration(repo_root, entity_name, "entity", repo_name)
    
    return candidates


def _find_file_declaring_package(repo_root: str, package_name: str, modules: List[Tuple[str, str]], repo_name: str = None) -> List[str]:
    """Find files that declare a specific package.
    
    Args:
        repo_root: Repository root directory
        package_name: Name of the package to find
        modules: List of (module_name, file_path) tuples
        repo_name: Repository name for path normalization
    
    Returns:
        List of file paths that might contain the package
    """
    # Packages are usually not in the modules list (which typically only has entities)
    # So go straight to repository-wide search
    candidates = _search_repo_for_declaration(repo_root, package_name, "package", repo_name)
    
    return candidates


def _parse_missing_entities_with_context(log_text: str) -> List[Tuple[str, str]]:
    """Parse GHDL output for missing entity errors with the file context.
    Returns list of (file_with_error, missing_entity_name) tuples.
    
    Example error:
    Project/Components/microcontroller.vhd:59:24:error: no declaration for "controller"
    """
    missing = []
    # Pattern: filename:line:col:error: no declaration for "entity_name"
    pattern = r'([^\s:]+\.vhdl?):\d+:\d+:.*?no\s+declaration\s+for\s+["\']([^"\']+)["\']'
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        filename = m.group(1)
        entity = m.group(2)
        # Filter out IEEE/STD libraries
        if entity.lower() not in ['std', 'ieee', 'work', 'std_logic', 'std_logic_vector']:
            missing.append((filename, entity))
    return missing


def _parse_missing_packages_with_context(log_text: str) -> List[Tuple[str, str]]:
    """Parse GHDL output for missing package errors with the file context.
    Returns list of (file_with_error, missing_package_name) tuples.
    
    Example error:
    src/pp_potato.vhd:8:10:error: unit "pp_types" not found in library "work"
    """
    missing = []
    # Pattern: filename:line:col:error: unit "package_name" not found
    pattern = r'([^\s:]+\.vhdl?):\d+:\d+:.*?unit\s+["\']([^"\']+)["\']\s+not\s+found'
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        filename = m.group(1)
        package = m.group(2)
        # Filter out IEEE/STD libraries
        if package.lower() not in ['std', 'ieee', 'work', 'std_logic', 'std_logic_vector']:
            missing.append((filename, package))
    return missing


def _reorder_by_dependencies(files: List[str], log_text: str, repo_root: str) -> List[str]:
    """
    Reorder files based on GHDL error messages showing dependencies.
    If file A needs package/entity from file B, ensure B comes before A.
    
    Returns reordered file list.
    """
    missing_pkg_deps = _parse_missing_packages_with_context(log_text)
    missing_ent_deps = _parse_missing_entities_with_context(log_text)
    
    if not missing_pkg_deps and not missing_ent_deps:
        return files
    
    print_yellow(f"[GHDL-INCREMENTAL] Found dependencies - packages: {len(missing_pkg_deps)}, entities: {len(missing_ent_deps)}")
    
    # Build a map: package/entity name -> file that declares it
    symbol_to_file: Dict[str, str] = {}
    for f in files:
        full_path = os.path.join(repo_root, f) if not os.path.isabs(f) else f
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()  # Read entire file to catch all entity declarations
                # Look for ALL "package <name> is" declarations
                for pkg_match in re.finditer(r'^\s*package\s+(\w+)\s+is\b', content, flags=re.IGNORECASE | re.MULTILINE):
                    pkg_name = pkg_match.group(1).lower()
                    symbol_to_file[pkg_name] = f
                # Also look for ALL "entity <name> is" declarations
                for ent_match in re.finditer(r'^\s*entity\s+(\w+)\s+is\b', content, flags=re.IGNORECASE | re.MULTILINE):
                    ent_name = ent_match.group(1).lower()
                    symbol_to_file[ent_name] = f
        except Exception:
            continue
    
    print_blue(f"[GHDL-INCREMENTAL] Symbol map: {symbol_to_file}")
    
    # Build constraints: provider_file must come before dependent_file
    must_come_before: Dict[str, Set[str]] = {}  # provider_file -> set of files that need it
    
    # Handle package dependencies
    for error_file, missing_symbol in missing_pkg_deps:
        # Normalize error_file path to match our file list
        error_file_normalized = None
        error_basename = os.path.basename(error_file)
        for f in files:
            if os.path.basename(f) == error_basename:
                error_file_normalized = f
                break
        
        if not error_file_normalized:
            continue
        
        # Find which file provides this symbol
        provider_file = symbol_to_file.get(missing_symbol.lower())
        if provider_file and provider_file != error_file_normalized:
            if provider_file not in must_come_before:
                must_come_before[provider_file] = set()
            must_come_before[provider_file].add(error_file_normalized)
            print_green(f"[GHDL-INCREMENTAL] Package dependency: {provider_file} must come before {error_file_normalized} (provides {missing_symbol})")
    
    # Handle entity dependencies  
    for error_file, missing_symbol in missing_ent_deps:
        # Normalize error_file path to match our file list
        error_file_normalized = None
        error_basename = os.path.basename(error_file)
        for f in files:
            if os.path.basename(f) == error_basename:
                error_file_normalized = f
                break
        
        if not error_file_normalized:
            continue
        
        # Find which file provides this symbol
        provider_file = symbol_to_file.get(missing_symbol.lower())
        if provider_file and provider_file != error_file_normalized:
            if provider_file not in must_come_before:
                must_come_before[provider_file] = set()
            must_come_before[provider_file].add(error_file_normalized)
            print_green(f"[GHDL-INCREMENTAL] Entity dependency: {provider_file} must come before {error_file_normalized} (provides {missing_symbol})")
    
    if not must_come_before:
        print_yellow("[GHDL-INCREMENTAL] No actionable dependencies found for reordering")
        return files
    
    # Reorder: move provider files before their dependents
    result = list(files)
    
    for provider, dependents in must_come_before.items():
        if provider not in result:
            continue
        
        provider_idx = result.index(provider)
        
        # Find the earliest position needed (before all dependents)
        earliest_needed = provider_idx
        for dep in dependents:
            if dep in result:
                dep_idx = result.index(dep)
                if dep_idx < earliest_needed:
                    earliest_needed = dep_idx
        
        # Move provider to earliest needed position if it's currently after dependents
        if earliest_needed < provider_idx:
            result.remove(provider)
            result.insert(earliest_needed, provider)
            print_yellow(f"[GHDL-INCREMENTAL] Reordered: moved {provider} before {len(dependents)} dependent(s)")
    
    return result


def _order_vhdl_files(files: List[str], repo_root: str) -> List[str]:
    """
    Order VHDL files with packages first, then entities.
    VHDL requires packages to be analyzed before entities that use them.
    """
    packages = []
    entities = []
    
    for f in files:
        full_path = os.path.join(repo_root, f) if not os.path.isabs(f) else f
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read(10000)  # Read first 10KB
                # Check if it's a package file (must come before entities)
                if re.search(r'^\s*package\s+\w+\s+is\b', content, flags=re.IGNORECASE | re.MULTILINE):
                    packages.append(f)
                else:
                    entities.append(f)
        except Exception:
            entities.append(f)
    
    # Packages first, then entities - critical for VHDL!
    return packages + entities


def _ghdl_clean_work(repo_root: str, workdir: str, library_name: str = "work") -> None:
    """Clean GHDL work library files to ensure fresh analysis.
    
    GHDL uses <library>-obj08.cf in the workdir to store analyzed units.
    Between iterations, we need to clean this to avoid stale analysis results.
    For custom libraries (like neorv32), we clean the custom library file.
    """
    # Clean the specific library file
    library_file = os.path.join(workdir, f"{library_name}-obj08.cf")
    if os.path.exists(library_file):
        try:
            os.remove(library_file)
            print_blue(f"[GHDL-INCREMENTAL] Cleaned library: {library_file}")
        except Exception as e:
            print_yellow(f"[GHDL-INCREMENTAL] Warning: Could not clean library file: {e}")
    
    # Also clean work-obj08.cf if it exists (for backwards compatibility)
    if library_name != "work":
        work_file = os.path.join(workdir, "work-obj08.cf")
        if os.path.exists(work_file):
            try:
                os.remove(work_file)
            except Exception:
                pass


def _detect_vendor_libraries(files: List[str], repo_root: str) -> List[str]:
    """
    Detect files that use vendor-specific libraries that are incompatible with GHDL.
    Returns list of problematic files that should be excluded.
    """
    vendor_patterns = [
        r'library\s+altera_mf\b',       # Altera/Intel libraries
        r'library\s+altera\b',
        r'library\s+xilinx\b',          # Xilinx libraries
        r'library\s+unisim\b',          # Xilinx simulation library
        r'library\s+unimacro\b',        # Xilinx macro library
        r'use\s+altera_mf\.',           # Direct use statements
        r'use\s+xilinx\.',
        r'use\s+unisim\.',
        r'use\s+unimacro\.',
    ]
    
    problematic_files = []
    
    for file in files:
        full_path = os.path.join(repo_root, file) if not os.path.isabs(file) else file
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
                for pattern in vendor_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        print_yellow(f"[GHDL-INCREMENTAL] Detected vendor-specific library in {file}, excluding from compilation")
                        problematic_files.append(file)
                        break  # No need to check other patterns for this file
        except Exception:
            continue
    
    return problematic_files


def _detect_synopsys_packages(files: List[str], repo_root: str) -> bool:
    """
    Detect if any of the VHDL files use Synopsys non-standard packages.
    Returns True if -fsynopsys flag should be added.
    """
    synopsys_patterns = [
        r'use\s+ieee\.std_logic_unsigned\.',
        r'use\s+ieee\.std_logic_signed\.',
        r'use\s+ieee\.std_logic_arith\.',
        r'library\s+synopsys\b',
    ]
    
    for file in files:
        full_path = os.path.join(repo_root, file) if not os.path.isabs(file) else file
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
                for pattern in synopsys_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        print_yellow(f"[GHDL-INCREMENTAL] Detected Synopsys package usage in {file}")
                        return True
        except Exception:
            continue
    
    return False


def _validation_flags(ghdl_extra_flags: List[str] = None, files: List[str] = None, repo_root: str = None) -> List[str]:
    """
    Return flags for proper validation:
    - keep relaxed parsing (-frelaxed) for VHDL features
    - treat binding warnings as errors (--warn-error=binding) to catch missing entities
    - add -fsynopsys if Synopsys packages are detected
    - disable hide warnings (-Wno-hide) to avoid signal/port naming conflicts
    """
    base = list(ghdl_extra_flags or [])
    
    # Keep -frelaxed for shared variables and other VHDL relaxations
    # But add --warn-error=binding to catch missing entities/components
    has_warn_binding = any((f.startswith("--warn-error=") and "binding" in f) for f in base)
    if not has_warn_binding:
        base.append("--warn-error=binding")
    
    # Disable hide warnings to avoid signal/port naming conflicts (common in VHDL designs)
    has_no_hide = any(f == "-Wno-hide" for f in base)
    if not has_no_hide:
        base.append("-Wno-hide")
    
    # Auto-detect and add -fsynopsys if needed
    has_synopsys = any(f == "-fsynopsys" for f in base)
    if not has_synopsys and files and repo_root:
        if _detect_synopsys_packages(files, repo_root):
            base.append("-fsynopsys")
            print_green("[GHDL-INCREMENTAL] Added -fsynopsys flag for Synopsys package support")
    
    return base


def _build_ghdl_cmd(
    files: List[str],
    top_entity: str,
    workdir: str,
    ghdl_extra_flags: List[str] = None,
    work_library: str = None,
    repo_root: str = None
) -> List[str]:
    """Build the GHDL analyze command with validation flags.
    
    Args:
        files: List of VHDL files to analyze
        top_entity: Top entity name (unused in analyze, but kept for consistency)
        workdir: Working directory for GHDL
        ghdl_extra_flags: Additional GHDL flags
        work_library: Custom library name (default: "work")
        repo_root: Repository root for Synopsys package detection
    """
    cmd = ["ghdl", "-a", "--std=08", f"--workdir={workdir}"]
    
    # Add custom library name if specified
    if work_library and work_library != "work":
        cmd.append(f"--work={work_library}")
    
    # Use validation flags to ensure --warn-error=binding is included
    flags = _validation_flags(ghdl_extra_flags, files, repo_root)
    if flags:
        cmd.extend(flags)
    
    cmd.extend(files)
    
    return cmd


def _build_elab_cmd(
    top_entity: str,
    workdir: str,
    ghdl_extra_flags: List[str] = None,
    work_library: str = None,
    files: List[str] = None,
    repo_root: str = None
) -> List[str]:
    """Build the GHDL elaboration command.
    
    Args:
        top_entity: Top entity name to elaborate
        workdir: Working directory for GHDL
        ghdl_extra_flags: Additional GHDL flags
        work_library: Custom library name (default: "work")
        files: List of files for Synopsys detection
        repo_root: Repository root for Synopsys package detection
    """
    cmd = ["ghdl", "-e", "--std=08", f"--workdir={workdir}"]
    
    # Add custom library name if specified
    if work_library and work_library != "work":
        cmd.append(f"--work={work_library}")
    
    # Use validation flags
    flags = _validation_flags(ghdl_extra_flags, files, repo_root)
    if flags:
        cmd.extend(flags)
    
    cmd.append(top_entity)
    
    return cmd


def compile_incremental(
    repo_root: str,
    repo_name: str,
    top_entity: str,
    top_entity_file: str,
    modules: List[Tuple[str, str]],
    ghdl_extra_flags: List[str] = None,
    max_iterations: int = 20,
    timeout: int = 300,
) -> Tuple[int, str, List[str]]:
    """
    Incrementally compile VHDL starting from the top entity.
    
    Args:
        repo_root: Repository root directory
        repo_name: Repository name for path normalization
        top_entity: Name of the top entity
        top_entity_file: Path to the file containing the top entity
        modules: List of (module_name, file_path) tuples
        ghdl_extra_flags: Additional GHDL flags
        max_iterations: Maximum number of iterations
        timeout: Timeout for each GHDL command
    
    Returns: (return_code, log, final_files)
    """
    print_green(f"[GHDL-INCREMENTAL] Starting incremental compilation for top entity: {top_entity}")
    print_blue(f"[GHDL-INCREMENTAL] Top entity file: {top_entity_file}")
    print_blue(f"[GHDL-INCREMENTAL] Repo root (absolute): {repo_root}")
    
    # Create temporary work directory for GHDL
    workdir = tempfile.mkdtemp(prefix="ghdl_work_", dir=repo_root)
    
    try:
        current_files = [top_entity_file]
        added_files_history = set([top_entity_file])
        
        # Detect and filter out vendor-specific files
        vendor_files = _detect_vendor_libraries([top_entity_file], repo_root)
        if vendor_files:
            print_red(f"[GHDL-INCREMENTAL] ✗ Top entity file uses vendor-specific libraries, cannot compile with GHDL")
            return 1, "Top entity file contains vendor-specific libraries incompatible with GHDL", current_files
        
        # Detect if files use a custom library name (like "neorv32" instead of "work")
        work_library = _detect_custom_library(repo_root, [top_entity_file])
        
        # Track if files have been reordered by dependency analysis
        # If True, don't re-order them with the simple package-first sort
        files_are_dependency_ordered = False
        
        for iteration in range(1, max_iterations + 1):
            print_blue(f"[GHDL-INCREMENTAL] Iteration {iteration}/{max_iterations} | files={len(current_files)}")
            
            # Clean work library from previous iteration to avoid stale analysis
            _ghdl_clean_work(repo_root, workdir, work_library)
            
            # Order files (packages first, then fine-tune based on dependencies)
            # But if files are already dependency-ordered, preserve that order
            if files_are_dependency_ordered:
                ordered_files = current_files  # Keep existing dependency order
            else:
                ordered_files = _order_vhdl_files(current_files, repo_root)
            
            # Build and run GHDL command
            cmd = _build_ghdl_cmd(ordered_files, top_entity, workdir, ghdl_extra_flags, work_library, repo_root)
            
            print_blue(f"[GHDL-INCREMENTAL] Files: {', '.join(ordered_files)}")
            
            rc, output = _run(cmd, repo_root, timeout)
            
            if rc == 0:
                # Analysis successful, now try elaboration to catch missing entity instantiations
                print_blue(f"[GHDL-INCREMENTAL] Analysis succeeded, running elaboration...")
                elab_cmd = _build_elab_cmd(top_entity, workdir, ghdl_extra_flags, work_library, ordered_files, repo_root)
                rc_elab, output_elab = _run(elab_cmd, repo_root, timeout)
                
                if rc_elab == 0:
                    print_green(f"[GHDL-INCREMENTAL] ✓ Elaboration successful after {iteration} iterations!")
                    return rc_elab, output + "\n" + output_elab, current_files
                
                # Elaboration failed - parse errors from elaboration output
                print_yellow(f"[GHDL-INCREMENTAL] Elaboration failed, need to add more dependencies...")
                output = output + "\n" + output_elab  # Combine both outputs for error parsing
            
            # Try dynamic reordering based on error messages
            reordered_files = _reorder_by_dependencies(ordered_files, output, repo_root)
            if reordered_files != ordered_files:
                # Files were reordered, try compiling again with new order
                print_yellow(f"[GHDL-INCREMENTAL] Trying with reordered files...")
                # Clean work library before retry to ensure fresh analysis
                _ghdl_clean_work(repo_root, workdir, work_library)
                cmd = _build_ghdl_cmd(reordered_files, top_entity, workdir, ghdl_extra_flags, work_library)
                rc, output = _run(cmd, repo_root, timeout)
                
                # Mark files as dependency-ordered so we preserve this order in next iteration
                files_are_dependency_ordered = True
                
                if rc == 0:
                    # Analysis successful after reordering, try elaboration
                    print_blue(f"[GHDL-INCREMENTAL] Analysis succeeded after reordering, running elaboration...")
                    elab_cmd = _build_elab_cmd(top_entity, workdir, ghdl_extra_flags, work_library)
                    rc_elab, output_elab = _run(elab_cmd, repo_root, timeout)
                    
                    if rc_elab == 0:
                        print_green(f"[GHDL-INCREMENTAL] ✓ Elaboration successful after reordering!")
                        return rc_elab, output + "\n" + output_elab, current_files
                    
                    # Elaboration failed - parse errors
                    print_yellow(f"[GHDL-INCREMENTAL] Elaboration failed after reordering...")
                    output = output + "\n" + output_elab
                
                # Update current_files to maintain the new order
                current_files = reordered_files
            
            # Parse errors
            missing_entities = _parse_missing_entities(output)
            missing_packages = _parse_missing_packages(output)
            
            # Filter out packages that are actually entities (avoid duplicates)
            # If a symbol appears as both, it's an entity
            entity_names_lower = set(e.lower() for e in missing_entities)
            missing_packages = [p for p in missing_packages if p.lower() not in entity_names_lower]
            
            print_blue(f"[GHDL-INCREMENTAL] Missing: entities={len(missing_entities)} packages={len(missing_packages)}")
            
            added_something = False
            
            # Add missing packages first (they must come before entities)
            for pkg_name in missing_packages:
                pkg_files = _find_file_declaring_package(repo_root, pkg_name, modules, repo_name)
                
                if pkg_files:
                    for pkg_file in pkg_files:
                        if pkg_file not in added_files_history:
                            # Check for vendor-specific libraries before adding
                            vendor_files = _detect_vendor_libraries([pkg_file], repo_root)
                            if vendor_files:
                                print_yellow(f"[GHDL-INCREMENTAL] Skipping {pkg_file} due to vendor-specific libraries")
                                continue
                            
                            # Just append - let the reordering functions handle proper positioning
                            current_files.append(pkg_file)
                            added_files_history.add(pkg_file)
                            print_green(f"[GHDL-INCREMENTAL] + Adding package file: {pkg_file} (provides '{pkg_name}')")
                            added_something = True
                            break  # Use first candidate
            
            # Add missing entities 
            for entity_name in missing_entities:
                entity_files = _find_file_declaring_entity(repo_root, entity_name, modules, repo_name)
                
                if entity_files:
                    for entity_file in entity_files:
                        if entity_file not in added_files_history:
                            # Check for vendor-specific libraries before adding
                            vendor_files = _detect_vendor_libraries([entity_file], repo_root)
                            if vendor_files:
                                print_yellow(f"[GHDL-INCREMENTAL] Skipping {entity_file} due to vendor-specific libraries")
                                continue
                            
                            # Just append - let the reordering functions handle proper positioning
                            current_files.append(entity_file)
                            added_files_history.add(entity_file)
                            print_green(f"[GHDL-INCREMENTAL] + Adding entity file: {entity_file} (provides '{entity_name}')")
                            added_something = True
                            break  # Use first candidate
            
            # If we added new files, reset dependency ordering flag
            # so the new files get properly ordered in the next iteration
            if added_something:
                files_are_dependency_ordered = False
                print_yellow(f"[GHDL-INCREMENTAL] Added new files, will reorder in next iteration")
                print_blue(f"[GHDL-INCREMENTAL] Current file order: {', '.join(current_files)}")
                
                # Immediately try reordering to fix dependency issues
                reordered_files = _reorder_by_dependencies(current_files, output, repo_root)
                if reordered_files != current_files:
                    print_yellow(f"[GHDL-INCREMENTAL] Reordering files after adding dependencies...")
                    print_blue(f"[GHDL-INCREMENTAL] New file order: {', '.join(reordered_files)}")
                    current_files = reordered_files
                    files_are_dependency_ordered = True
                else:
                    print_yellow(f"[GHDL-INCREMENTAL] No reordering needed or possible")
                    # Try basic VHDL ordering (packages first, then entities)
                    basic_ordered = _order_vhdl_files(current_files, repo_root)
                    if basic_ordered != current_files:
                        print_yellow(f"[GHDL-INCREMENTAL] Applying basic VHDL ordering...")
                        print_blue(f"[GHDL-INCREMENTAL] Basic ordered: {', '.join(basic_ordered)}")
                        current_files = basic_ordered
            
            # Check if we're stuck
            if not added_something:
                print_red(f"[GHDL-INCREMENTAL] ✗ No progress made in iteration {iteration}")
                print_red("[GHDL-INCREMENTAL] Still have unresolved dependencies:")
                for e in missing_entities:
                    print_red(f"  - Entity: {e}")
                for p in missing_packages:
                    print_red(f"  - Package: {p}")
                
                print_blue(f"[GHDL-INCREMENTAL] Current files in order:")
                for i, f in enumerate(current_files):
                    print_blue(f"  {i+1}. {f}")
                
                # Fallback: if we've made significant progress but are stuck, try including all VHDL files
                if iteration > 2 and len(current_files) > 5:
                    print_yellow("[GHDL-INCREMENTAL] Attempting fallback: including ALL VHDL files...")
                    all_vhdl_files = []
                    for mod_name, file_path in modules:
                        normalized_path = _normalize_file_path(file_path, repo_name) if repo_name else file_path
                        if normalized_path.lower().endswith(('.vhd', '.vhdl')) and normalized_path not in added_files_history:
                            # Check for vendor-specific libraries before adding
                            vendor_files = _detect_vendor_libraries([normalized_path], repo_root)
                            if vendor_files:
                                print_yellow(f"[GHDL-INCREMENTAL] Skipping {normalized_path} in fallback due to vendor-specific libraries")
                                continue
                            all_vhdl_files.append(normalized_path)
                    
                    if all_vhdl_files:
                        # Just append all files - let the reordering functions handle proper positioning
                        current_files.extend(all_vhdl_files)
                        for vhdl_file in all_vhdl_files:
                            added_files_history.add(vhdl_file)
                        
                        print_green(f"[GHDL-INCREMENTAL] Added {len(all_vhdl_files)} additional VHDL files for fallback")
                        
                        # Force a complete reordering with all files
                        ordered_all = _order_vhdl_files(current_files, repo_root)
                        if ordered_all != current_files:
                            print_yellow("[GHDL-INCREMENTAL] Reordering all files...")
                            current_files = ordered_all
                        
                        added_something = True
                        files_are_dependency_ordered = False  # Trigger reordering
                
                if not added_something:
                    break
        
        print_red(f"[GHDL-INCREMENTAL] ✗ Failed to achieve clean compilation after {max_iterations} iterations")
        return 1, output, current_files  # Explicitly return failure code
        
    finally:
        # Clean up work directory
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass


def incremental_compilation(
    repo_root: str,
    repo_name: str,
    top_candidates: List[str],
    modules: List[Tuple[str, str]],
    ghdl_extra_flags: List[str] = None,
    timeout: int = 300,
) -> Tuple[bool, str, List[str], str]:
    """
    Try incremental compilation with multiple top entity candidates.
    
    Args:
        repo_root: Repository root directory
        repo_name: Repository name
        top_candidates: List of top entity candidates to try
        modules: List of (module_name, file_path) tuples
        ghdl_extra_flags: Additional GHDL flags
        timeout: Timeout for each operation
    
    Returns: (success, log, final_files, selected_top)
    """
    print_green(f"[GHDL-INCREMENTAL] Trying incremental bottom-up approach for {repo_name}")
    print_blue(f"[GHDL-INCREMENTAL] Candidates to try: {', '.join(top_candidates[:10])}")
    
    # Limit candidates for performance
    MAX_CANDIDATES = 10
    if len(top_candidates) > MAX_CANDIDATES:
        print_yellow(f"[GHDL-INCREMENTAL] Limiting to top {MAX_CANDIDATES} candidates (out of {len(top_candidates)})")
        top_candidates = top_candidates[:MAX_CANDIDATES]
    
    for idx, candidate in enumerate(top_candidates, 1):
        print_blue(f"[GHDL-INCREMENTAL] === Candidate {idx}/{len(top_candidates)}: {candidate} ===")
        print_green(f"[GHDL-INCREMENTAL] Testing top entity: {candidate}")
        
        # Find the file that contains this entity
        entity_files = _find_file_declaring_entity(repo_root, candidate, modules, repo_name)
        
        if not entity_files:
            print_yellow(f"[GHDL-INCREMENTAL] Could not find file for entity '{candidate}'")
            continue
        
        top_entity_file = entity_files[0]
        print_blue(f"[GHDL-INCREMENTAL] Top entity file (final): {top_entity_file}")
        print_blue(f"[GHDL-INCREMENTAL] Repo root: {repo_root}")
        print_blue(f"[GHDL-INCREMENTAL] Repo basename: {repo_name}")
        
        # If the path starts with the repo name (e.g., "temp/potato/..."), strip the repo root prefix
        # since we'll be joining it with repo_root later
        if top_entity_file.startswith(f"temp/{repo_name}/"):
            # Remove the "temp/reponame/" prefix since repo_root already points to it
            top_entity_file = top_entity_file.replace(f"temp/{repo_name}/", "")
            print_blue(f"[GHDL-INCREMENTAL] Adjusted top entity file: {top_entity_file}")
        
        # Check if file exists
        full_path = os.path.join(repo_root, top_entity_file) if not os.path.isabs(top_entity_file) else top_entity_file
        if not os.path.exists(full_path):
            print_yellow(f"[GHDL-INCREMENTAL] ✗ File does not exist: {full_path}")
            continue
        
        print_green(f"[GHDL-INCREMENTAL] ✓ File exists: {full_path}")
        
        # Try incremental compilation
        rc, log, final_files = compile_incremental(
            repo_root,
            repo_name,
            candidate,
            top_entity_file,
            modules,
            ghdl_extra_flags=ghdl_extra_flags,
            timeout=timeout
        )
        
        if rc == 0:
            print_green(f"[GHDL-INCREMENTAL] ✓ Success with top entity: {candidate}")
            print_blue(f"[GHDL-INCREMENTAL] Final files: {len(final_files)}")
            return True, log, final_files, candidate
        
        print_yellow(f"[GHDL-INCREMENTAL] ✗ Failed with top entity: {candidate}")
    
    print_red("[GHDL-INCREMENTAL] All candidates failed")
    return False, "", [], ""