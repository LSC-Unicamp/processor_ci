"""
Verilator compile/lint runner with dependency resolution and file minimization.

Responsibilities:
- Lint-only compile using Verilator for Verilog/SystemVerilog sources
- Parse errors to detect missing includes/modules, duplicate definitions, syntax errors
- Resolve dependencies by adding include dirs and candidate module files
- Minimize file set by removing non-essential files one-by-one while keeping lint clean

Public API:
- compile_with_dependency_resolution(...): iterative compile with fixes
- minimize_files(...): remove-one-by-one minimization using lint checks
"""
from __future__ import annotations

import os
import re
import subprocess
import time
from typing import List, Tuple, Set, Dict
from core.log import print_green, print_yellow, print_red, print_blue
import shlex

from core.file_manager import (
    find_missing_modules,
    find_missing_module_files,
)


def _normalize_path(path: str, repo_root: str) -> str:
    """
    Normalize a file path to be relative to repo_root for consistent comparison.
    Handles both absolute and relative paths, and normalizes path separators.
    """
    try:
        # If it's already absolute, make it relative
        if os.path.isabs(path):
            return os.path.relpath(path, repo_root).replace("\\", "/")
        # If it's relative, normalize separators and return as-is
        return path.replace("\\", "/")
    except Exception:
        # If normalization fails, just normalize separators
        return path.replace("\\", "/")


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

    file_to_imports: Dict[str, Set[str]] = {f: set() for f in files}
    pkg_to_file: Dict[str, str] = {}
    # Map: define name -> file that defines it
    define_to_file: Dict[str, str] = {}
    # Map: file -> set of defines it requires to NOT be defined yet (must come before definer)
    file_to_forbidden_defines: Dict[str, Set[str]] = {f: set() for f in files}

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
        # Explicit ordering constraints: ifdef + error means must come before definer
        for m in ifdef_error_re.finditer(text):
            define = m.group(1)
            if define:
                file_to_forbidden_defines[f].add(define)
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


def _effective_language(files: List[str], language_version: str) -> Tuple[str, str]:
    """Compute the effective language mode and standard for Verilator.

    Returns (mode, standard), where mode is 'sv' or 'verilog', and standard is
    '1800-2017' or '1364-2005'. This mirrors the logic used when building the
    Verilator command line, so callers can log a reliable value.
    """
    has_sv = any(str(f).lower().endswith((".sv", ".svh")) for f in files)
    lang = (language_version or "").strip()
    if (lang and lang.startswith("1800")) or has_sv:
        return "sv", "1800-2017"
    # Classic Verilog (2005)
    if any(k in lang for k in ("2005", "1364-2005")) or lang.lower() in {"verilog-2005", "1364-2005ext+"}:
        return "verilog", "1364-2005"
    # Fallback: if no explicit hint, prefer Verilog-2005 when all files are .v, else SV
    if not has_sv:
        return "verilog", "1364-2005"
    return "sv", "1800-2017"


def _path_score_generic(p: str) -> Tuple[int, int, int]:
    """Generic path scoring for source quality.

    Higher is better. Based on presence/absence of common tokens; no repo-specific rules.
    Returns a tuple for stable sorting: (score, desired_hits, -undesired_hits). Shorter paths tie-break.
    """
    pl = p.replace('\\', '/').lower()

    # Tokenize by separators and also split camel-case words (e.g., VivadoSim -> vivado, sim)
    raw_tokens = [t for t in re.split(r"[/_.-]+", pl) if t]
    split_tokens: Set[str] = set()
    for t in raw_tokens:
        # split camel case boundaries
        cc = re.sub(r"([a-z])([A-Z])", r"\1 \2", t, flags=0)
        for sub in cc.replace('-', ' ').replace('_', ' ').split():
            if sub:
                split_tokens.add(sub.lower())

    tokens = split_tokens
    desired = {
        'src', 'rtl', 'core', 'cpu', 'hdl', 'ip', 'lib'
    }
    undesired = {
        'sim', 'simulation', 'tb', 'test', 'tests', 'testing', 'verification', 'verif', 'bench', 'example', 'examples', 'sample',
        'project', 'proj', 'vivado', 'vivadosim', 'quartus', 'fpga', 'board', 'boards', 'platform', 'syn', 'synth', 'asic', 'modelsim', 'questa',
        'vendor', 'third', 'thirdparty', 'third-party', 'doc', 'docs', 'script', 'scripts', 'cmake', 'make', 'build', 'out', 'obj', 'work'
    }
    desired_hits = sum(1 for t in tokens if t in desired)
    undesired_hits = sum(1 for t in tokens if t in undesired)
    score = desired_hits * 3 - undesired_hits * 4
    # Bonus if file extension is a source (not header-only) to break ties when symbols equal
    if pl.endswith(('.sv', '.v')):
        score += 1
    # Slight bonus for shorter paths (closer to repo root)
    score -= len(pl) // 80  # diminish very long subpaths
    return score, desired_hits, -undesired_hits


