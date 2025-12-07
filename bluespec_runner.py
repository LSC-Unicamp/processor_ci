#!/usr/bin/env python3
"""
Bluespec Runner

Standalone script to process Bluespec SystemVerilog projects.
Can be used independently or integrated with config_generator.py

Usage:
    python bluespec_runner.py -d /path/to/bluespec/project -o config/
    python bluespec_runner.py -d /path/to/bluespec/project --skip-verilog
    python bluespec_runner.py -d /path/to/bluespec/project --list-modules
"""

import argparse
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processor_ci.core.bluespec_manager import (
    find_bsv_files,
    extract_bluespec_modules,
    extract_interfaces,
    build_bluespec_dependency_graph,
    find_top_module,
    compile_to_verilog,
    process_bluespec_project
)


def list_modules(directory: str):
    """List all modules found in the project."""
    print(f"Scanning for Bluespec modules in: {directory}\n")
    
    bsv_files = find_bsv_files(directory)
    print(f"Found {len(bsv_files)} BSV files")
    
    if not bsv_files:
        print("No BSV files found!")
        return
    
    modules = extract_bluespec_modules(bsv_files)
    print(f"\nFound {len(modules)} modules:\n")
    
    for module_name, file_path in sorted(modules):
        rel_path = os.path.relpath(file_path, directory)
        print(f"  {module_name:30} -> {rel_path}")
    
    # Show interfaces
    interfaces = extract_interfaces(bsv_files)
    if interfaces:
        print(f"\nFound {len(interfaces)} interfaces:\n")
        for ifc_name, file_path in sorted(interfaces):
            rel_path = os.path.relpath(file_path, directory)
            print(f"  {ifc_name:30} -> {rel_path}")
    
    # Show dependency graph
    if modules:
        module_graph, module_graph_inverse = build_bluespec_dependency_graph(modules)
        print("\nDependency Graph:")
        print("-" * 60)
        for module_name, instantiated in sorted(module_graph.items()):
            if instantiated:
                print(f"  {module_name} instantiates:")
                for inst in sorted(instantiated):
                    print(f"    -> {inst}")


def analyze_project(directory: str, repo_name: str = None):
    """Analyze project and show top module without compiling."""
    print(f"Analyzing Bluespec project: {directory}\n")
    
    bsv_files = find_bsv_files(directory)
    print(f"Found {len(bsv_files)} BSV files")
    
    if not bsv_files:
        print("No BSV files found!")
        return None
    
    modules = extract_bluespec_modules(bsv_files)
    print(f"Found {len(modules)} modules")
    
    if not modules:
        print("No modules found!")
        return None
    
    module_graph, module_graph_inverse = build_bluespec_dependency_graph(modules)
    top_module = find_top_module(module_graph, module_graph_inverse, modules, repo_name)
    
    if top_module:
        print(f"\n{'='*60}")
        print(f"Top module identified: {top_module}")
        print(f"{'='*60}")
        
        # Show what it instantiates
        children = module_graph.get(top_module, [])
        if children:
            print(f"\n{top_module} instantiates {len(children)} modules:")
            for child in sorted(children):
                print(f"  -> {child}")
    else:
        print("\nCould not identify top module!")
    
    return top_module


def process_and_compile(directory: str, repo_name: str = None, output_dir: str = None):
    """Process project and compile to Verilog."""
    print(f"Processing Bluespec project: {directory}\n")
    
    config = process_bluespec_project(directory, repo_name)
    
    if 'error' in config:
        print(f"\nERROR: {config['error']}")
        return None
    
    print("\nConfiguration generated successfully!")
    print(json.dumps(config, indent=2))
    
    # Save config if output directory specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        config_file = os.path.join(output_dir, f"{config['name']}.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to: {config_file}")
    
    return config


def main():
    parser = argparse.ArgumentParser(
        description='Process Bluespec SystemVerilog projects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process project and generate Verilog
  %(prog)s -d /path/to/bsv/project -o config/
  
  # Analyze project without compiling
  %(prog)s -d /path/to/bsv/project --skip-verilog
  
  # List all modules
  %(prog)s -d /path/to/bsv/project --list-modules
  
  # Specify repository name for better heuristics
  %(prog)s -d /path/to/bsv/project -r my-riscv-core
        """
    )
    
    parser.add_argument(
        '-d', '--directory',
        required=True,
        help='Path to Bluespec project directory'
    )
    
    parser.add_argument(
        '-r', '--repo-name',
        help='Repository name (for heuristics, default: directory name)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory for config file (default: ./config)'
    )
    
    parser.add_argument(
        '--skip-verilog',
        action='store_true',
        help='Skip Verilog generation (analysis only)'
    )
    
    parser.add_argument(
        '--list-modules',
        action='store_true',
        help='List all modules and exit'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Compilation timeout in seconds (default: 300)'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"ERROR: Directory not found: {args.directory}")
        sys.exit(1)
    
    # Get repository name
    repo_name = args.repo_name or os.path.basename(os.path.abspath(args.directory))
    
    # Execute requested action
    if args.list_modules:
        list_modules(args.directory)
    elif args.skip_verilog:
        analyze_project(args.directory, repo_name)
    else:
        config = process_and_compile(args.directory, repo_name, args.output_dir)
        if config and config.get('is_simulable'):
            print("\n✓ Success! Project processed and Verilog generated.")
            sys.exit(0)
        else:
            print("\n✗ Failed to process project or generate Verilog.")
            sys.exit(1)


if __name__ == '__main__':
    main()
