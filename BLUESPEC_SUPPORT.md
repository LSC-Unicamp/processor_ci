# Bluespec SystemVerilog Support in Processor CI

This document describes the Bluespec SystemVerilog (BSV) support added to the Processor CI configuration generator.

## Overview

The config generator now automatically detects and processes Bluespec projects, extracting module definitions, building dependency graphs, identifying top-level modules, and compiling to Verilog using the bsc compiler.

## How It Works

### 1. Detection
When processing a repository, the config generator checks for `.bsv` files. If found, it automatically switches to Bluespec processing mode.

### 2. Module Extraction
The system parses BSV files to find module definitions following Bluespec conventions:
```bsv
module mkCore(CoreIfc);
    // module implementation
endmodule

module [Module] mkProcessor(ProcIfc);
    // module implementation with monad
endmodule

(* synthesize *)
module mkTop(TopIfc);
    // synthesizable top module
endmodule
```

Bluespec convention: module names typically start with `mk` prefix (mkCore, mkALU, mkCache, etc.)

### 3. Interface Extraction
The system also extracts interface definitions:
```bsv
interface CoreIfc;
    method Action start();
    method Bit#(32) getResult();
    interface FIFOF#(Data) dataFifo;
endinterface
```

### 4. Dependency Graph
It analyzes module instantiations to build a dependency graph:
```bsv
ALU alu <- mkALU();
Cache cache <- mkCache(params);
let regFile <- mkRegFile();
```

### 5. Top Module Identification
Using sophisticated heuristics, it identifies the top-level module:
- Modules with zero parents (not instantiated by others)
- Modules with "mkTop", "mkCore", or "mkProcessor" patterns
- Modules matching the repository name (e.g., `mkBluespec` for bluespec-cpu repo)
- Modules that instantiate many other modules
- Synthesizable modules marked with `(* synthesize *)`

### 6. Verilog Generation
The system:
1. Identifies the top module and its containing file
2. Constructs the appropriate `bsc` command with search paths
3. Runs `bsc -verilog -g <top_module> <file>` to generate Verilog
4. Locates the generated `.v` file

## Usage

### Using config_generator.py (Recommended)

For a remote Bluespec repository:
```bash
python config_generator.py -u https://github.com/user/bsv-processor -p config/
```

For a local Bluespec project:
```bash
python config_generator.py -u https://github.com/user/bsv-processor \
    -l /path/to/local/bsv/project \
    -p config/
```

### Using bluespec_manager.py Directly

For direct processing of a local Bluespec project:
```python
from processor_ci.core.bluespec_manager import process_bluespec_project

config = process_bluespec_project(
    directory='/path/to/bsv/project',
    repo_name='my-riscv-core'
)
print(config)
```

## Requirements

- Python 3.7+
- Bluespec Compiler (bsc) installed and in PATH
- Bluespec SystemVerilog libraries

### Installing Bluespec Compiler

**Open Source Version:**
```bash
git clone https://github.com/B-Lang-org/bsc
cd bsc
make install
```

**Commercial Version:**
Available from Bluespec, Inc.

## Bluespec Patterns Supported

### Module Definitions
- `module mkModuleName(InterfaceName);`
- `module [Module] mkModuleName(InterfaceName);`
- `(* synthesize *) module mkModuleName(...);`
- `module mkModuleName(); // Empty interface`

### Module Instantiations
- `ALU alu <- mkALU();`
- `Cache cache <- mkCache(params);`
- `let regFile <- mkRegFile();`
- `RegFile#(Addr, Data) rf <- mkRegFile();`

### Interfaces
- `interface InterfaceName; ... endinterface`
- `interface SubInterface; ... endinterface`

## Output Configuration

The generated JSON configuration includes:

```json
{
  "name": "processor-name",
  "folder": "processor-name",
  "language": "bluespec",
  "top_module": "mkCore",
  "files": ["mkCore.v"],
  "source_files": [
    "src/Core.bsv",
    "src/ALU.bsv",
    "src/Cache.bsv"
  ],
  "interfaces": [
    "CoreIfc",
    "ALUIfc",
    "CacheIfc"
  ],
  "modules": [
    {"module": "mkCore", "file": "src/Core.bsv"},
    {"module": "mkALU", "file": "src/ALU.bsv"},
    {"module": "mkCache", "file": "src/Cache.bsv"}
  ],
  "is_simulable": true
}
```

## Implementation Details

### Core Module: `core/bluespec_manager.py`

The Bluespec manager provides the following main functions:

#### `find_bsv_files(directory: str) -> List[str]`
Locates all `.bsv` files in the project directory, excluding:
- Build directories (build, obj, bdir, simdir, verilog)
- Test directories
- Git directories

#### `extract_bluespec_modules(bsv_files: List[str]) -> List[Tuple[str, str]]`
Extracts module definitions (mk* pattern) from BSV files.

Returns: List of (module_name, file_path) tuples

#### `find_module_instantiations(file_path: str) -> Set[str]`
Finds all module instantiations in a BSV file using pattern matching.

Returns: Set of instantiated module names

#### `extract_interfaces(bsv_files: List[str]) -> List[Tuple[str, str]]`
Extracts interface definitions from BSV files.

Returns: List of (interface_name, file_path) tuples