def _extract_declared_symbols(repo_root: str, rel_path: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """Return (modules, interfaces, packages) declared by the file. Empty sets if unreadable.
    Only looks for top-level declarations via regex; fast approximation.
    """
    mods: Set[str] = set()
    ifs: Set[str] = set()
    pkgs: Set[str] = set()
    full = os.path.join(repo_root, rel_path) if not os.path.isabs(rel_path) else rel_path
    try:
        with open(full, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read(200000)
        # Remove block comments quickly to reduce false positives
        content = re.sub(r"/\*.*?\*/", "\n", content, flags=re.S)
        # Capture package names
        for m in re.finditer(r"^\s*package\s+([a-zA-Z_]\w*)\s*;", content, flags=re.M):
            pkgs.add(m.group(1))
        # Capture interfaces
        for m in re.finditer(r"^\s*interface\s+([a-zA-Z_]\w*)\b", content, flags=re.M):
            ifs.add(m.group(1))
        # Capture modules (exclude 'module automatic' handled by same regex)
        for m in re.finditer(r"^\s*module\s+([a-zA-Z_]\w*)\b", content, flags=re.M):
            mods.add(m.group(1))
    except Exception:
        return set(), set(), set()
    return mods, ifs, pkgs


def _tokenize_path_components(pl: str) -> Set[str]:
    raw_tokens = [t for t in re.split(r"[/_.-]+", pl) if t]
    split_tokens: Set[str] = set()
    for t in raw_tokens:
        cc = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)
        for sub in cc.replace('-', ' ').replace('_', ' ').split():
            if sub:
                split_tokens.add(sub.lower())
    return split_tokens


def _looks_like_wrapper_basename(base: str) -> bool:
    b = base.lower()
    if b.endswith(('.sv', '.v')):
        b = b.rsplit('.', 1)[0]
    patterns = [
        r"^tb_", r"_tb$", r"test", r"bench", r"^main$", r"^top_tb$", r"^tb$",
    ]
    return any(re.search(p, b, flags=re.I) for p in patterns)


def _source_has_sim_initials(full_path: str) -> bool:
    """Check if a file looks like a testbench based on simulation-only constructs.
    
    Returns True only if the file has ALL of:
    - timescale directive
    - initial blocks
    - simulation control statements ($finish/$stop/$dumpvars)
    AND
    - No module declarations (pure testbench)
    OR
    - The module name looks like a testbench (tb_, *_tb, *test*, etc.)
    
    This prevents false positives on RTL files that have debug code or initial blocks
    for register initialization.
    """
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
            head = fh.read(80000)  # Read more to catch module declarations
        
        has_timescale = re.search(r"^\s*`timescale", head, flags=re.I|re.M) is not None
        has_initial = re.search(r"^\s*initial\b", head, flags=re.I|re.M) is not None
        has_sim_control = re.search(r"\$(finish|stop|dumpvars|dumpfile)\b", head, flags=re.I) is not None
        
        if not (has_timescale and has_initial and has_sim_control):
            return False
        
        # Check if there's a module declaration
        module_match = re.search(r"^\s*module\s+(\w+)", head, flags=re.I|re.M)
        if not module_match:
            # No module = likely a pure testbench file
            return True
        
        # If there's a module, check if the name suggests it's a testbench
        module_name = module_match.group(1).lower()
        if re.search(r"(^tb_|_tb$|test|bench|sim)", module_name, flags=re.I):
            return True
        
        # Has module with normal name and sim constructs = likely RTL with debug code
        return False
    except Exception:
        return False


def _is_wrapperish_source(path: str, repo_root: str | None = None) -> bool:
    """Generic detection for sim/testbench/project wrapper sources.

    Heuristics (conservative):
      - Path tokens include strong sim/test tokens (sim, tb, test, bench, example, vivado, modelsim, verification)
      - Basename looks like a testbench (tb_*, *_tb, *test*, *bench*, main)
      - Content has timescale + initial + $finish/$stop/$dumpvars

    Note: Do NOT classify sources as wrappers merely because they live under a 'project'/'proj' folder,
    as many repos keep real RTL there (e.g., arRISCado/project/...).
    """
    try:
        p = path.replace('\\', '/').lower()
    except Exception:
        p = str(path).lower()
    tokens = _tokenize_path_components(p)
    # Strong indicators of sim/test wrappers
    strong_tokens = {
        'sim', 'simulation', 'tb', 'test', 'tests', 'testing', 'bench', 'example', 'examples', 'sample',
        'vivado', 'vivadosim', 'quartus', 'modelsim', 'questa', 'verification'
    }
    # Mild tokens that should NOT by themselves mark a file as wrapperish
    mild_tokens = {'project', 'proj'}

    base = os.path.basename(p)
    token_hit_strong = bool(tokens & strong_tokens)
    base_hit = _looks_like_wrapper_basename(base)
    content_hit = False
    if repo_root:
        full = os.path.join(repo_root, path) if not os.path.isabs(path) else path
        content_hit = _source_has_sim_initials(full)
    # Consider wrapper if strong tokens found, or basename looks like a bench, or content shows sim initials
    if token_hit_strong or base_hit or content_hit:
        return True
    # Presence of only mild tokens (like 'project') is not enough
    return False


def _is_wrapperish_module_name(name: str) -> bool:
    n = (name or '').lower()
    return (
        n == 'main' or n == 'tb' or n.endswith('_tb') or n.startswith('tb_') or
        'test' in n or 'bench' in n
    )


def _dedupe_files_generically(files: List[str], repo_root: str | None = None) -> List[str]:
    """Generic dedupe across files providing the same declared symbols or sharing basename.

    Steps:
    - If repo_root is provided, parse each file for declared modules/interfaces/packages.
      For each symbol, keep the path with best generic path score; drop others.
    - For files without detected symbols, fallback to deduping by basename using path score.
    - Always keep unique files.
    """
    if not files:
        return files

    keep: Set[str] = set()
    if repo_root:
        symbol_to_files: Dict[str, List[str]] = {}
        file_to_symbols: Dict[str, Set[str]] = {}
        file_has_symbols: Dict[str, bool] = {}
        for f in files:
            mods, ifs, pkgs = _extract_declared_symbols(repo_root, f)
            syms = set()
            syms.update({f"mod::{m}" for m in mods})
            syms.update({f"if::{i}" for i in ifs})
            syms.update({f"pkg::{p}" for p in pkgs})
            file_has_symbols[f] = bool(syms)
            file_to_symbols[f] = syms
            for s in syms:
                symbol_to_files.setdefault(s, []).append(f)

        # Choose best provider per symbol
        symbol_best: Dict[str, str] = {}
        for sym, paths in symbol_to_files.items():
            if len(paths) == 1:
                keep.add(paths[0])
                symbol_best[sym] = paths[0]
                continue
            best = sorted(paths, key=lambda p: (_path_score_generic(p), len(p)), reverse=True)[0]
            keep.add(best)
            symbol_best[sym] = best
            dropped = [p for p in paths if p != best]

        # Coalesce winners by basename: keep only the best-scored file per basename
        by_base_keep: Dict[str, List[str]] = {}
        for f in list(keep):
            by_base_keep.setdefault(os.path.basename(f), []).append(f)
        for base, paths in by_base_keep.items():
            if len(paths) <= 1:
                continue
            best = sorted(paths, key=lambda p: (_path_score_generic(p), len(p)), reverse=True)[0]
            for p in paths:
                if p != best and p in keep:
                    keep.remove(p)

        # For files with no symbols (headers or utility), fallback to basename dedupe
        by_base: Dict[str, List[str]] = {}
        for f in files:
            if f in keep:
                continue
            base = os.path.basename(f)
            by_base.setdefault(base, []).append(f)
        for base, paths in by_base.items():
            if len(paths) == 1:
                keep.add(paths[0])
            else:
                best = sorted(paths, key=lambda p: (_path_score_generic(p), len(p)), reverse=True)[0]
                keep.add(best)
                dropped = [p for p in paths if p != best]
        return [f for f in files if f in keep]

    # No repo_root: fallback to basename scoring only
    by_base: Dict[str, List[str]] = {}
    for f in files:
        by_base.setdefault(os.path.basename(f), []).append(f)
    out: List[str] = []
    for base, paths in by_base.items():
        if len(paths) == 1:
            out.append(paths[0])
        else:
            best = sorted(paths, key=lambda p: (_path_score_generic(p), len(p)), reverse=True)[0]
            out.append(best)
            dropped = [p for p in paths if p != best]
            if dropped:
                print_yellow(f"[VERILATOR] Dedupe basename '{base}': keeping {best}, dropping {', '.join(dropped)}")
    return out


def _build_verilator_cmd(
    files: List[str],
    include_dirs: Set[str],
    top_module: str | None,
    language_version: str,
    extra_flags: List[str] | None,
    repo_root: str | None = None,
) -> List[str]:
    cmd: List[str] = [
        "verilator",
        "--lint-only",
        "-Wall",
        "--no-timing",
        "-Wno-PROCASSWIRE",
        "--relative-includes",
    ]

    # Language/version switches
    # Use SystemVerilog if 1800-* is detected or any file is .sv/.svh
    has_sv = any(str(f).lower().endswith((".sv", ".svh")) for f in files)
    lang = (language_version or "").strip()
    if (lang and lang.startswith("1800")) or has_sv:
        cmd.append("--sv")
        # Be explicit about the language standard to avoid parser ambiguity
        cmd.extend(["--language", "1800-2017"])  # SystemVerilog 2017
    else:
        # For classic Verilog, enforce Verilog-2005 when requested (or detected),
        # to prevent SV keywords (e.g., 'byte', 'do') from being treated specially.
        if any(k in lang for k in ("2005", "1364-2005")) or lang.lower() in {"verilog-2005", "1364-2005ext+"}:
            cmd.extend(["--language", "1364-2005"])  # Verilog 2005

    if top_module:
        cmd.extend(["--top-module", top_module])

    # Include directories (Verilator expects -I<dir> without space)
    # Filter out problematic legacy directories that cause undefined macro/package errors
    for idir in sorted(include_dirs):
        idir_lower = idir.lower()
        # Skip legacy Rocket chip integration directories - they have undefined macros and missing packages
        if "/bsg_legacy/" in idir_lower and any(x in idir_lower for x in ["/bsg_chip/", "/bsg_fsb/", "/bsg_tag/"]):
            print_yellow(f"[VERILATOR] Skipping legacy include dir: {idir}")
            continue
        # Verilator expects native paths; repo_root is handled by caller providing relative dirs
        cmd.append(f"-I{idir}")

    if extra_flags:
        cmd.extend(extra_flags)

    # Add files at the end, ordering with package-aware generic algorithm
    # Dedupe generically (by declared symbols and generic path scoring) before ordering
    files_deduped = _dedupe_files_generically(files, repo_root)
    ordered_files = _order_sv_files(files_deduped, repo_root)
    cmd.extend(ordered_files)
    return cmd


def _fmt_list(items: List[str], max_items: int = 20) -> str:
    try:
        items = list(items)
        return ", ".join(items) if len(items) <= max_items else ", ".join(items[:max_items]) + f" ... (+{len(items)-max_items} more)"
    except Exception:
        return str(items)


def _summarize_verilator_log(log_text: str) -> Tuple[int, int]:
    """Return (warnings, errors) counts from Verilator output."""
    if not log_text:
        return 0, 0
    warns = len(re.findall(r"^%Warning", log_text, flags=re.MULTILINE))
    errs = len(re.findall(r"^%Error", log_text, flags=re.MULTILINE))
    return warns, errs


def _print_tool_output(tag: str, text: str, max_lines: int = 240) -> None:
    if not text:
        return
    lines = text.splitlines()
    print_red(f"{tag} (showing up to {max_lines} lines)")
    if len(lines) <= max_lines:
        print("\n".join(lines))
    else:
        head = max_lines // 2
        tail = max_lines - head
        print("\n".join(lines[:head]))
        print_yellow(f"... ({len(lines) - max_lines} lines omitted) ...")
        print("\n".join(lines[-tail:]))


def _collect_included_basenames(repo_root: str, files: List[str]) -> List[str]:
    """Scan given files for Verilog `include directives and return included basenames.

    This helps us proactively add -I directories before the first attempt when projects
    use bare includes like `include "BasicMacros.sv" placed in sibling folders.
    """
    includes: Set[str] = set()
    inc_re = re.compile(r"^\s*`include\s+[\"<]([^\">]+)[\">]", re.IGNORECASE | re.MULTILINE)
    for rel in files:
        if not rel.lower().endswith((".v", ".sv", ".svh", ".vh")):
            continue
        full = os.path.join(repo_root, rel) if not os.path.isabs(rel) else rel
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as fh:
                # Read a chunk from head; includes tend to be near the top
                content = fh.read(120000)
            for m in inc_re.finditer(content):
                inc_path = m.group(1).strip()
                if inc_path:
                    includes.add(os.path.basename(inc_path))
        except Exception:
            continue
    return sorted(includes)


def _run(cmd: List[str], cwd: str, timeout: int, use_fish: bool = True, stream_to_console: bool = True) -> Tuple[int, str]:
    """Run a command and stream output like a fish terminal.

    - If use_fish is True, invoke via the fish shell so quoting/behavior matches the user's shell.
    - If stream_to_console is True, print lines as they arrive for real-time visibility.
    """
    start = time.time()
    out_lines: List[str] = []

    try:
        if use_fish:
            # Build a shell command string compatible with fish quoting
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
                    # Print tool output live as if in terminal
                    print(line, end="")
            if time.time() - start > timeout:
                try:
                    proc.kill()
                except Exception:
                    pass
                out_lines.append("\n[TIMEOUT] Verilator lint timed out\n")
                return 124, "".join(out_lines)
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        out_lines.append(f"\n[EXCEPTION] {e}\n")
        return 1, "".join(out_lines)
    return proc.returncode or 0, "".join(out_lines)


def _parse_missing_includes(log_text: str) -> List[str]:
    missing = set()
    patterns = [
        r"can't find file \"([^\"]+)\"",
        r"Can't find file \"([^\"]+)\"",
        r"unable to find include file \"([^\"]+)\"",
        r"unable to find include file '([^']+)'",
        r"Cannot find include file: ['\"]([^'\"]+)['\"]",
        r"%Error: .*Cannot find include file: ['\"]([^'\"]+)['\"]",
        r"['\"]([^'\"]+\.(svh|vh|vhdr|v|sv))['\"] not found",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing.add(m.group(1))
    return list(missing)


def _parse_missing_include_pairs(log_text: str) -> List[Tuple[str, str]]:
    """Extract (including_file, include_path) pairs from Verilator missing include errors.
    Example line:
    %Error: path/to/file.v:12:5: Cannot find include file: '../../rtl/config.vh'
    """
    pairs: List[Tuple[str, str]] = []
    # Capture the source file and the quoted include path
    pat = re.compile(r"%Error:\s+([^:]+):\d+:\d+:\s*Cannot\s+find\s+include\s+file:\s*['\"]([^'\"]+)['\"]",
                     re.IGNORECASE)
    for m in pat.finditer(log_text):
        src = m.group(1).strip()
        inc = m.group(2).strip()
        pairs.append((src, inc))
    return pairs


def _parse_missing_modules(log_text: str) -> List[str]:
    missing_modules = set()
    patterns = [
        r"Cannot find file containing module: '([^']+)'",
        r'Cannot find file containing module: "([^"]+)"',
        r"Cannot find module '([^']+)'",
        r'Cannot find module "([^"]+)"',
        r"module '([^']+)' not found",
        r'module "([^"]+)" not found',
        r"undefined module '([^']+)'",
        r'undefined module "([^"]+)"',
        r"unresolved module '([^']+)'",
        r'unresolved module "([^"]+)"',
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text, flags=re.IGNORECASE):
            missing_modules.add(m.group(1))
    return list(missing_modules)


def _parse_missing_interfaces(log_text: str) -> List[str]:
    """Extract missing SystemVerilog interface names from Verilator output."""
    missing_if = set()
    patterns = [
        r"Cannot find file containing interface: '([^']+)'",
        r'Cannot find file containing interface: "([^"]+)"',
        r"unlinked interface\s+([^\s]+)",
        r"Unlinked interface\s+([^\s]+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text):
            name = m.group(1)
            # strip possible trailing punctuation
            name = name.strip().strip("',\")")
            if name:
                missing_if.add(name)
    return list(missing_if)


def _parse_duplicate_declarations(log_text: str) -> List[str]:
    duplicate_files = set()
    patterns = [
        r"%Warning-MODDUP: ([^:]+):\d+:\d+: Duplicate declaration of module:",
        r"%Error: ([^:]+):\d+:\d+: Duplicate declaration of module:",
        r"%Error: ([^:]+):\d+:\d+: Duplicate declaration of signal:",
        r"%Error: ([^:]+):\d+:\d+: Duplicate declaration of TYPEDEF:",
        r"%Error: ([^:]+):\d+:\d+: Duplicate declaration of task:",
        r"%Error: ([^:]+):\d+:\d+: Duplicate declaration of function:",
        r"Duplicate declaration.*?in\s+([^:]+):",
        r"([^:]+):\d+.*Duplicate declaration",
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, log_text):
            duplicate_files.add(m.group(1))
    return list(duplicate_files)


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
            print_yellow(f"[VERILATOR] Detected SystemVerilog keyword conflict: '{keyword}' used as identifier")
            return True
    
    return False


def _parse_syntax_error_files(log_text: str) -> List[str]:
    error_files = set()
    patterns = [
        r"%Error:\s+([^:]+\.s?v[h]?):\d+:\d+:.*(?:syntax error|parse error|Too many digits|unexpected)",
        r"%Error:\s+([^:]+\.s?v[h]?):\d+.*(?:syntax|parse|unexpected)",
        r"Error.*?:\s+([^:]+\.s?v[h]?):\d+.*(?:syntax|parse|unexpected)",
        r"Syntax error.*?in\s+([^:]+\.s?v[h]?)",
        r"Parse error.*?in\s+([^:]+\.s?v[h]?)",
        # Treat specific standard-violation errors as syntax-like to allow exclusion when optional
        r"%Error:\s+([^:]+\.s?v[h]?):\d+:\d+:\s*Mixing\s+positional\s+and\s+.*named\s+instantiation\s+connection",
        # Treat missing pin connections as syntax-like for board-specific wrapper files
        r"%Error-PINNOTFOUND:\s+([^:]+):\d+:\d+:",
        # Treat type expectation errors on system functions (e.g., $onehot0) as syntax-like so we can bail out fast
        r"%Error:\s+([^:]+\.s?v[h]?):\d+:\d+:\s*Expected\s+numeric\s+type",
    ]
    for pat in patterns:
        for m in re.finditer(pat, log_text):
            error_files.add(m.group(1))
    return list(error_files)


def _parse_all_error_files(log_text: str) -> List[str]:
    """
    Parse ANY file mentioned in %Error lines from Verilator output.
    This is a catch-all parser for iterative error fixing.
    Returns files with .v, .sv, .vh, .svh extensions mentioned in error messages.
    """
    error_files = set()
    # Match any %Error line with a file path (file:line:col: message pattern)
    # This catches syntax errors, undefined symbols, missing defines, etc.
    pattern = r"%Error[^:]*:\s+([^:]+\.(?:sv|v|svh|vh)):\d+"
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        error_files.add(m.group(1))
    return list(error_files)


def _parse_missing_include_files(log_text: str) -> List[str]:
    """
    Parse files that try to include missing or excluded files.
    When a file tries to include a file that doesn't exist or was already excluded,
    we should exclude the file that's trying to include it.
    
    Example: %Error: file.sv:10:5: Cannot find include file: 'missing.vh'
    We want to exclude 'file.sv'
    """
    problematic_files = set()
    
    # Pattern: %Error: file.sv:line:col: Cannot find include file: 'missing.vh'
    pattern = r"%Error:\s+([^:]+\.(?:sv|v|svh|vh)):\d+:\d+:\s+Cannot find include file:"
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        problematic_files.add(m.group(1))
    
    return list(problematic_files)


def _parse_missing_module_files(log_text: str) -> List[str]:
    """
    Parse files that try to instantiate modules that cannot be found.
    When a file tries to instantiate a module that Verilator can't find,
    we should exclude the file that's trying to instantiate it.
    
    Example: %Error: bsg_two_fifo.sv:56:4: Cannot find file containing module: 'bsg_mem_1r1w'
    We want to exclude 'bsg_two_fifo.sv'
    """
    problematic_files = set()
    
    # Pattern: %Error: file.sv:line:col: Cannot find file containing module: 'module_name'
    pattern = r"%Error:\s+([^:]+\.(?:sv|v|svh|vh)):\d+:\d+:\s+Cannot find file containing module:"
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        problematic_files.add(m.group(1))
    
    return list(problematic_files)


def _parse_parameter_mismatch_files(log_text: str) -> List[str]:
    """
    Parse files involved in parameter mismatch errors (PINNOTFOUND).
    These are typically external utility modules being instantiated with wrong parameters.
    We want to exclude BOTH the problematic utility file AND the parent file that calls it.
    """
    problematic_files = set()
    
    # Pattern 1: The utility file with the parameter error
    # %Error-PINNOTFOUND: external/basejump_stl/bsg_misc/bsg_dff_reset_en_bypass.sv:26:7: Parameter not found
    pattern1 = r"%Error-PINNOTFOUND:\s+([^:]+\.(?:sv|v|svh|vh)):\d+:\d+:"
    for m in re.finditer(pattern1, log_text, flags=re.IGNORECASE):
        problematic_files.add(m.group(1))
    
    # Pattern 2: Parent file that includes the problematic file
    # "... note: In file included from 'bp_fe_top.sv'"
    pattern2 = r"\.\.\.\s+note:\s+In file included from '([^']+)'"
    for m in re.finditer(pattern2, log_text, flags=re.IGNORECASE):
        parent_file = m.group(1)
        # Only add if it looks like a source file
        if parent_file.endswith(('.sv', '.v', '.svh', '.vh')):
            problematic_files.add(parent_file)
    
    return list(problematic_files)


def _parse_undefined_package_files(log_text: str) -> List[str]:
    """
    Parse files trying to import packages that don't exist (PKGNODECL).
    Example: %Error-PKGNODECL: file.v:6:10: Package/class 'bsg_fsb_packet' not found
    We want to exclude the file trying to import the missing package.
    """
    problematic_files = set()
    
    # Pattern: %Error-PKGNODECL: file.sv:line:col: Package/class 'name' not found
    # Note: May have no space or single space after colon
    pattern = r"%Error-PKGNODECL:\s*([^:]+\.(?:sv|v|svh|vh)):\d+:\d+:"
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        problematic_files.add(m.group(1))
    
    return list(problematic_files)


def _parse_undefined_macro_files(log_text: str) -> List[str]:
    """
    Parse files using undefined macros/defines.
    Example: %Error: file.v:31:36: Define or directive not defined: '`TILE_MAX_X'
    We want to exclude files that use undefined macros.
    """
    problematic_files = set()
    
    # Pattern: %Error: file.v:line:col: Define or directive not defined
    # Note: May have no space or single space after colon
    pattern = r"%Error:\s*([^:]+\.(?:sv|v|svh|vh)):\d+:\d+:\s+Define or directive not defined"
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        problematic_files.add(m.group(1))
    
    return list(problematic_files)


def _parse_parent_files_from_errors(log_text: str) -> List[str]:
    """
    Parse parent files that include/instantiate problematic modules.
    When a file has a parameter mismatch or missing port, the file that instantiates
    it is often the real problem. Verilator shows: "... note: In file included from 'parent.sv'"
    
    This parser extracts those parent files so we can exclude them instead of the utility module.
    
    NOTE: Verilator sometimes reports just the basename in quotes (e.g., 'file.sv') instead of
    the full path. In such cases, we also extract the full path from the first part of the message.
    """
    parent_files = set()
    
    # Pattern: Match filepath right before line:col, avoiding capturing error message context
    # Format: "    path/to/file.sv:69:1: ... note: In file included from 'file.sv'"
    # Use \s+ to skip leading whitespace, then ([^\s:]+) to capture the filepath
    pattern = r"\s+([^\s:]+\.(?:sv|v|svh|vh)):\d+:\d+:\s+\.\.\.\s+note:\s+In file included from '([^']+)'"
    for m in re.finditer(pattern, log_text, flags=re.IGNORECASE):
        full_path = m.group(1)  # The full path before the line number
        parent_file = m.group(2)  # The filename in quotes
        
        # Add both the quoted filename and the full path to handle both cases
        parent_files.add(parent_file)
        parent_files.add(full_path)
    
    return list(parent_files)


def _parse_missing_packages(log_text: str) -> List[str]:
    """Parse Verilator output for missing package/import errors."""
    missing = set()
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
            name = m.group(1).strip()
            if name:
                # keep raw name; callers may normalize _pkg
                missing.add(name)
    return list(missing)


def _find_sv_package_files(repo_root: str, package_names: List[str]) -> List[str]:
    """Search repo for SystemVerilog package definition files for given package names."""
    result: List[str] = []
    targets = set()
    for n in package_names:
        if not n:
            continue
        # Accept both name and name_pkg
        targets.add(n)
        if not n.endswith("_pkg"):
            targets.add(f"{n}_pkg")
    pkg_decl_re = re.compile(r"^\s*package\s+(\w+)\s*;", re.IGNORECASE | re.MULTILINE)
    for root, _dirs, files in os.walk(repo_root):
        for fname in files:
            if not fname.lower().endswith((".sv", ".svh")):
                continue
            full = os.path.join(root, fname)
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for m in pkg_decl_re.finditer(content):
                    pkg = m.group(1)
                    if pkg in targets:
                        rel = os.path.relpath(full, repo_root)
                        result.append(rel)
                        break
            except Exception:
                continue
    # Heuristic fallback: if we didn't find explicit package declarations, try filename-based candidates
    if not result:
        name_variants: Set[str] = set()
        for n in targets:
            name_variants.add(f"{n}.sv")
            name_variants.add(f"{n}.svh")
            # Common naming patterns for type packages
            name_variants.add(f"{n}Types.sv")
            name_variants.add(f"{n}_types.sv")
            name_variants.add(f"{n}Pkg.sv")
            name_variants.add(f"{n}_pkg.sv")
        for root, _dirs, files in os.walk(repo_root):
            for fname in files:
                if fname in name_variants:
                    full = os.path.join(root, fname)
                    rel = os.path.relpath(full, repo_root)
                    result.append(rel)
    # Deduplicate while preserving order
    seen: Set[str] = set()
    deduped: List[str] = []
    for r in result:
        if r not in seen:
            seen.add(r)
            deduped.append(r)
    return deduped


def _find_missing_interface_files(repo_root: str, interface_names: List[str]) -> List[str]:
    """Search repo for files that declare the given SystemVerilog interfaces.

    Returns relative file paths containing a line like: interface <name>
    """
    results: List[str] = []
    # Build regexes for each interface name, anchored at start ignoring leading whitespace
    regexes = [re.compile(rf"^\s*interface\s+{re.escape(n)}\b", re.IGNORECASE | re.MULTILINE) for n in interface_names]
    for root, _dirs, files in os.walk(repo_root):
        for fname in files:
            if not fname.lower().endswith(('.sv', '.svh')):
                continue
            full = os.path.join(root, fname)
            try:
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                for rx in regexes:
                    if rx.search(content):
                        rel = os.path.relpath(full, repo_root)
                        results.append(rel)
                        break
            except Exception:
                continue
    return results


def _add_include_dirs_from_missing(repo_root: str, include_dirs: Set[str], missing_basenames: List[str]) -> List[str]:
    added: List[str] = []
    for root, _dirs, files in os.walk(repo_root):
        for name in files:
            if name in missing_basenames:
                rel_dir = os.path.relpath(root, repo_root)
                if rel_dir not in include_dirs:
                    include_dirs.add(rel_dir)
                    added.append(rel_dir)
    return added


def _files_importing_packages(repo_root: str, files: List[str], package_names: List[str]) -> List[str]:
    """Return files from the list that import or reference the given SV packages.

    We detect either explicit imports (import <pkg>::*;) or direct package-qualified
    references (<pkg>::type/id), since some code relies on qualified names without an
    import statement.
    """
    results: List[str] = []
    if not package_names:
        return results
    # Precompile a small set of regexes per package
    regexes = []
    for pkg in package_names:
        if not pkg:
            continue
        # import <pkg>::*; or import <pkg>::something;
        regexes.append(re.compile(rf"\bimport\s+{re.escape(pkg)}\s*::", re.IGNORECASE))
        # qualified usage <pkg>::symbol
        regexes.append(re.compile(rf"\b{re.escape(pkg)}\s*::", re.IGNORECASE))
    for rel in files:
        if not rel.lower().endswith((".sv", ".svh", ".v")):
            continue
        full = os.path.join(repo_root, rel)
        try:
            with open(full, 'r', encoding='utf-8', errors='ignore') as fh:
                # Read a chunk; package refs are typically near the top
                content = fh.read(200000)
            for rx in regexes:
                if rx.search(content):
                    results.append(rel)
                    break
        except Exception:
            continue
    return results


def _minimize_include_dirs(
        repo_root: str,
        files_local: List[str],
        include_dirs_local: Set[str],
        top_module_local: str | None,
        language_version_local: str,
        timeout_local: int = 300,
        extra_flags_local: List[str] | None = None,
    ) -> Tuple[Set[str], str]:
        print_green(f"[VERILATOR] Include-dir minimization start | initial dirs={len(include_dirs_local)}")
        keep_dirs: List[str] = sorted(include_dirs_local)
        last_local_log = ""
        changed = True
        while changed:
            changed = False
            for d in list(keep_dirs):
                trial_dirs = [x for x in keep_dirs if x != d]
                cmd = _build_verilator_cmd(files_local, set(trial_dirs), top_module_local, language_version_local, extra_flags_local, repo_root)
                print_blue(f"[VERILATOR] Try remove include dir: {d}")
                rc_t, out_t = _run(cmd, cwd=repo_root, timeout=timeout_local)
                last_local_log = out_t
                if rc_t == 0:
                    keep_dirs = trial_dirs
                    print_yellow(f"[VERILATOR] Include dir removal accepted: {d}")
                    changed = True
        print_green(f"[VERILATOR] Include-dir minimization done | kept={len(keep_dirs)}")
        return set(keep_dirs), last_local_log


def compile_with_iterative_error_fixing(
    repo_root: str,
    files: List[str],
    include_dirs: Set[str],
    top_module: str | None,
    language_version: str,
    timeout: int = 300,
    extra_flags: List[str] | None = None,
    max_fix_iterations: int = 5,
    excluded_files_blacklist: Set[str] | None = None,
) -> Tuple[int, str, List[str], Set[str]]:
    """
    Iteratively compile with error fixing by progressively excluding problematic files.
    Parses Verilator errors and excludes files that cause issues, then retries.
    This is more aggressive than compile_with_dependency_resolution and will exclude
    any file causing errors, not just obvious wrapper/testbench files.
    
    Returns: (rc, log, files, include_dirs)
    """
    print_green(f"[VERILATOR-FIX] Starting iterative error fixing | top={top_module} max_iterations={max_fix_iterations}")
    
    excluded = set(excluded_files_blacklist or [])
    current_files = [f for f in files if f not in excluded]
    current_includes = set(include_dirs)
    last_log = ""
    last_error_count = float('inf')
    
    for iteration in range(max_fix_iterations):
        print_yellow(f"[VERILATOR-FIX] Iteration {iteration + 1}/{max_fix_iterations} | files={len(current_files)}")
        print_yellow(f"[VERILATOR-FIX] DEBUG: Starting iteration with {len(excluded)} files in blacklist")
        
        # Try normal dependency resolution with minimal retries (we'll handle retries at this level)
        rc, out, fixed_files, fixed_incl = compile_with_dependency_resolution(
            repo_root,
            current_files,
            current_includes,
            top_module,
            language_version,
            timeout=timeout,
            extra_flags=extra_flags,
            max_retries=1,  # Keep retries minimal, we handle iteration here
            excluded_files_blacklist=excluded,
        )
        
        last_log = out
        
        if rc == 0:
            print_green(f"[VERILATOR-FIX] ✓ Success after {iteration + 1} iteration(s) | files={len(fixed_files)}")
            return rc, out, fixed_files, fixed_incl
        
        # Parse all error types from Verilator log
        syntax_error_files = _parse_syntax_error_files(out)
        duplicate_files = _parse_duplicate_declarations(out)
        all_error_files = _parse_all_error_files(out)  # Catch-all for any %Error with file
        parent_files = _parse_parent_files_from_errors(out)  # Files that include problematic modules
        param_mismatch_files = _parse_parameter_mismatch_files(out)  # PINNOTFOUND errors
        missing_include_files = _parse_missing_include_files(out)  # Files with missing includes
        missing_module_files = _parse_missing_module_files(out)  # Cannot find module errors
        undefined_package_files = _parse_undefined_package_files(out)  # PKGNODECL errors
        undefined_macro_files = _parse_undefined_macro_files(out)  # Undefined macro/define errors
        
        # Count total errors to track progress
        _, error_count = _summarize_verilator_log(out)
        print_yellow(f"[VERILATOR-FIX] Errors: {error_count}")
        
        # Collect all problematic files (union of all parsers)
        problematic_files = set()
        problematic_files.update(syntax_error_files)
        problematic_files.update(duplicate_files)
        problematic_files.update(all_error_files)
        problematic_files.update(parent_files)
        problematic_files.update(param_mismatch_files)
        problematic_files.update(missing_include_files)
        problematic_files.update(missing_module_files)
        problematic_files.update(undefined_package_files)
        problematic_files.update(undefined_macro_files)
        
        if not problematic_files:
            print_red(f"[VERILATOR-FIX] No error files identified")
            return rc, last_log, fixed_files, fixed_incl
        
        # Convert to relative paths and filter
        files_to_exclude = set()
        skipped_already_excluded = 0
        skipped_not_found = 0
        
        for bad_file in problematic_files:
            # Normalize path for consistent comparison
            rel = _normalize_path(bad_file, repo_root)
            
            # Skip if already excluded
            if rel in excluded:
                skipped_already_excluded += 1
                continue
            
            # Check if file exists in repo (some error messages might have relative paths)
            file_exists = os.path.isfile(os.path.join(repo_root, rel))
            if not file_exists:
                skipped_not_found += 1
                continue
            
            # Prioritize excluding certain types of files first
            path_lower = rel.lower().replace("\\", "/")
            priority = 0
            
            # Priority 8: Files with undefined macros - likely missing configuration
            # These require external defines that we can't provide
            if bad_file in undefined_macro_files:
                priority = 8
            # Priority 7: Files trying to import missing packages (PKGNODECL)
            # These depend on packages that don't exist or weren't compiled
            elif bad_file in undefined_package_files:
                priority = 7
            # Priority 6: Files trying to include missing/excluded files OR instantiate missing modules
            # These cause cascading errors and should be excluded immediately
            elif bad_file in missing_include_files or bad_file in missing_module_files:
                priority = 6
            # Priority 5: Files with parameter mismatch errors (PINNOTFOUND)
            # These are broken external utilities or parent files calling them wrong
            elif bad_file in param_mismatch_files:
                priority = 5
            # Priority 4: parent files that instantiate modules with wrong parameters
            # These are often core files with bugs that we should exclude
            elif bad_file in parent_files:
                priority = 4
            # Priority 3: external/vendor/legacy code (most likely to have issues)
            elif any(x in path_lower for x in ["/external/", "/legacy/", "/vendor/", "/third_party/", "/3rdparty/"]):
                priority = 3
            # Priority 2: testbenches and non-synthesizable code
            elif any(x in path_lower for x in ["_tb", "tb_", "test", "nonsynth", "wrapper"]):
                priority = 2
            # Priority 1: duplicate declarations (likely utility/compatibility files)
            elif bad_file in duplicate_files:
                priority = 1
            # Priority 0: syntax errors in any file
            else:
                priority = 0
            
            files_to_exclude.add((priority, rel))
        
        if not files_to_exclude:
            print_red(f"[VERILATOR-FIX] All error files already excluded or not in file list")
            return rc, last_log, fixed_files, fixed_incl
        
        # Sort by priority (highest first) and take up to 10 files per iteration
        # Prioritize external/legacy files to quickly eliminate problematic dependencies
        sorted_excludes = sorted(files_to_exclude, key=lambda x: (-x[0], x[1]))
        files_to_exclude_this_round = [rel for _, rel in sorted_excludes[:10]]
        
        # Exclude the problematic files
        for rel in files_to_exclude_this_round:
            excluded.add(rel)
            if excluded_files_blacklist is not None:
                excluded_files_blacklist.add(rel)
            priority = next(p for p, r in files_to_exclude if r == rel)
            
            # Determine the specific priority label based on which parser caught it
            if priority == 8:
                priority_label = "undefined-macro"
            elif priority == 7:
                priority_label = "missing-package"
            elif priority == 6:
                # Both missing include and missing module have priority 6
                if rel in missing_include_files:
                    priority_label = "missing-include"
                elif rel in missing_module_files:
                    priority_label = "missing-module"
                else:
                    priority_label = "missing-dependency"
            elif priority == 5:
                priority_label = "param-mismatch"
            elif priority == 4:
                priority_label = "parent-instantiation"
            elif priority == 3:
                priority_label = "external"
            elif priority == 2:
                priority_label = "test/wrapper"
            elif priority == 1:
                priority_label = "duplicate"
            else:
                priority_label = "syntax"
                
            print_yellow(f"[VERILATOR-FIX] Excluding [{priority_label}]: {rel}")
        
        current_files = [f for f in fixed_files if f not in excluded]
        current_includes = fixed_incl
        
        # Check if we're making progress
        if error_count >= last_error_count:
            print_yellow(f"[VERILATOR-FIX] Warning: Error count not decreasing (was {last_error_count}, now {error_count})")
        
        last_error_count = error_count
        print_yellow(f"[VERILATOR-FIX] Excluded {len(files_to_exclude_this_round)} file(s), {len(current_files)} files remaining")
        print_yellow(f"[VERILATOR-FIX] DEBUG: Total files in blacklist: {len(excluded)}")
        
        # Sample what's in the blacklist
        if len(excluded) > 0:
            sample = list(excluded)[:5]
            print_yellow(f"[VERILATOR-FIX] DEBUG: Sample blacklist: {sample}")
    
    print_red(f"[VERILATOR-FIX] Failed to achieve clean build after {max_fix_iterations} iterations")
    return rc, last_log, current_files, current_includes


def compile_with_dependency_resolution(
    repo_root: str,
    files: List[str],
    include_dirs: Set[str],
    top_module: str | None,
    language_version: str,
    timeout: int = 300,
    extra_flags: List[str] | None = None,
    max_retries: int = 2,
    excluded_files_blacklist: Set[str] | None = None,
) -> Tuple[int, str, List[str], Set[str]]:
    """
    Run lint with retries while adding missing include dirs and module files.
    Returns: (rc, log, files, include_dirs)
    """
    excluded = set(excluded_files_blacklist or [])
    # Defensive defaults for variables that may be assigned inside retry loop
    # but referenced later if an early path skips assignments
    missing_includes: List[str] = []
    missing_include_pairs: List[Tuple[str, str]] = []
    missing_modules: List[str] = []
    missing_packages: List[str] = []
    missing_interfaces: List[str] = []
    duplicate_files: List[str] = []
    syntax_error_files: Set[str] = set()
    broken_include_sources: Set[str] = set()
    # Drop wrapper-ish files early (generic heuristics)
    current_files = [f for f in files if f not in excluded and not _is_wrapperish_source(f, repo_root)]
    # Keep include dirs ordered but unique. Prioritize dirs that likely contain packages.
    def _pkg_dir_priority(d: str) -> int:
        dl = d.lower()
        if dl.endswith("/rtl") or dl.endswith("/sv"):
            return 0
        if "/pkg" in dl or dl.endswith("/pkg"):
            return 0
        return 1

    current_includes = set(include_dirs)

    # Proactively dedupe the initial file set to avoid early duplicate symbol errors
    try:
        before_len = len(current_files)
        current_files = _dedupe_files_generically(current_files, repo_root)
        if len(current_files) != before_len:
            print_green(f"[VERILATOR] Initial dedupe reduced files: {before_len} -> {len(current_files)}")
    except Exception:
        pass

    print_green(f"[VERILATOR] Dependency resolution start | files={len(current_files)} includes={len(current_includes)} top={top_module} lang={language_version}")
    # Proactively add include dirs that contain common headers referenced by `include
    try:
        inc_basenames = _collect_included_basenames(repo_root, current_files)
        if inc_basenames:
            added0 = _add_include_dirs_from_missing(repo_root, current_includes, inc_basenames)
            if added0:
                print_green(f"[VERILATOR] Pre-added include dirs from scanned includes: {_fmt_list(sorted(added0))}")
    except Exception:
        pass
    for _attempt in range(max_retries + 1):
        # Sort includes so package-y dirs appear early on the command line.
        sorted_includes = sorted(current_includes, key=_pkg_dir_priority)
        cmd = _build_verilator_cmd(current_files, set(sorted_includes), top_module, language_version, extra_flags, repo_root)
        # Emit a parsable effective language hint for downstream config writers
        mode, std = _effective_language(current_files, language_version)
        print_blue(f"[LANG-EFFECTIVE] {std} mode={mode}")
        print_blue(f"[VERILATOR] Attempt {_attempt+1}/{max_retries+1}")
        print_blue(f"[VERILATOR] Files ({len(current_files)}): {_fmt_list(sorted(current_files))}")
        if current_includes:
            print_blue(f"[VERILATOR] Include dirs ({len(current_includes)}): {_fmt_list(sorted(current_includes))}")
        try:
            print_blue(f"[VERILATOR] CMD: {' '.join(shlex.quote(x) for x in cmd)}")
        except Exception:
            pass
        rc, out = _run(cmd, cwd=repo_root, timeout=timeout)
        
        # Check for SystemVerilog keyword conflicts on first attempt
        # If detected and we're using SystemVerilog mode, retry with plain Verilog
        if _attempt == 0 and rc != 0:
            if _detect_systemverilog_keyword_conflict(out):
                mode, std = _effective_language(current_files, language_version)
                if mode == 'sv':
                    print_yellow("[VERILATOR] SystemVerilog keyword conflict detected, retrying with Verilog mode")
                    # Override language to Verilog 2005
                    language_version = "1364-2005"
                    # Rebuild command with Verilog mode
                    cmd = _build_verilator_cmd(current_files, set(sorted_includes), top_module, language_version, extra_flags, repo_root)
                    print_blue(f"[VERILATOR] Retrying with Verilog mode: {' '.join(shlex.quote(x) for x in cmd)}")
                    rc, out = _run(cmd, cwd=repo_root, timeout=timeout)
        
        if (rc == 0):
            w, e = _summarize_verilator_log(out)
            print_green(f"[VERILATOR] Lint clean | files={len(current_files)} includes={len(current_includes)}")
            print_green(f"[VERILATOR REPORT] errors={e} warnings={w}")
            return rc, out, current_files, current_includes
    # Output already streamed live; avoid duplicate dumps

        # Parse and try to fix
        missing_includes = _parse_missing_includes(out)
        missing_include_pairs = _parse_missing_include_pairs(out)
        missing_modules = _parse_missing_modules(out)
        missing_packages = _parse_missing_packages(out)
        missing_interfaces = _parse_missing_interfaces(out)
        duplicate_files = _parse_duplicate_declarations(out)
        syntax_error_files = _parse_syntax_error_files(out)

        changed = False

        # EARLY DROP: if we detected syntax-error files, exclude them immediately and retry.
        # This avoids burning multiple attempts before we finally drop known-bad sources.
        if syntax_error_files:
            any_excluded = False
            for bad in list(syntax_error_files):
                rel = os.path.relpath(bad, repo_root) if os.path.isabs(bad) else bad
                base = os.path.basename(rel).lower()
                # Avoid excluding likely package files; they may fail due to unresolved imports
                if "_pkg" in base:
                    continue
                if _is_wrapperish_source(rel, repo_root):
                    reason = "wrapper"
                else:
                    reason = "syntax"
                if rel in current_files:
                    excluded.add(rel)
                    if excluded_files_blacklist is not None:
                        excluded_files_blacklist.add(rel)
                    current_files = [f for f in current_files if f != rel]
                    print_yellow(f"[VERILATOR] Early exclude due to {reason}: {rel}")
                    any_excluded = True
            if any_excluded:
                # Immediately try again with the offending files removed
                continue

        # Add include dirs for missing includes (do this before excluding anything)
        if missing_includes:
            added = _add_include_dirs_from_missing(
                repo_root, current_includes, [os.path.basename(x) for x in missing_includes]
            )
            if added:
                print_green(f"[VERILATOR] Added include dirs: {_fmt_list(sorted(added))}")
                changed = True

        # Identify sources with includes we cannot satisfy
        broken_include_sources: Set[str] = set()
        # Case 1: Unresolvable relative include paths (e.g., '../../rtl/config.vh' not present)
        for src, inc in missing_include_pairs:
            if "/" in inc or "\\" in inc:
                # Resolve relative to the including file's directory
                try:
                    src_rel = os.path.relpath(src, repo_root) if os.path.isabs(src) else src
                except Exception:
                    src_rel = src
                src_dir = os.path.dirname(src_rel)
                candidate = os.path.normpath(os.path.join(src_dir, inc))
                candidate_abs = os.path.join(repo_root, candidate)
                if not os.path.isfile(candidate_abs):
                    broken_include_sources.add(src_rel)
        # Case 2: Plain include names that don't exist anywhere in the repo after include-dir search
        try:
            repo_files_set: Set[str] = set()
            for r, _d, fns in os.walk(repo_root):
                for fn in fns:
                    repo_files_set.add(fn)
        except Exception:
            repo_files_set = set()
        unresolved_plain_includes: Set[str] = set()
        for inc in missing_includes:
            if ("/" not in inc and "\\" not in inc) and inc not in repo_files_set:
                unresolved_plain_includes.add(inc)
        if unresolved_plain_includes:
            # Exclude importers of these unresolved headers
            for src, inc in missing_include_pairs:
                if inc in unresolved_plain_includes:
                    try:
                        src_rel = os.path.relpath(src, repo_root) if os.path.isabs(src) else src
                    except Exception:
                        src_rel = src
                    broken_include_sources.add(src_rel)
        # We'll exclude these later with other syntax/duplicate offenders

        # Add package files if packages are missing
        if missing_packages:
            pkg_files = _find_sv_package_files(repo_root, missing_packages)
            for p in pkg_files:
                # Normalize path for consistent exclusion checking
                p_rel = _normalize_path(p, repo_root)
                
                # Check if this file is in the blacklist (excluded due to errors)
                if p_rel in excluded:
                    print_yellow(f"[VERILATOR] Skipping blacklisted package file: {p_rel}")
                    continue
                
                if p_rel not in current_files:
                    current_files.append(p_rel)
                    print_green(f"[VERILATOR] Added package file: {p_rel}")
                    changed = True
                # Also add their directories as -I to help header lookup within package dirs
                try:
                    pkg_dir = os.path.dirname(p)
                    if pkg_dir and pkg_dir not in current_includes:
                        current_includes.add(pkg_dir)
                        print_green(f"[VERILATOR] Added include dir from package dir: {pkg_dir}")
                        changed = True
                except Exception:
                    pass

            # If we still have unresolved packages (no providers found), exclude importers of those
            unresolved = [pkg for pkg in missing_packages if not any(os.path.basename(x).lower().startswith(pkg.lower()) or f"{pkg.lower()}_pkg" in os.path.basename(x).lower() for x in pkg_files)]
            if unresolved:
                importers = _files_importing_packages(repo_root, current_files, unresolved)
                for rel in importers:
                    # Avoid excluding likely package files themselves
                    base = os.path.basename(rel).lower()
                    if "_pkg" in base:
                        continue
                    if rel in current_files:
                        excluded.add(rel)
                        if excluded_files_blacklist is not None:
                            excluded_files_blacklist.add(rel)
                        current_files = [f for f in current_files if f != rel]
                        print_yellow(f"[VERILATOR] Excluding importer of unresolved package(s): {rel}")
                        changed = True
            # Regardless of explicit resolution, move likely provider files to the front to ensure packages compile first
            try:
                pkg_names_lc = {p.lower() for p in missing_packages}
                def _is_candidate_provider(rel: str) -> bool:
                    b = os.path.basename(rel).lower()
                    # Direct name match or typical variants
                    if b.endswith('.sv') or b.endswith('.svh'):
                        stem = b.rsplit('.', 1)[0]
                        if stem in pkg_names_lc:
                            return True
                        if stem.endswith('_pkg') and stem[:-4] in pkg_names_lc:
                            return True
                        if stem.endswith('types') and stem[:-5] in pkg_names_lc:
                            return True
                    return False
                if any(_is_candidate_provider(f) for f in current_files):
                    before = list(current_files)
                    providers = [f for f in current_files if _is_candidate_provider(f)]
                    others = [f for f in current_files if not _is_candidate_provider(f)]
                    current_files = providers + others
                    if before != current_files:
                        print_green(f"[VERILATOR] Reordered to place package providers first: {_fmt_list([os.path.basename(x) for x in providers], 10)}")
                        changed = True
            except Exception:
                pass

        # Add interface declaration files for missing interfaces
        if missing_interfaces:
            if_files = _find_missing_interface_files(repo_root, missing_interfaces)
            for p in if_files:
                # Normalize path for consistent exclusion checking
                p_rel = _normalize_path(p, repo_root)
                
                if p_rel not in excluded and p_rel not in current_files:
                    current_files.append(p_rel)
                    print_green(f"[VERILATOR] Added interface file: {p_rel}")
                    changed = True
                elif p_rel in excluded:
                    print_yellow(f"[VERILATOR] Skipping blacklisted interface file: {p_rel}")
            # Add their directories as -I too
            for p in if_files:
                d = os.path.dirname(p)
                if d and d not in current_includes:
                    current_includes.add(d)
                    print_green(f"[VERILATOR] Added include dir from interface dir: {d}")
                    changed = True

        # Add files that likely contain the missing modules
        if missing_modules:
            # Do not satisfy missing modules using sim/project wrappers (e.g., VivadoSim/Main.sv)
            module_paths = []
            unresolvable_modules = []  # Track modules we can't find or are blacklisted
            blacklisted_modules = set()  # Track modules that are in the blacklist
            
            for p in find_missing_module_files(repo_root, missing_modules):
                # Normalize path for consistent exclusion checking
                p_rel = _normalize_path(p, repo_root)
                
                # Skip adding wrapper-ish modules (e.g., Main, tb_*) to avoid steering toward benches
                if _is_wrapperish_source(p_rel, repo_root):
                    continue
                # Skip by module-name semantics when possible
                base_mod = os.path.splitext(os.path.basename(p_rel))[0]
                if _is_wrapperish_module_name(base_mod):
                    continue
                # Skip if blacklisted - track these as they cause dependencies to be unresolvable
                if p_rel in excluded:
                    blacklisted_modules.add(base_mod)
                    print_yellow(f"[VERILATOR] Module '{base_mod}' is blacklisted - files using it will be excluded")
                    continue
                module_paths.append(p_rel)
            
            # Identify which modules we couldn't find files for (either don't exist or are blacklisted)
            found_module_names = {os.path.splitext(os.path.basename(p))[0] for p in module_paths}
            for mod_name in missing_modules:
                if mod_name not in found_module_names:
                    unresolvable_modules.append(mod_name)
            
            # DON'T add back any module files if they have unresolvable dependencies
            # Check all module_paths to see if they use unresolvable modules
            if unresolvable_modules or blacklisted_modules:
                unavailable = set(unresolvable_modules) | blacklisted_modules
                if unavailable:
                    print_yellow(f"[VERILATOR] Unavailable modules (missing or blacklisted): {_fmt_list(sorted(unavailable), 5)}")
                    print_yellow(f"[VERILATOR] Files using these modules will NOT be added back")
            
            for p in module_paths:
                if p not in excluded and p not in current_files:
                    current_files.append(p)
                    print_green(f"[VERILATOR] Added module file for missing module: {p}")
                    changed = True
            # Also add their directories as -I to help header lookup
            extra_dirs = [d for d in find_missing_modules(repo_root, missing_modules) if not _is_wrapperish_source(d, repo_root)]
            for d in extra_dirs:
                if d not in current_includes:
                    current_includes.add(d)
                    print_green(f"[VERILATOR] Added include dir from missing module: {d}")
                    changed = True

    # Exclude syntax-error files and importers with broken includes (last), but handle
    # duplicates by preferring best path per basename rather than excluding arbitrarily.
    safe_excluded = False
    # Also exclude wrappers when they show up as sources of errors (e.g., VivadoSim/Main.sv)
    for bad in list(syntax_error_files) + list(broken_include_sources):
        rel = os.path.relpath(bad, repo_root) if os.path.isabs(bad) else bad
        # Avoid excluding packages; they may have failed due to prior missing includes
        base = os.path.basename(rel).lower()
        if "_pkg" in base:
            continue
        if _is_wrapperish_source(rel, repo_root):
            reason = "wrapper"
        else:
            reason = "duplicate/syntax"
        if rel in current_files:
            excluded.add(rel)
            if excluded_files_blacklist is not None:
                excluded_files_blacklist.add(rel)
            current_files = [f for f in current_files if f != rel]
            print_yellow(f"[VERILATOR] Excluding file due to {reason}: {rel}")
            changed = True
            safe_excluded = True

        # Handle duplicate declarations by consolidating on best-scored file per basename
        if duplicate_files:
            base_to_paths: Dict[str, List[str]] = {}
            for f in current_files:
                base_to_paths.setdefault(os.path.basename(f), []).append(f)
            for base, paths in base_to_paths.items():
                if len(paths) <= 1:
                    continue
                best = sorted(paths, key=lambda p: (_path_score_generic(p), len(p)), reverse=True)[0]
                for pth in paths:
                    if pth != best and pth in current_files:
                        excluded.add(pth)
                        if excluded_files_blacklist is not None:
                            excluded_files_blacklist.add(pth)
                        current_files = [f for f in current_files if f != pth]
                        print_yellow(f"[VERILATOR] Excluding duplicate by basename '{base}': {pth} (keep {best})")
                        changed = True

        # Always dedupe before deciding if nothing changed
        before_len = len(current_files)
        current_files = _dedupe_files_generically(current_files, repo_root)
        if len(current_files) != before_len:
            changed = True

        if not changed:
            # Nothing else to try
            print_red("[VERILATOR] No further automatic fixes possible")
            return rc, out, current_files, current_includes

    # Final attempt already performed, return last state
    cmd = _build_verilator_cmd(current_files, current_includes, top_module, language_version, extra_flags, repo_root)
    rc, out = _run(cmd, cwd=repo_root, timeout=timeout)
    return rc, out, current_files, current_includes


def minimize_files(
    repo_root: str,
    files: List[str],
    include_dirs: Set[str],
    tb_files: List[str],
    top_module: str | None,
    language_version: str,
    timeout: int = 300,
    extra_flags: List[str] | None = None,
    excluded_files_blacklist: Set[str] | None = None,
) -> Tuple[List[str], Set[str], str]:
    """
    Remove non-testbench files one-by-one and keep removal if lint is still clean.
    Returns: (final_files, include_dirs, last_log)
    """
    excluded = set(excluded_files_blacklist or [])
    keep_files = [f for f in files if f not in excluded]
    tb_set = set(tb_files)

    # Helper: detect if file declares a package or an interface (avoid removing foundational defs)
    def _declares_pkg_or_interface(rel_path: str) -> bool:
        try:
            full = os.path.join(repo_root, rel_path)
            with open(full, 'r', encoding='utf-8', errors='ignore') as fh:
                head = fh.read(8000)  # read first chunk; decls are typically near the top
            if re.search(r"^\s*package\s+\w+\s*;", head, flags=re.IGNORECASE | re.MULTILINE):
                return True
            if re.search(r"^\s*interface\s+\w+\b", head, flags=re.IGNORECASE | re.MULTILINE):
                return True
        except Exception:
            return False
        return False

    # Candidates are non-testbench files and not package/interface providers
    candidates = [f for f in keep_files if f not in tb_set and not _declares_pkg_or_interface(f)]

    print_green(f"[VERILATOR] Minimization start | initial files={len(keep_files)} (tb={len(tb_set)})")
    last_log = ""
    for f in list(candidates):
        trial = [x for x in keep_files if x != f]
        cmd = _build_verilator_cmd(trial, include_dirs, top_module, language_version, extra_flags, repo_root)
        print_blue(f"[VERILATOR] Try remove: {f}")
        rc, out = _run(cmd, cwd=repo_root, timeout=timeout)
        last_log = out
        if rc == 0:
            keep_files = trial  # removal successful
            print_yellow(f"[VERILATOR] Removal accepted: {f}")

    print_green(f"[VERILATOR] Minimization done | kept={len(keep_files)}")
    return keep_files, include_dirs, last_log


def auto_orchestrate(
    repo_root: str,
    repo_name: str,
    tb_files: List[str],
    candidate_files: List[str],
    include_dirs: Set[str] | None,
    top_candidates: List[str],
    language_version: str,
    timeout: int = 300,
    extra_flags: List[str] | None = None,
    max_retries: int = 2,
    excluded_files_blacklist: Set[str] | None = None,
) -> Tuple[List[str], Set[str], str, str, bool]:
    """End-to-end flow for SV/V linting: try tops, resolve deps, minimize, final checks.

    Returns (files, include_dirs, last_log, selected_top, is_simulable).
    """
    print_green(f"[VERILATOR] Orchestrate start | repo={repo_name} candidates={len(top_candidates)} files={len(candidate_files)}")

    # Limit number of candidates for large projects to avoid excessive testing
    MAX_CANDIDATES_TO_TRY = 10
    if len(top_candidates) > MAX_CANDIDATES_TO_TRY:
        print_yellow(f"[VERILATOR] Large project detected ({len(top_candidates)} candidates). Limiting to top {MAX_CANDIDATES_TO_TRY} candidates.")
        top_candidates = top_candidates[:MAX_CANDIDATES_TO_TRY]

    # Determine if this is a large project that needs iterative fixing
    is_large_project = len(candidate_files) > 200
    max_fix_iterations = 10 if is_large_project else 3
    
    if is_large_project:
        print_yellow(f"[VERILATOR] Large project detected ({len(candidate_files)} files). Using iterative error fixing with {max_fix_iterations} iterations per candidate.")

    # Filter out wrapper-ish files from initial candidates
    files = [f for f in candidate_files if not _is_wrapperish_source(f, repo_root)]
    incl: Set[str] = set(include_dirs or set())
    last_log = ""
    transcript = ""
    selected_top = ""
    got_clean = False

    # Try each top candidate with dependency resolution
    for cand in top_candidates:
        print_green(f"[VERILATOR] Trying top candidate: {cand}")
        transcript += f"[TOP-TRY] {cand}\n"
        
        # Use iterative fixing for large projects, normal resolution for small ones
        if is_large_project:
            rc, out, fixed_files, fixed_incl = compile_with_iterative_error_fixing(
                repo_root,
                files,
                incl,
                cand,
                language_version,
                timeout=timeout,
                extra_flags=extra_flags,
                max_fix_iterations=max_fix_iterations,
                excluded_files_blacklist=excluded_files_blacklist,
            )
        else:
            rc, out, fixed_files, fixed_incl = compile_with_dependency_resolution(
                repo_root,
                files,
                incl,
                cand,
                language_version,
                timeout=timeout,
                extra_flags=extra_flags,
                max_retries=max_retries,
                excluded_files_blacklist=excluded_files_blacklist,
            )
        
        # Summarize attempt and append to transcript
        w_try, e_try = _summarize_verilator_log(out)
        transcript += f"[TOP-TRY-RESULT] {cand} rc={rc} errors={e_try} warnings={w_try}\n"
        last_log = out
        if rc == 0:
            selected_top = cand
            files = fixed_files
            incl = fixed_incl
            got_clean = True
            break

    # If we never got a clean lint, return current state with failure
    if not files or not selected_top or not got_clean:
        print_red("[VERILATOR] No clean candidate; returning failure state")
        return files, incl, last_log, (selected_top or ""), False

    # Minimization pass
    files, incl, last_log = minimize_files(
        repo_root,
        files,
        incl,
        tb_files,
        selected_top,
        language_version,
        timeout=timeout,
        extra_flags=extra_flags,
        excluded_files_blacklist=excluded_files_blacklist,
    )

    # Final lint check
    print_green(f"[VERILATOR] Final lint check | files={len(files)} includes={len(incl)} top={selected_top}")
    rc_f, out_f = _run(
        _build_verilator_cmd(files, incl, selected_top, language_version, extra_flags, repo_root),
        cwd=repo_root,
        timeout=timeout,
    )
    last_log = transcript + out_f
    w, e = _summarize_verilator_log(out_f)
    print_green(f"[VERILATOR REPORT] errors={e} warnings={w}")
    is_simulable = (rc_f == 0)

    # Optional final cleanup pass (files and include dirs) only if success
    if is_simulable:
        # Snapshot working state for rollback
        working_files = list(files)
        working_incl = set(incl)

        # One more short file minimization in case include-dir changes freed up removals
        files, incl, last_log = minimize_files(
            repo_root,
            files,
            incl,
            tb_files,
            selected_top,
            language_version,
            timeout=timeout,
            extra_flags=extra_flags,
            excluded_files_blacklist=excluded_files_blacklist,
        )

        # Final include-dir minimization
        incl, last_log = _minimize_include_dirs(
            repo_root,
            files,
            incl,
            selected_top,
            language_version,
            timeout_local=timeout,
            extra_flags_local=extra_flags,
        )

        # Validate
        print_green(f"[VERILATOR] Final lint check (post-cleanup) | files={len(files)} includes={len(incl)} top={selected_top}")
        rc_fc, out_fc = _run(
            _build_verilator_cmd(files, incl, selected_top, language_version, extra_flags, repo_root),
            cwd=repo_root,
            timeout=timeout,
        )
        last_log = transcript + out_fc
        w2, e2 = _summarize_verilator_log(out_fc)
        print_green(f"[VERILATOR REPORT] errors={e2} warnings={w2}")
        if rc_fc != 0:
            print_yellow("[VERILATOR] Post-cleanup failed; reverting to last clean set")
            files = working_files
            incl = working_incl
            is_simulable = True

    return files, incl, last_log, (selected_top or ""), is_simulable
