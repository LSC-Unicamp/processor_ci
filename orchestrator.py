"""
Processor CI Orchestrator

This script serves as the main entry point for processor CI operations.
It can orchestrate the three main functionalities:
1. Config Generation (config_generator_core.py)
2. Template Generation (template_generator.py) 
3. Jenkins Pipeline Generation (jenkins_generator.py)

This maintains backward compatibility with the original script while
providing modular functionality.

Command-Line Interface:
-----------------------
- `-c`, `--generate-config`: Generate processor configuration
- `-t`, `--generate-template`: Generate SystemVerilog template
- `-j`, `--generate-jenkinsfile`: Generate Jenkins pipeline
- `-a`, `--all`: Run all three operations in sequence

Usage:
------
# Generate only config:
python orchestrator.py -c -u https://github.com/user/processor.git

# Generate all (config + template + jenkinsfile):
python orchestrator.py -a -u https://github.com/user/processor.git

# Generate template from existing config:
python orchestrator.py -t -n processor_name -p config/

# Generate jenkinsfiles from existing configs:
python orchestrator.py -j -d config/
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from core.log import print_green, print_red, print_yellow


def run_config_generator(args):
    """Run the config generator with appropriate arguments."""
    cmd = [sys.executable, 'config_generator_core.py']
    
    if args.processor_url:
        cmd.extend(['-u', args.processor_url])
    if args.config_path:
        cmd.extend(['-p', args.config_path])
    if args.plot_graph:
        cmd.append('-g')
    if args.add_to_config:
        cmd.append('-a')
    if args.no_llama:
        cmd.append('-n')
    if args.model:
        cmd.extend(['-m', args.model])
    
    print_green('[ORCHESTRATOR] Running config generator...')
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def run_template_generator(args):
    """Run the template generator with appropriate arguments."""
    cmd = [sys.executable, 'template_generator.py']
    
    if args.processor_name:
        cmd.extend(['-n', args.processor_name])
    elif args.config_path and args.processor_url:
        # Extract processor name from URL
        processor_name = args.processor_url.split('/')[-1].replace('.git', '')
        cmd.extend(['-n', processor_name])
    
    if args.config_path:
        if args.processor_name:
            config_file = os.path.join(args.config_path, f"{args.processor_name}.json")
        elif args.processor_url:
            processor_name = args.processor_url.split('/')[-1].replace('.git', '')
            config_file = os.path.join(args.config_path, f"{processor_name}.json")
        else:
            config_file = None
            
        if config_file and os.path.exists(config_file):
            cmd.extend(['-c', config_file])
        elif os.path.isdir(args.config_path):
            cmd.extend(['-d', args.config_path])
    
    if args.output_dir:
        cmd.extend(['-o', args.output_dir])
    if args.template_path:
        cmd.extend(['-t', args.template_path])
    if args.use_ollama:
        cmd.append('--use-ollama')
    if args.model:
        cmd.extend(['-m', args.model])
    
    print_green('[ORCHESTRATOR] Running template generator...')
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def run_jenkins_generator(args):
    """Run the Jenkins generator with appropriate arguments."""
    cmd = [sys.executable, 'jenkins_generator.py']
    
    if args.config_path:
        if args.processor_name:
            config_file = os.path.join(args.config_path, f"{args.processor_name}.json")
            if os.path.exists(config_file):
                cmd.extend(['-c', config_file])
            else:
                cmd.extend(['-d', args.config_path])
        elif args.processor_url:
            processor_name = args.processor_url.split('/')[-1].replace('.git', '')
            config_file = os.path.join(args.config_path, f"{processor_name}.json")
            if os.path.exists(config_file):
                cmd.extend(['-c', config_file])
            else:
                cmd.extend(['-d', args.config_path])
        else:
            cmd.extend(['-d', args.config_path])
    
    if args.jenkins_output_dir:
        cmd.extend(['-o', args.jenkins_output_dir])
    if args.fpgas:
        cmd.extend(['-f', args.fpgas])
    if args.script_path:
        cmd.extend(['-s', args.script_path])
    
    cmd.append('--summary')  # Always generate summary
    
    print_green('[ORCHESTRATOR] Running Jenkins generator...')
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    """Main orchestrator function."""
    parser = argparse.ArgumentParser(
        description='Processor CI Orchestrator - Generate configs, templates, and Jenkins pipelines'
    )

    # Operation selection
    operation_group = parser.add_argument_group('Operations')
    operation_group.add_argument(
        '-c', '--generate-config', action='store_true',
        help='Generate processor configuration'
    )
    operation_group.add_argument(
        '-t', '--generate-template', action='store_true',
        help='Generate SystemVerilog template'
    )
    operation_group.add_argument(
        '-j', '--generate-jenkinsfile', action='store_true',
        help='Generate Jenkins pipeline'
    )
    operation_group.add_argument(
        '-a', '--all', action='store_true',
        help='Run all operations (config + template + jenkins)'
    )

    # Config generation options
    config_group = parser.add_argument_group('Config Generation')
    config_group.add_argument(
        '-u', '--processor-url', type=str,
        help='URL of the processor repository'
    )
    config_group.add_argument(
        '-p', '--config-path', type=str, default='config/',
        help='Path to configuration directory'
    )
    config_group.add_argument(
        '-g', '--plot-graph', action='store_true',
        help='Plot module dependency graph'
    )
    config_group.add_argument(
        '--add-to-config', action='store_true',
        help='Add generated configuration to central config file'
    )
    config_group.add_argument(
        '-n', '--no-llama', action='store_true',
        help='Skip OLLAMA processing'
    )
    config_group.add_argument(
        '-m', '--model', type=str, default='qwen2.5:32b',
        help='OLLAMA model to use'
    )

    # Template generation options
    template_group = parser.add_argument_group('Template Generation')
    template_group.add_argument(
        '--processor-name', type=str,
        help='Processor name (for template generation)'
    )
    template_group.add_argument(
        '-o', '--output-dir', type=str, default='rtl/',
        help='Output directory for templates'
    )
    template_group.add_argument(
        '--template-path', type=str, default='rtl/template.sv',
        help='Base template file to use'
    )
    template_group.add_argument(
        '--use-ollama', action='store_true',
        help='Use OLLAMA for enhanced template generation'
    )

    # Jenkins generation options
    jenkins_group = parser.add_argument_group('Jenkins Generation')
    jenkins_group.add_argument(
        '--jenkins-output-dir', type=str, default='jenkins_pipeline/',
        help='Output directory for Jenkinsfiles'
    )
    jenkins_group.add_argument(
        '--fpgas', type=str,
        help='Comma-separated list of target FPGAs'
    )
    jenkins_group.add_argument(
        '--script-path', type=str, default='/eda/processor_ci/main.py',
        help='Path to main synthesis script'
    )

    args = parser.parse_args()

    # Validate arguments
    if not any([args.generate_config, args.generate_template, args.generate_jenkinsfile, args.all]):
        print_red('[ERROR] No operation specified. Use -c, -t, -j, or -a')
        parser.print_help()
        return 1

    if (args.generate_config or args.all) and not args.processor_url:
        print_red('[ERROR] --processor-url is required for config generation')
        return 1

    success = True
    results = []

    try:
        # Run operations in sequence
        if args.all or args.generate_config:
            print_green('\n' + '='*50)
            print_green('[ORCHESTRATOR] STEP 1: CONFIGURATION GENERATION')
            print_green('='*50)
            
            if run_config_generator(args):
                results.append("✓ Configuration generation succeeded")
                print_green('[ORCHESTRATOR] Config generation completed successfully')
            else:
                results.append("✗ Configuration generation failed")
                print_red('[ORCHESTRATOR] Config generation failed')
                success = False

        if (args.all or args.generate_template) and success:
            print_green('\n' + '='*50)
            print_green('[ORCHESTRATOR] STEP 2: TEMPLATE GENERATION')
            print_green('='*50)
            
            if run_template_generator(args):
                results.append("✓ Template generation succeeded")
                print_green('[ORCHESTRATOR] Template generation completed successfully')
            else:
                results.append("✗ Template generation failed")
                print_yellow('[ORCHESTRATOR] Template generation failed (continuing...)')

        if (args.all or args.generate_jenkinsfile) and (success or not args.all):
            print_green('\n' + '='*50)
            print_green('[ORCHESTRATOR] STEP 3: JENKINS PIPELINE GENERATION')
            print_green('='*50)
            
            if run_jenkins_generator(args):
                results.append("✓ Jenkins generation succeeded")
                print_green('[ORCHESTRATOR] Jenkins generation completed successfully')
            else:
                results.append("✗ Jenkins generation failed")
                print_yellow('[ORCHESTRATOR] Jenkins generation failed')

        # Print summary
        print_green('\n' + '='*50)
        print_green('[ORCHESTRATOR] EXECUTION SUMMARY')
        print_green('='*50)
        
        for result in results:
            if result.startswith("✓"):
                print_green(result)
            else:
                print_red(result)

        if args.processor_url:
            processor_name = args.processor_url.split('/')[-1].replace('.git', '')
            print_green(f'\n[ORCHESTRATOR] Processor: {processor_name}')
            
            # Show generated files
            config_file = os.path.join(args.config_path, f"{processor_name}.json")
            template_file = os.path.join(args.output_dir, f"{processor_name}.sv")
            jenkins_file = os.path.join(args.jenkins_output_dir, f"{processor_name}.Jenkinsfile")
            
            print_green('\nGenerated files:')
            if os.path.exists(config_file):
                print(f"  📄 Config: {config_file}")
            if os.path.exists(template_file):
                print(f"  📄 Template: {template_file}")
            if os.path.exists(jenkins_file):
                print(f"  📄 Jenkinsfile: {jenkins_file}")

        return 0 if success else 1

    except KeyboardInterrupt:
        print_yellow('\n[ORCHESTRATOR] Operation cancelled by user')
        return 1
    except Exception as e:
        print_red(f'[ORCHESTRATOR ERROR] {e}')
        return 1


if __name__ == '__main__':
    exit(main())
