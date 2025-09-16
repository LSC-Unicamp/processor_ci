# Processor CI - Modular Architecture

This directory contains the modular processor CI system, separated into three distinct components for better maintainability and flexibility.

## Architecture Overview

The original monolithic `config_generator.py` has been separated into:

1. **Config Generator** (`config_generator_core.py`) - Analyzes repositories and generates processor configurations
2. **Template Generator** (`template_generator.py`) - Creates SystemVerilog templates for processors  
3. **Jenkins Generator** (`jenkins_generator.py`) - Generates Jenkins pipelines for CI/CD
4. **Orchestrator** (`orchestrator.py`) - Coordinates all three components (maintains backward compatibility)

## Components

### 1. Config Generator (`config_generator_core.py`)

Analyzes processor repositories to generate configuration files.

**Features:**
- Repository cloning and analysis
- Module extraction and dependency graphing
- Interactive simulation and file minimization
- Top module identification with heuristics
- Language detection (Verilog/SystemVerilog/VHDL)

**Usage:**
```bash
# Generate config for a processor
python config_generator_core.py -u https://github.com/user/processor.git -p config/

# With graph plotting
python config_generator_core.py -u https://github.com/user/processor.git -p config/ -g

# Skip OLLAMA processing
python config_generator_core.py -u https://github.com/user/processor.git -p config/ -n
```

**Arguments:**
- `-u, --processor-url`: Repository URL (required)
- `-p, --config-path`: Config output directory (default: 'config/')
- `-g, --plot-graph`: Plot module dependency graphs
- `-a, --add-to-config`: Add to central config file
- `-n, --no-llama`: Skip OLLAMA processing
- `-m, --model`: OLLAMA model (default: 'qwen2.5:32b')

### 2. Template Generator (`template_generator.py`)

Generates SystemVerilog templates for processor cores.

**Features:**
- Basic template generation
- Enhanced templates from processor configs
- OLLAMA-powered intelligent template creation
- Batch template generation

**Usage:**
```bash
# Generate template for specific processor
python template_generator.py -n processor_name -c config/processor.json

# Generate templates for all processors in config directory
python template_generator.py -d config/ -o rtl/

# Use OLLAMA for enhanced templates
python template_generator.py -n processor_name -c config/processor.json --use-ollama
```

**Arguments:**
- `-n, --name`: Processor name
- `-c, --config`: Specific config file
- `-d, --config-dir`: Config directory (batch mode)
- `-o, --output`: Output directory (default: 'rtl/')
- `-t, --template`: Base template file
- `--use-ollama`: Enable OLLAMA enhancement
- `-m, --model`: OLLAMA model

### 3. Jenkins Generator (`jenkins_generator.py`)

Creates Jenkins pipeline files for CI/CD.

**Features:**
- Single processor Jenkinsfile generation
- Batch Jenkinsfile generation
- Configurable FPGA targets
- Pipeline summary generation

**Usage:**
```bash
# Generate Jenkinsfile for specific processor
python jenkins_generator.py -c config/processor.json

# Generate Jenkinsfiles for all processors
python jenkins_generator.py -d config/ -o jenkins_pipeline/

# Custom FPGA targets
python jenkins_generator.py -d config/ -f "digilent_arty_a7_100t,xilinx_vc709"
```

**Arguments:**
- `-c, --config`: Specific config file
- `-d, --config-dir`: Config directory (batch mode)
- `-o, --output`: Output directory (default: 'jenkins_pipeline/')
- `-f, --fpgas`: Comma-separated FPGA list
- `-s, --script-path`: Synthesis script path
- `--summary`: Generate pipeline summary

### 4. Orchestrator (`orchestrator.py`)

Coordinates all components and maintains backward compatibility.

**Features:**
- Sequential execution of all components
- Selective component execution
- Progress tracking and error handling
- Backward compatibility with original script

**Usage:**
```bash
# Run all components (equivalent to original script)
python orchestrator.py -a -u https://github.com/user/processor.git

# Run only config generation
python orchestrator.py -c -u https://github.com/user/processor.git

# Run template + jenkins from existing configs
python orchestrator.py -t -j -p config/
```

**Arguments:**
- `-c, --generate-config`: Run config generation
- `-t, --generate-template`: Run template generation  
- `-j, --generate-jenkinsfile`: Run Jenkins generation
- `-a, --all`: Run all components
- All arguments from individual components are supported

## Migration Guide

### From Original Script

The original `config_generator.py` functionality is now split as follows:

| Original Function | New Location | Component |
|------------------|--------------|-----------|
| `generate_processor_config()` | `config_generator_core.py` | Config Generator |
| `copy_hardware_template()` | `template_generator.py` | Template Generator |
| `generate_all_pipelines()` | `jenkins_generator.py` | Jenkins Generator |

### Backward Compatibility

To maintain compatibility, you can:

1. Use the orchestrator with `-a` flag:
   ```bash
   python orchestrator.py -a -u <url>  # Equivalent to old script
   ```

2. Or create an alias/symlink:
   ```bash
   ln -s orchestrator.py config_generator.py
   ```

## File Structure

```
processor_ci/
├── config_generator_core.py    # Core config generation logic
├── template_generator.py       # Template generation
├── jenkins_generator.py        # Jenkins pipeline generation  
├── orchestrator.py            # Main orchestrator
├── core/                      # Shared utilities
│   ├── config.py
│   ├── file_manager.py
│   ├── graph.py
│   ├── jenkins.py
│   ├── ollama.py
│   └── log.py
└── README_modular.md          # This file
```

## Benefits of Modular Architecture

1. **Separation of Concerns**: Each component has a single responsibility
2. **Independent Usage**: Components can be used standalone
3. **Better Testing**: Easier to test individual components
4. **Maintainability**: Smaller, focused codebases
5. **Flexibility**: Mix and match components as needed
6. **Scalability**: Easy to extend or replace individual components

## Dependencies

All components share the same dependencies as the original script:
- Core modules (`core/`)
- Python standard library
- External tools (Verilator, GHDL for simulation)
- OLLAMA (optional, for enhanced functionality)

## Examples

### Complete Workflow
```bash
# 1. Generate config
python config_generator_core.py -u https://github.com/user/riscv-core.git -p config/

# 2. Generate template  
python template_generator.py -n riscv-core -c config/riscv-core.json

# 3. Generate Jenkins pipeline
python jenkins_generator.py -c config/riscv-core.json
```

### Batch Processing
```bash
# Generate templates for all existing configs
python template_generator.py -d config/ -o rtl/

# Generate Jenkinsfiles for all processors
python jenkins_generator.py -d config/ -o jenkins_pipeline/
```

### Using Orchestrator
```bash
# Everything in one command (like original script)
python orchestrator.py -a -u https://github.com/user/processor.git -p config/
```
