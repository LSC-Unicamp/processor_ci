# Bluespec Quick Reference

## Files Overview
```
processor_ci/
├── core/
│   └── bluespec_manager.py       # Core implementation (782 lines)
├── bluespec_runner.py            # Standalone runner (213 lines)
├── test_bluespec_manager.py      # Test suite (315 lines)
├── BLUESPEC_SUPPORT.md           # User documentation (358 lines)
├── BLUESPEC_IMPLEMENTATION.md    # Integration guide (377 lines)
└── BLUESPEC_SUMMARY.md           # This summary
```

## Command Quick Reference

### Using Standalone Runner
```bash
# List all modules and interfaces
python processor_ci/bluespec_runner.py -d /path/to/project --list-modules

# Analyze without compiling (no bsc required)
python processor_ci/bluespec_runner.py -d /path/to/project --skip-verilog

# Full processing with Verilog generation (requires bsc)
python processor_ci/bluespec_runner.py -d /path/to/project -o config/

# With custom repo name for better heuristics
python processor_ci/bluespec_runner.py -d /path/to/project -r my-core --skip-verilog
```

### Run Tests
```bash
python processor_ci/test_bluespec_manager.py
```

## Python API Quick Reference

### Import
```python
from processor_ci.core.bluespec_manager import (
    find_bsv_files,
    extract_bluespec_modules,
    extract_interfaces,
    build_bluespec_dependency_graph,
    find_top_module,
    compile_to_verilog,
    process_bluespec_project
)
```

### Basic Usage
```python
# Complete processing
config = process_bluespec_project('/path/to/bsv/project', repo_name='my-core')

# Step-by-step
bsv_files = find_bsv_files('/path/to/project')
modules = extract_bluespec_modules(bsv_files)
interfaces = extract_interfaces(bsv_files)
graph, inv_graph = build_bluespec_dependency_graph(modules)
top = find_top_module(graph, inv_graph, modules, 'my-core')
success, verilog, log = compile_to_verilog('/path', top, bsv_files)
```

## Bluespec Patterns Recognized

### Module Definitions ✓
```bsv
module mkCore(CoreIfc);                    // Standard
module [Module] mkCore(CoreIfc);           // With monad
(* synthesize *) module mkTop(TopIfc);     // Synthesizable
module mkRegFile();                        // Empty interface
```

### Instantiations ✓
```bsv
ALU alu <- mkALU();                        // Basic
Cache cache <- mkCache(params);            // With params
let rf <- mkRegFile();                     // With let
RegFile#(Addr, Data) rf <- mkRegFile();    // Parametric
```

### Interfaces ✓
```bsv
interface CoreIfc;
    method Action start();
    method Bit#(32) result();
endinterface
```

## Top Module Scoring Examples

From test run:
- `mkCore`: **13,510** points (winner)
  - mkCore pattern: +5,000
  - Direct core: +4,000
  - *Core suffix: +3,500
  - One parent: +1,000
  
- `mkTop`: **12,520** points
  - mkTop pattern: +6,000
  - CPU top pattern: +4,500
  - Zero parents: +2,000
  
- `mkALU`: **-1,000** points (filtered)
  - One parent: +1,000
  - Functional unit: -2,000

## BSC Compilation Command

Generated command:
```bash
bsc -verilog -g mkCore -u -aggressive-conditions \
    -p /path/to/project:%/Libraries \
    /path/to/Core.bsv
```

Output: `mkCore.v`

## Configuration Output Schema

```json
{
  "name": "project-name",
  "folder": "project-folder",
  "language": "bluespec",
  "top_module": "mkCore",
  "files": ["mkCore.v"],
  "source_files": ["src/Core.bsv", "src/ALU.bsv"],
  "interfaces": ["CoreIfc", "ALUIfc"],
  "is_simulable": true
}
```

## Common Issues

### bsc not found
```bash
export PATH=$PATH:/path/to/bsc/bin
# or install: https://github.com/B-Lang-org/bsc
```

### Wrong top module
- Use `-r/--repo-name` flag with repository name
- Check module naming (mk* prefix)
- Review scoring in debug output

### Compilation fails
- Check BSC_INSTALL_DIR environment variable
- Verify package imports are available
- Check syntax in BSV files

## Integration Checklist

To integrate into config_generator.py:

- [ ] Import `process_bluespec_project` from `bluespec_manager`
- [ ] Add `.bsv` file detection
- [ ] Add `language='bluespec'` case
- [ ] Call `process_bluespec_project(directory, repo_name)`
- [ ] Handle config output
- [ ] Test with real Bluespec projects

## Test Projects

Good projects for testing:
1. **Piccolo** - Small RISC-V (https://github.com/bluespec/Piccolo)
2. **Flute** - Mid-range RISC-V (https://github.com/bluespec/Flute)
3. **Toooba** - Superscalar RISC-V (https://github.com/bluespec/Toooba)

## Status: ✅ Complete

- [x] Core implementation
- [x] Standalone runner
- [x] Test suite (all passing)
- [x] User documentation
- [x] Integration guide
- [x] Summary documentation

**Ready for integration and deployment!**
