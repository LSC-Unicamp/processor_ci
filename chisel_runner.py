#!/usr/bin/env python3
"""
Chisel Runner - OPTIONAL standalone tool for processing Chisel projects

NOTE: This is an optional convenience script. The main config_generator.py
automatically handles Chisel projects when you use the -l flag:

    python config_generator.py -u <url> -l /path/to/chisel/project -p config/

This standalone script is only needed if you want to process a Chisel project
directly without the full config_generator workflow.

This script provides a command-line interface for:
- Analyzing Chisel/Scala projects
- Extracting module definitions and dependencies
- Identifying top-level modules
- Generating Verilog output via SBT

Usage:
    python chisel_runner.py -d <directory> [-r <repo_name>] [-o <output_dir>]
    
Examples:
    # Process a local Chisel project
    python chisel_runner.py -d /path/to/chisel/project
    
    # Process with custom repo name
    python chisel_runner.py -d /path/to/chisel/project -r my-processor
    
    # Save configuration to specific directory
    python chisel_runner.py -d /path/to/chisel/project -o ./configs
"""

import argparse
import json
import os
import sys
from core.chisel_manager import (
    find_scala_files,
    extract_chisel_modules,
    build_chisel_dependency_graph,
    find_top_module,
    generate_main_app,
    configure_build_sbt,
    emit_verilog,
    process_chisel_project,
)
from core.log import print_green, print_red, print_yellow


def main():
    parser = argparse.ArgumentParser(
        description='Process Chisel projects and generate Verilog',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a local Chisel project
  python chisel_runner.py -d /path/to/chisel/project
  
  # Process with custom repo name
  python chisel_runner.py -d /path/to/chisel/project -r my-processor
  
  # Save configuration to specific directory
  python chisel_runner.py -d /path/to/chisel/project -o ./configs
        """
    )
    
    parser.add_argument(
        '-d', '--directory',
        type=str,
        required=True,
        help='Path to the Chisel project directory'
    )
    
    parser.add_argument(
        '-r', '--repo-name',
        type=str,
        default=None,
        help='Repository name (default: directory name)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='./config',
        help='Output directory for configuration file (default: ./config)'
    )
    
    parser.add_argument(
        '--skip-verilog',
        action='store_true',
        help='Skip Verilog generation (only analyze project)'
    )
    
    parser.add_argument(
        '--list-modules',
        action='store_true',
        help='List all found modules and exit'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.exists(args.directory):
        print_red(f"[ERROR] Directory not found: {args.directory}")
        return 1
    
    directory = os.path.abspath(args.directory)
    repo_name = args.repo_name or os.path.basename(directory)
    
    print_green(f"[INFO] Processing Chisel project: {directory}")
    print_green(f"[INFO] Repository name: {repo_name}\n")
    
    # Step 1: Find Scala files
    print_green("[STEP 1] Finding Scala files...")
    scala_files = find_scala_files(directory)
    print_green(f"[INFO] Found {len(scala_files)} Scala files\n")
    
    if not scala_files:
        print_red("[ERROR] No Scala files found")
        return 1
    
    # Step 2: Extract Chisel modules
    print_green("[STEP 2] Extracting Chisel modules...")
    modules = extract_chisel_modules(scala_files)
    print_green(f"[INFO] Found {len(modules)} Chisel modules\n")
    
    if not modules:
        print_red("[ERROR] No Chisel modules found")
        return 1
    
    # List modules if requested
    if args.list_modules:
        print_green("[MODULES]")
        for module_name, file_path in sorted(modules):
            rel_path = os.path.relpath(file_path, directory)
            print(f"  - {module_name} ({rel_path})")
        return 0
    
    # Step 3: Build dependency graph
    print_green("[STEP 3] Building dependency graph...")
    module_graph, module_graph_inverse = build_chisel_dependency_graph(modules)
    
    # Print dependency summary
    instantiated_count = sum(1 for v in module_graph_inverse.values() if v)
    standalone_count = sum(1 for v in module_graph_inverse.values() if not v)
    print_green(f"[INFO] Modules instantiated by others: {instantiated_count}")
    print_green(f"[INFO] Standalone modules: {standalone_count}\n")
    
    # Step 4: Identify top module
    print_green("[STEP 4] Identifying top module...")
    top_module = find_top_module(module_graph, module_graph_inverse, modules, repo_name)
    
    if not top_module:
        print_red("[ERROR] Could not identify top module")
        return 1
    
    print_green(f"[INFO] Top module: {top_module}\n")
    
    if args.skip_verilog:
        print_yellow("[INFO] Skipping Verilog generation (--skip-verilog)")
        return 0
    
    # Step 5: Generate or find main App
    print_green("[STEP 5] Generating main App...")
    main_app = generate_main_app(directory, top_module)
    print_green(f"[INFO] Main App: {os.path.relpath(main_app, directory)}\n")
    
    # Step 6: Configure build.sbt
    print_green("[STEP 6] Configuring build.sbt...")
    build_sbt = configure_build_sbt(directory, top_module)
    print_green(f"[INFO] build.sbt: {os.path.relpath(build_sbt, directory)}\n")
    
    # Step 7: Emit Verilog
    print_green("[STEP 7] Generating Verilog (this may take a while)...")
    success, verilog_file, log = emit_verilog(directory, main_app)
    
    if not success:
        print_red("[ERROR] Failed to generate Verilog")
        print_yellow("[LOG] SBT output:")
        print(log)
        return 1
    
    print_green(f"[SUCCESS] Generated Verilog: {os.path.relpath(verilog_file, directory)}\n")
    
    # Step 8: Save configuration
    print_green("[STEP 8] Saving configuration...")
    
    config = {
        'name': repo_name,
        'folder': os.path.basename(directory),
        'language': 'chisel',
        'top_module': top_module,
        'main_app': os.path.relpath(main_app, directory),
        'build_sbt': os.path.relpath(build_sbt, directory),
        'generated_verilog': os.path.relpath(verilog_file, directory),
        'modules': [
            {'module': name, 'file': os.path.relpath(path, directory)}
            for name, path in modules
        ],
        'is_simulable': True
    }
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Save configuration
    config_file = os.path.join(args.output_dir, f"{repo_name}.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    
    print_green(f"[SUCCESS] Configuration saved to: {config_file}")
    
    # Print summary
    print_green("\n" + "="*60)
    print_green("SUMMARY")
    print_green("="*60)
    print(f"Project:          {repo_name}")
    print(f"Modules found:    {len(modules)}")
    print(f"Top module:       {top_module}")
    print(f"Verilog output:   {verilog_file}")
    print(f"Configuration:    {config_file}")
    print_green("="*60 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