#### `build_bluespec_dependency_graph(modules) -> Tuple[Dict, Dict]`
Builds dependency graph showing which modules instantiate which other modules.

Returns:
- `module_graph`: module_name -> list of instantiated modules
- `module_graph_inverse`: module_name -> list of modules that instantiate it

#### `find_top_module(module_graph, module_graph_inverse, modules, repo_name) -> Optional[str]`
Identifies the top-level module using sophisticated scoring:
- Repository name matching (highest priority)
- Bluespec patterns (mkTop, mkCore, mkProcessor)
- Architectural indicators (CPU, core, processor)
- Structural analysis (parent/child relationships)
- Negative indicators (peripherals, test benches, utilities)

Returns: Name of the top module

#### `compile_to_verilog(directory, top_module, bsv_files, timeout, search_paths) -> Tuple[bool, str, str]`
Compiles Bluespec to Verilog using bsc compiler.

Returns: (success, verilog_file_path, log_output)

#### `process_bluespec_project(directory: str, repo_name: str) -> Dict`
End-to-end processing of a Bluespec project.

Returns: Configuration dictionary

## BSC Compiler Command

The system constructs and runs:
```bash
bsc -verilog -g <top_module> -u -aggressive-conditions \
    -p <directory>:%/Libraries <file_with_top_module>
```

### BSC Flags Used:
- `-verilog`: Generate Verilog output
- `-g <top_module>`: Specify top-level module to compile
- `-u`: Update/recompile only changed files
- `-aggressive-conditions`: Enable optimization
- `-p <path>`: Add search paths for BSV packages

## Directory Structure

Typical Bluespec project structure:
```
project/
├── src/
│   ├── Core.bsv          # mkCore module
│   ├── ALU.bsv           # mkALU module
│   ├── Cache.bsv         # mkCache module
│   └── Interfaces.bsv    # Interface definitions
├── sim/
│   └── Testbench.bsv     # Testbenches (excluded)
└── build/                # Build output (excluded)
```

## Common Issues and Solutions

### Issue: bsc compiler not found
**Solution:** Install Bluespec Compiler and add to PATH:
```bash
export PATH=$PATH:/path/to/bsc/bin
```

### Issue: Package not found
**Solution:** Add search paths for Bluespec libraries:
- Check `BSC_INSTALL_DIR` environment variable
- Ensure standard libraries are accessible
- Add custom package paths if needed

### Issue: Multiple top modules detected
**Solution:** The scoring algorithm should handle this automatically by:
- Matching repository name
- Preferring mkTop/mkCore patterns
- Analyzing instantiation graph

### Issue: Generated Verilog not found
**Solution:** Check bsc output directory:
- Default: current directory
- Check for `mkModuleName.v` file
- Verify bsc completed successfully

## Advanced Features

### Custom Search Paths
```python
from processor_ci.core.bluespec_manager import compile_to_verilog

success, verilog, log = compile_to_verilog(
    directory='/path/to/project',
    top_module='mkCore',
    bsv_files=bsv_files,
    search_paths=['/custom/packages', '/additional/libs']
)
```

### Module Graph Analysis
```python
from processor_ci.core.bluespec_manager import (
    extract_bluespec_modules,
    build_bluespec_dependency_graph
)

modules = extract_bluespec_modules(bsv_files)
module_graph, module_graph_inverse = build_bluespec_dependency_graph(modules)

# Analyze dependencies
for module, children in module_graph.items():
    print(f"{module} instantiates: {children}")
```

### Interface Extraction
```python
from processor_ci.core.bluespec_manager import extract_interfaces

interfaces = extract_interfaces(bsv_files)
for ifc_name, file_path in interfaces:
    print(f"Interface {ifc_name} defined in {file_path}")
```

## Example Bluespec Projects

The system has been tested with various Bluespec projects including:
- RISC-V cores (Piccolo, Flute, Toooba)
- Custom processor designs
- SoC components
- Hardware accelerators

## Comparison with Other HDLs

| Feature | Verilog/SV | VHDL | Chisel | Bluespec |
|---------|------------|------|---------|----------|
| Module Pattern | `module X` | `entity X` | `class X extends Module` | `module mkX` |
| Instantiation | `X inst()` | `inst: X port map` | `Module(new X)` | `x <- mkX()` |
| Top Detection | Heuristics | Heuristics | Graph + Heuristics | mk* + Heuristics |
| Compilation | N/A | N/A | SBT | bsc |

## Future Enhancements

Potential improvements:
- [ ] Support for Bluespec packages and imports
- [ ] Better handling of parametric modules
- [ ] Detection of clock domains
- [ ] Support for BSV simulation (bsim)
- [ ] Integration with BlueSim/Verilog simulation
- [ ] Automatic testbench generation

## References

- [Bluespec SystemVerilog Language Reference](http://wiki.bluespec.com/)
- [BSC Compiler Documentation](https://github.com/B-Lang-org/bsc)
- [Bluespec Tutorial](http://csg.csail.mit.edu/6.375/6_375_2019_www/resources/bsv_by_example.pdf)

## Contributing

When contributing Bluespec support improvements:
1. Test with multiple Bluespec projects
2. Verify bsc compilation works
3. Check dependency graph accuracy
4. Ensure top module detection is robust
5. Update this documentation

## License

Same as Processor CI project license.
