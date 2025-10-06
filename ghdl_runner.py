"""
GHDL analyze/elaboration runner for VHDL sources with dependency resolution and minimization.

We use VHDL-2008 by default. -fsynopsys enables some Synopsys-compatible VHDL constructs that
many open-source cores rely on; we expose it as an optional flag the caller can pass if needed.

Public API:
- analyze_with_dependency_resolution(...): iterative analyze while fixing missing entities/packages
- minimize_files(...): remove-one-by-one while keeping analysis clean
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import List, Tuple, Set, Dict
from core.log import print_green, print_yellow, print_red, print_blue
import shlex


def _run(cmd: List[str], cwd: str, timeout: int, use_fish: bool = True, stream_to_console: bool = True) -> Tuple[int, str]:
    start = time.time()
    out_lines: List[str] = []
    try:
        if use_fish:
            cmd_str = " ".join(shlex.quote(x) for x in cmd)
            shell_exe = "/usr/bin/fish" if os.path.exists("/usr/bin/fish") else os.environ.get("SHELL", "/bin/sh")
            proc = subprocess.Popen(
                cmd_str,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                executable=shell_exe,
            )
        else:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                out_lines.append(line)
                if stream_to_console:
                    print(line, end="")
            if time.time() - start > timeout:
                try:
                    proc.kill()
                except Exception:
                    pass
                out_lines.append("\n[TIMEOUT] GHDL analyze timed out\n")
                return 124, "".join(out_lines)
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        out_lines.append(f"\n[EXCEPTION] {e}\n")
        return 1, "".join(out_lines)
    return proc.returncode or 0, "".join(out_lines)


def _parse_missing_entities(log_text: str) -> List[str]:
    missing = set()
    patterns = [
        r'unit "([^"]+)" not found in library "work"',
        r"unit '([^']+)' not found in library 'work'",
        r'entity "([^"]+)" not found',
        r"entity '([^']+)' not found",
        r'cannot find entity "([^"]+)"',
        r"cannot find entity '([^']+)'",
        r'undefined entity "([^"]+)"',
        r"undefined entity '([^']+)'",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing.add(m.group(1))
    return list(missing)


def _parse_missing_packages_with_context(log_text: str) -> List[Tuple[str, str]]:
    """Parse GHDL output for missing package errors with the file context.
    Returns list of (file_with_error, missing_package_name) tuples.
    
    Example error:
    src/pp_constants.vhd:8:10:error: unit "pp_types" not found in library "work"
    """
    missing = []
    # Pattern: filename:line:col:error: unit "package_name" not found
    pattern = r'([^\s:]+\.vhdl?):\d+:\d+:error:\s+unit\s+["\']([^"\']+)["\']\s+not\s+found'
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        filename = m.group(1)
        package = m.group(2)
        missing.append((filename, package))
    return missing


def _parse_missing_packages(log_text: str) -> List[str]:
    missing = set()
    patterns = [
        r"package\s+'([^']+)'\s+not\s+found",
        r"cannot\s+find\s+package\s+'([^']+)'",
        r"unknown\s+package\s+'([^']+)'",
        r'package\s+"([^\"]+)"\s+not\s+found',
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing.add(m.group(1))
    return list(missing)


def _parse_syntax_error_files(log_text: str) -> List[str]:
    """Parse GHDL output to collect files with syntax/parse errors."""
    error_files = set()
    patterns = [
        r"(^|\n)([^\s:]+\.vhd[l]?):\d+:\d+:\s*(?:error:)?\s*(?:syntax|parse|unexpected)",
        r"(^|\n)error: .*? in file ([^\s:]+\.vhd[l]?)",
        r"(^|\n)\*\*\s+error:.*?\s+in\s+([^\s:]+\.vhd[l]?)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            # file group index depends on pattern; pick the last captured group
            for g in reversed(m.groups()):
                if g and g.lower().endswith((".vhd", ".vhdl")):
                    error_files.add(g)
                    break
    return list(error_files)


def _parse_duplicate_declarations(log_text: str) -> List[str]:
    """Parse GHDL output to detect duplicate declaration files."""
    duplicate_files = set()
    patterns = [
        r"(^|\n)([^\s:]+\.vhd[l]?):\d+:\d+:\s*(?:error:)?\s*duplicate",
        r"duplicate\s+declaration.*?\s+in\s+([^\s:]+\.vhd[l]?)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            for g in reversed(m.groups()):
                if g and g.lower().endswith((".vhd", ".vhdl")):
                    duplicate_files.add(g)
                    break
    return list(duplicate_files)


def _reorder_by_ghdl_errors(files: List[str], log_text: str, repo_root: str) -> Tuple[List[str], bool]:
    """Reorder files based on GHDL missing package/entity errors.
    
    Parses GHDL errors for missing units (packages or entities) and reorders files
    so that provider files come before files that depend on them.
    
    Returns (reordered_files, changed) where changed indicates if order was modified.
    """
    missing_deps = _parse_missing_packages_with_context(log_text)
    if not missing_deps:
        return files, False
    
    # Build a map: package/entity name -> file that declares it
    package_to_file: Dict[str, str] = {}
    for f in files:
        try:
            full_path = os.path.join(repo_root, f) if not os.path.isabs(f) else f
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read(12000)
                # Look for "package <name> is"
                pkg_match = re.search(r'^\s*package\s+(\w+)\s+is\b', content, flags=re.IGNORECASE | re.MULTILINE)
                if pkg_match:
                    pkg_name = pkg_match.group(1).lower()
                    package_to_file[pkg_name] = f
                # Also look for "entity <name> is"
                ent_match = re.search(r'^\s*entity\s+(\w+)\s+is\b', content, flags=re.IGNORECASE | re.MULTILINE)
                if ent_match:
                    ent_name = ent_match.group(1).lower()
                    package_to_file[ent_name] = f
        except Exception:
            continue
    
    # Build constraints: file A must come before file B
    must_come_before: Dict[str, Set[str]] = {}  # provider_file -> set of files that need it
    
    for error_file, missing_pkg in missing_deps:
        # Normalize error_file path to match our file list
        error_file_normalized = None
        error_basename = os.path.basename(error_file)
        for f in files:
            if os.path.basename(f) == error_basename:
                error_file_normalized = f
                break
        
        if not error_file_normalized:
            continue
        
        # Find which file provides this package
        provider_file = package_to_file.get(missing_pkg.lower())
        if provider_file and provider_file != error_file_normalized:
            if provider_file not in must_come_before:
                must_come_before[provider_file] = set()
            must_come_before[provider_file].add(error_file_normalized)
    
    if not must_come_before:
        return files, False
    
    # Reorder: move provider files before their dependents
    result = list(files)
    changed = False
    
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
            changed = True
    
    return result, changed


def _order_vhdl_files(files: List[str], repo_root: str | None = None) -> List[str]:
    """Place package files first, then the rest, keeping stable order within groups.
    
    NOTE: This function now does minimal pre-ordering to avoid conflicting with
    dynamic error-based reordering. Let GHDL errors guide the correct order.
    """
    # Just return files as-is - dynamic reordering will fix the order based on actual errors
    return files


def _find_entity_files(repo_root: str, entity_names: List[str]) -> List[str]:
    found: List[str] = []
    for root, _dirs, files in os.walk(repo_root):
        for fname in files:
            if not fname.lower().endswith((".vhd", ".vhdl")):
                continue
            for en in entity_names:
                # quick filename heuristic first
                if en.lower() in fname.lower():
                    rel = os.path.relpath(os.path.join(root, fname), repo_root)
                    found.append(rel)
    return found


def _find_files_referencing_entity(repo_root: str, current_files: List[str], entity_name: str) -> List[str]:
    """Find files that reference (instantiate or use) a specific entity.
    Returns list of files that contain references to the entity.
    """
    referencing_files = []
    patterns = [
        rf'\b{re.escape(entity_name)}\s*:\s*entity\s+work\.{re.escape(entity_name)}',  # component instantiation
        rf'\bwork\.{re.escape(entity_name)}\b',  # work.entity_name reference
        rf'\bcomponent\s+{re.escape(entity_name)}\b',  # component declaration
    ]
    
    for f in current_files:
        try:
            full_path = os.path.join(repo_root, f) if not os.path.isabs(f) else f
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
                for pat in patterns:
                    if re.search(pat, content, flags=re.IGNORECASE):
                        referencing_files.append(f)
                        break
        except Exception:
            continue
    
    return referencing_files


def _build_analyze_cmd(files: List[str], ghdl_extra_flags: List[str] | None, workdir: str | None = None) -> List[str]:
    cmd = ["ghdl", "-a", "--std=08"]
    if ghdl_extra_flags:
        cmd.extend(ghdl_extra_flags)
    if workdir:
        cmd.append(f"--workdir={workdir}")
    cmd.extend(files)
    return cmd


def _validation_flags(ghdl_extra_flags: List[str] | None) -> List[str]:
    """Return flags for strict validation:
    - keep relaxed parsing (-frelaxed) for VHDL features
    - treat binding warnings as errors (--warn-error=binding) to catch missing entities
    """
    base = list(ghdl_extra_flags or [])
    # Keep -frelaxed for shared variables and other VHDL relaxations
    # But add --warn-error=binding to catch missing entities/components
    has_warn_binding = any((f.startswith("--warn-error=") and "binding" in f) for f in base)
    if not has_warn_binding:
        base.append("--warn-error=binding")
    return base


def _ghdl_clean_work(repo_root: str, workdir: str) -> None:
    # GHDL typically uses work-obj08.cf in cwd. Keep per-attempt temp dir and clean it.
    if os.path.exists(os.path.join(workdir, "work-obj08.cf")):
        try:
            os.remove(os.path.join(workdir, "work-obj08.cf"))
        except Exception:
            pass


def analyze_with_dependency_resolution(
    repo_root: str,
    files: List[str],
    timeout: int = 300,
    ghdl_extra_flags: List[str] | None = None,
    max_retries: int = 2,
    excluded_files_blacklist: Set[str] | None = None,
) -> Tuple[int, str, List[str], str]:
    """
    Analyze all files with GHDL, automatically resolving dependencies through:
    - Dynamic file reordering based on missing package/entity errors
    - Adding missing entity files when found
    - Excluding problematic files (syntax errors, duplicates, missing dependencies)
    
    Returns: (return_code, log, final_files, tmpdir)
    The tmpdir contains the analyzed GHDL work library and should be cleaned up by the caller.
    """
    excluded = set(excluded_files_blacklist or [])
    current_files = [f for f in files if f not in excluded]
    print_green(f"[GHDL] Dependency resolution start | files={len(current_files)}")
    tmpdir = tempfile.mkdtemp(prefix="ghdl_", dir=repo_root)
    skip_initial_ordering = False  # Track if files are already ordered from dynamic reordering
    attempt_count = 0
    max_total_attempts = max(max_retries * 3, 20)  # Allow more attempts for reordering
    try:
        while attempt_count < max_total_attempts:
            attempt_count += 1
            _ghdl_clean_work(repo_root, tmpdir)
            # Run from repo_root so relative file paths resolve; keep work files in tmpdir
            if skip_initial_ordering:
                ordered = current_files
                skip_initial_ordering = False
            else:
                ordered = _order_vhdl_files(current_files, repo_root)
            cmd = _build_analyze_cmd(ordered, ghdl_extra_flags, workdir=tmpdir)
            print_blue(f"[GHDL] Attempt {attempt_count}/{max_total_attempts}")
            rc, out = _run(cmd, cwd=repo_root, timeout=timeout)
            if rc == 0:
                print_green(f"[GHDL] Analyze clean | files={len(current_files)}")
                return rc, out, current_files, tmpdir
            # Output already streamed live; avoid duplicate dumps

            missing_entities = _parse_missing_entities(out)
            missing_packages = _parse_missing_packages(out)
            syntax_error_files = _parse_syntax_error_files(out)
            duplicate_files = _parse_duplicate_declarations(out)
            changed = False

            # Try dynamic reordering based on GHDL's missing package/entity errors
            reordered_files, was_reordered = _reorder_by_ghdl_errors(current_files, out, repo_root)
            if was_reordered:
                current_files = reordered_files
                changed = True
                skip_initial_ordering = True
                continue

            # Exclude files with syntax or duplicate declaration errors
            for bad in syntax_error_files + duplicate_files:
                # Try to normalize error path to current repo-relative files
                rel = bad
                if os.path.isabs(bad):
                    try:
                        rel = os.path.relpath(bad, repo_root)
                    except Exception:
                        rel = bad
                # If not directly present, try basename unique match
                if rel not in current_files:
                    base = os.path.basename(rel)
                    matches = [f for f in current_files if os.path.basename(f) == base]
                    if len(matches) == 1:
                        rel = matches[0]
                if rel in current_files:
                    excluded.add(rel)
                    if excluded_files_blacklist is not None:
                        excluded_files_blacklist.add(rel)
                    current_files = [f for f in current_files if f != rel]
                    print_yellow(f"[GHDL] Excluding file due to duplicate/syntax: {rel}")
                    changed = True

            # Add files that likely contain missing entities
            if missing_entities:
                entity_files = _find_entity_files(repo_root, missing_entities)
                added_any = False
                for p in entity_files:
                    if p not in current_files and p not in excluded:
                        current_files.append(p)
                        print_green(f"[GHDL] Added entity file: {p}")
                        changed = True
                        added_any = True
                
                # If no files found for missing entities, exclude files that reference them
                # BUT only if they're in example/test directories (likely testbenches/wrappers)
                if not added_any:
                    for entity_name in missing_entities:
                        referencing_files = _find_files_referencing_entity(repo_root, current_files, entity_name)
                        for ref_file in referencing_files:
                            # Only exclude if it's clearly an example/test/simulation file
                            ref_lower = ref_file.lower()
                            if any(x in ref_lower for x in ['example/', 'test/', 'tb_', 'testbench', 'sim/']):
                                if ref_file in current_files:
                                    excluded.add(ref_file)
                                    if excluded_files_blacklist is not None:
                                        excluded_files_blacklist.add(ref_file)
                                    current_files = [f for f in current_files if f != ref_file]
                                    print_yellow(f"[GHDL] Excluding example/test file referencing missing entity '{entity_name}': {ref_file}")
                                    changed = True

            # If missing packages are referenced, try to find packages by filename hint
            if missing_packages:
                pkg_files = _find_entity_files(repo_root, [p + "_pkg" for p in missing_packages])
                for p in pkg_files:
                    if p not in current_files and p not in excluded:
                        current_files.append(p)
                        print_green(f"[GHDL] Added package file: {p}")
                        changed = True

            if not changed:
                print_red("[GHDL] No further automatic fixes possible")
                return rc, out, current_files, tmpdir

        # Final attempt
        _ghdl_clean_work(repo_root, tmpdir)
        final_cmd = _build_analyze_cmd(_order_vhdl_files(current_files, repo_root), ghdl_extra_flags, workdir=tmpdir)
        rc, out = _run(final_cmd, cwd=repo_root, timeout=timeout)
        return rc, out, current_files, tmpdir
    except Exception as e:
        # Clean up tmpdir on exception
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
        raise e


def minimize_files(
    repo_root: str,
    files: List[str],
    timeout: int = 300,
    ghdl_extra_flags: List[str] | None = None,
    top_entity: str | None = None,
) -> Tuple[List[str], str]:
    """
    Remove files one-by-one and keep the removal if GHDL analyze remains clean.
    Returns: (final_files, last_log)
    """
    print_green(f"[GHDL] Minimization start | initial files={len(files)}")
    keep = list(files)
    last_log = ""
    tmpdir = tempfile.mkdtemp(prefix="ghdl_min_", dir=repo_root)
    try:
        for f in list(keep):
            trial = [x for x in keep if x != f]
            print_blue(f"[GHDL] Try remove: {f}")
            # Ensure a clean workdir each trial to avoid stale units
            _ghdl_clean_work(repo_root, tmpdir)
            if top_entity:
                # Analyze + elaborate top to validate
                strict_flags = _validation_flags(ghdl_extra_flags)
                analyze_cmd = _build_analyze_cmd(_order_vhdl_files(trial, repo_root), strict_flags, workdir=tmpdir)
                rc_a, out_a = _run(analyze_cmd, cwd=repo_root, timeout=timeout)
                last_log = out_a
                if rc_a == 0:
                    elab_cmd = ["ghdl", "-e", "--std=08", f"--workdir={tmpdir}"]
                    if strict_flags:
                        elab_cmd.extend(strict_flags)
                    elab_cmd.append(top_entity)
                    rc_e, out_e = _run(elab_cmd, cwd=repo_root, timeout=timeout)
                    last_log += "\n" + out_e
                    if rc_e == 0:
                        keep = trial
                        print_yellow(f"[GHDL] Removal accepted: {f}")
            else:
                # Analyze-only fallback
                strict_flags = _validation_flags(ghdl_extra_flags)
                cmd = _build_analyze_cmd(_order_vhdl_files(trial, repo_root), strict_flags, workdir=tmpdir)
                rc, out = _run(cmd, cwd=repo_root, timeout=timeout)
                last_log = out
                if rc == 0:
                    keep = trial
                    print_yellow(f"[GHDL] Removal accepted: {f}")
        print_green(f"[GHDL] Minimization done | kept={len(keep)}")
        return keep, last_log
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def _analyze_and_elaborate(
    repo_root: str,
    files: List[str],
    top_entity: str,
    timeout: int = 300,
    ghdl_extra_flags: List[str] | None = None,
    tmpdir: str | None = None,
) -> Tuple[int, str]:
    """
    Analyze files and elaborate the top entity.
    
    If tmpdir is provided, assumes files are already analyzed in that directory and
    only performs elaboration. Otherwise, creates a new temporary directory, analyzes
    all files, then elaborates.
    
    Returns: (return_code, combined_output)
    """
    should_cleanup = False
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp(prefix="ghdl_build_", dir=repo_root)
        should_cleanup = True
    try:
        # Use validation flags (keeps -frelaxed but adds --warn-error=binding)
        flags = _validation_flags(ghdl_extra_flags)
        
        # Only analyze if this is a new tmpdir
        if should_cleanup:
            analyze_cmd = _build_analyze_cmd(_order_vhdl_files(files, repo_root), flags, workdir=tmpdir)
            rc_a, out_a = _run(analyze_cmd, cwd=repo_root, timeout=timeout)
            if rc_a != 0:
                # Output already streamed live; avoid duplicate dumps
                return rc_a, out_a
        else:
            out_a = ""
            
        # Elaborate
        elab_cmd = ["ghdl", "-e", "--std=08", f"--workdir={tmpdir}"]
        if flags:
            elab_cmd.extend(flags)
        elab_cmd.append(top_entity)
        rc_e, out_e = _run(elab_cmd, cwd=repo_root, timeout=timeout)
        if rc_e != 0:
            # Output already streamed live; avoid duplicate dumps
            pass
        return rc_e, (out_a + "\n" + out_e) if out_a else out_e
    finally:
        if should_cleanup:
            try:
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass


def auto_orchestrate(
    repo_root: str,
    repo_name: str,
    tb_files: List[str],
    candidate_files: List[str],
    include_dirs_unused: Set[str] | None,
    top_candidates: List[str],
    language_version: str,
    timeout: int = 300,
    ghdl_extra_flags: List[str] | None = None,
    max_retries: int = 2,
    excluded_files_blacklist: Set[str] | None = None,
) -> Tuple[List[str], Set[str], str, str, bool]:
    """End-to-end flow for VHDL: try candidates, resolve deps, minimize, final check."""
    print_green(f"[GHDL] Orchestrate start | candidates={len(top_candidates)} files={len(candidate_files)}")
    
    # Limit number of candidates for large projects to avoid excessive testing
    MAX_CANDIDATES_TO_TRY = 10
    if len(top_candidates) > MAX_CANDIDATES_TO_TRY:
        print_yellow(f"[GHDL] Large project detected ({len(top_candidates)} candidates). Limiting to top {MAX_CANDIDATES_TO_TRY} candidates.")
        top_candidates = top_candidates[:MAX_CANDIDATES_TO_TRY]
    
    files = list(candidate_files)
    last_log = ""
    selected_top = top_candidates[0] if top_candidates else ""
    last_fixed_files = files  # Track the last reordered files
    shared_tmpdir = None  # Track the tmpdir across attempts

    try:
        # Try candidates
        for cand in top_candidates:
            print_green(f"[GHDL] Trying top candidate: {cand}")
            rc, out, fixed_files, tmpdir = analyze_with_dependency_resolution(
                repo_root,
                files,
                timeout=timeout,
                ghdl_extra_flags=ghdl_extra_flags,
                max_retries=max_retries,
                excluded_files_blacklist=excluded_files_blacklist,
            )
            last_log = out
            last_fixed_files = fixed_files  # Always save the latest reordered files
            
            # Clean up previous tmpdir if we have a new one
            if shared_tmpdir and shared_tmpdir != tmpdir:
                try:
                    shutil.rmtree(shared_tmpdir, ignore_errors=True)
                except Exception:
                    pass
            shared_tmpdir = tmpdir
            
            if rc == 0:
                # Elaborate selected cand using the same tmpdir
                print_green(f"[GHDL] Selected candidate for elaborate: {cand}")
                rc_e, out_e = _analyze_and_elaborate(repo_root, fixed_files, cand, timeout=timeout, ghdl_extra_flags=ghdl_extra_flags, tmpdir=tmpdir)
                last_log = out_e
                if rc_e == 0:
                    selected_top = cand
                    files = fixed_files
                    break

        # Use the reordered files even if no candidate fully succeeded
        if files != last_fixed_files:
            files = last_fixed_files

        # Minimization (invalidates tmpdir since file set changes)
        minimized_files, min_log = minimize_files(repo_root, files, timeout=timeout, ghdl_extra_flags=ghdl_extra_flags, top_entity=selected_top)
        last_log = min_log or last_log

        # Final check (tmpdir no longer valid after minimization, so don't pass it)
        print_green(f"[GHDL] Final elaborate | files={len(minimized_files)} top={selected_top}")
        rc_f, out_f = _analyze_and_elaborate(repo_root, minimized_files, selected_top, timeout=timeout, ghdl_extra_flags=ghdl_extra_flags, tmpdir=None)
        last_log = out_f
        is_simulable = (rc_f == 0)
    finally:
        # Clean up the shared tmpdir
        if shared_tmpdir:
            try:
                shutil.rmtree(shared_tmpdir, ignore_errors=True)
            except Exception:
                pass

    # --- Final cleanup pass: one more minimization after all checks ---
    if is_simulable:
        minimized_files, min_log2 = minimize_files(repo_root, minimized_files, timeout=timeout, ghdl_extra_flags=ghdl_extra_flags, top_entity=selected_top)
        last_log = min_log2 or last_log
        print_green(f"[GHDL] Final elaborate (post-cleanup) | files={len(minimized_files)} top={selected_top}")
        rc_fc, out_fc = _analyze_and_elaborate(repo_root, minimized_files, selected_top, timeout=timeout, ghdl_extra_flags=ghdl_extra_flags)
        last_log = out_fc
        is_simulable = (rc_fc == 0)

    return minimized_files, set(), last_log, selected_top, is_simulable
