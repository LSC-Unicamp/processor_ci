# Chisel Support in Processor CI

This document describes the Chisel/Scala support added to the Processor CI configuration generator.

## Overview

The config generator now automatically detects and processes Chisel projects, extracting module definitions, building dependency graphs, identifying top-level modules, and generating Verilog output via SBT.

## How It Works

### 1. Detection
When processing a repository, the config generator checks for `.scala` files. If found, it automatically switches to Chisel processing mode.

### 2. Module Extraction
The system parses Scala files to find Chisel module definitions:
```scala
class MyModule extends Module { ... }
class MyModule extends RawModule { ... }
object MyModule extends Module { ... }
```

### 3. Dependency Graph
It analyzes module instantiations to build a dependency graph:
```scala
val submodule = Module(new SubModule())
```

### 4. Top Module Identification
Using heuristics, it identifies the top-level module (not instantiated by any other module):
- Modules with zero parents (not instantiated by others)
- Modules with "top" in the name
- Modules matching the repository name
- Modules that instantiate many other modules

### 5. Verilog Generation
The system:
1. Finds or generates a main `App` object that instantiates the top module
2. Ensures `build.sbt` is properly configured
3. Runs `sbt runMain <MainApp>` to generate Verilog

## Usage

### Using config_generator.py (Recommended)

For a remote Chisel repository:
```bash
python config_generator.py -u https://github.com/user/chisel-processor -p config/
```

For a local Chisel project:
```bash
python config_generator.py -u https://github.com/user/chisel-processor \
    -l /path/to/local/chisel/project \
    -p config/
```

### Using chisel_runner.py (Optional)

For direct processing of a local Chisel project:
```bash
python chisel_runner.py -d /path/to/chisel/project -o config/
```

Options:
- `-d, --directory`: Path to Chisel project (required)
- `-r, --repo-name`: Repository name (default: directory name)
- `-o, --output-dir`: Output directory for config (default: ./config)
- `--skip-verilog`: Skip Verilog generation (analysis only)
- `--list-modules`: List all modules and exit

## Requirements

- Python 3.7+
- SBT (Scala Build Tool) installed and in PATH
- Chisel 3.x project with proper `build.sbt`

## Output Configuration

The generated JSON configuration includes:

```json
{
  "name": "processor-name",
  "folder": "processor-name",
  "language": "chisel",
  "top_module": "TopModule",
  "main_app": "src/main/scala/generated/GenerateVerilog.scala",
  "build_sbt": "build.sbt",
  "generated_verilog": "generated/TopModule.v",
  "modules": [
    {"module": "TopModule", "file": "src/main/scala/TopModule.scala"},
    {"module": "ALU", "file": "src/main/scala/ALU.scala"}
  ],
  "is_simulable": true
}
```

## Implementation Details

### Core Module: `core/chisel_manager.py`

Main functions:
- `find_scala_files()`: Locates all Scala files
- `extract_chisel_modules()`: Extracts module definitions
- `build_chisel_dependency_graph()`: Builds dependency relationships
- `find_top_module()`: Identifies the top-level module
- `generate_main_app()`: Creates/finds main App for Verilog generation
- `configure_build_sbt()`: Ensures proper build configuration
- `emit_verilog()`: Runs SBT to generate Verilog
- `process_chisel_project()`: End-to-end processing

### Integration in `config_generator.py`

The main config generator automatically:
1. Detects `.scala` files during file discovery
2. Switches to Chisel processing mode
3. Calls `process_chisel_project()` from `chisel_manager`
4. Saves configuration in the same format as HDL projects

## Testing

Run the test suite:
```bash
python test_chisel.py
```

This creates a minimal test project with:
- ALU module
- RegisterFile module
- SimpleCPU top module (instantiates ALU and RegisterFile)

And verifies:
- File discovery
- Module extraction
- Dependency graph construction
- Top module identification

## Limitations

- Requires SBT to be installed and accessible
- Only supports Chisel 3.x projects
- Assumes standard project structure (`src/main/scala/`)
- May timeout on very large projects (default: 300 seconds)

## Future Enhancements

- [ ] Support for Chisel parameters and configurations
- [ ] Multiple top module configurations
- [ ] Parallel SBT compilation
- [ ] Caching of generated Verilog
- [ ] Integration with Chisel test generation
- [ ] Support for custom SBT commands
