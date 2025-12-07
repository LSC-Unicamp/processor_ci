# Bluespec Integration Implementation Guide

This document describes how to integrate the Bluespec manager into the config_generator.py workflow.

## Files Created

1. **`processor_ci/core/bluespec_manager.py`** - Core Bluespec processing module
2. **`processor_ci/bluespec_runner.py`** - Standalone runner script
3. **`processor_ci/BLUESPEC_SUPPORT.md`** - User documentation

## Integration Steps

To integrate Bluespec support into `config_generator.py`, follow these steps:

### Step 1: Import Bluespec Manager

Add to imports in `config_generator.py`:

```python
from processor_ci.core.bluespec_manager import (
    find_bsv_files,
    process_bluespec_project
)
```

### Step 2: Add Bluespec Detection

In the language detection logic, add:

```python
def detect_hdl_language(directory: str) -> str:
    """Detect HDL language used in the project."""
    
    # Check for Bluespec files
    bsv_files = glob.glob(f'{directory}/**/*.bsv', recursive=True)
    if bsv_files:
        return 'bluespec'
    
    # Check for Chisel/Scala files
    scala_files = glob.glob(f'{directory}/**/*.scala', recursive=True)
    if scala_files:
        return 'chisel'
    
    # Check for VHDL files
    vhdl_files = glob.glob(f'{directory}/**/*.vhd', recursive=True) + \
                 glob.glob(f'{directory}/**/*.vhdl', recursive=True)
    if vhdl_files:
        return 'vhdl'
    
    # Default to Verilog/SystemVerilog
    return 'verilog'
```

### Step 3: Add Bluespec Processing

In the main processing logic, add a case for Bluespec:

```python
def process_repository(repo_url: str, local_path: str = None, **kwargs):
    """Process repository based on detected language."""
    
    # ... existing code ...
    
    # Detect language
    language = detect_hdl_language(directory)
    print(f"[INFO] Detected language: {language}")
    
    if language == 'bluespec':
        from processor_ci.core.bluespec_manager import process_bluespec_project
        config = process_bluespec_project(directory, repo_name)
        
        if 'error' in config:
            print(f"[ERROR] Failed to process Bluespec project: {config['error']}")
            return None
        
        # Add language field
        config['language'] = 'bluespec'
        return config
    
    elif language == 'chisel':
        from processor_ci.core.chisel_manager import process_chisel_project
        config = process_chisel_project(directory, repo_name)
        config['language'] = 'chisel'
        return config
    
    elif language == 'vhdl':
        # ... existing VHDL processing ...
        pass
    
    else:  # verilog
        # ... existing Verilog processing ...
        pass
```

### Step 4: Update Configuration Schema

Ensure the configuration schema supports Bluespec-specific fields:

```python
BLUESPEC_CONFIG_SCHEMA = {
    'name': str,           # Project name
    'folder': str,         # Folder name
    'language': str,       # 'bluespec'
    'top_module': str,     # mkCore, mkTop, etc.
    'files': list,         # Generated Verilog files
    'source_files': list,  # Original BSV files
    'interfaces': list,    # Interface definitions
    'repository': str,     # Repository URL
    'is_simulable': bool   # Whether compilation succeeded
}
```

### Step 5: Add BSC Installation Check

Add a utility to check if bsc is installed:

```python
def check_bsc_installed() -> bool:
    """Check if Bluespec Compiler (bsc) is installed."""
    try:
        result = subprocess.run(
            ['bsc', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[INFO] Found bsc: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("[WARNING] bsc compiler not found in PATH")
    except Exception as e:
        print(f"[WARNING] Error checking for bsc: {e}")
    
    return False
```

### Step 6: Handle Compilation Failures Gracefully

Add fallback logic for when bsc compilation fails:

```python
if language == 'bluespec':
    config = process_bluespec_project(directory, repo_name)
    
    if not config.get('is_simulable', False):
        print("[WARNING] Bluespec compilation failed, marking as non-simulable")
        # Still save the configuration for documentation purposes
        config['language'] = 'bluespec'
        config['compilation_error'] = config.get('error', 'Unknown error')
        # Remove error field so it can still be processed
        config.pop('error', None)
    
    return config
```

## Usage Examples

### Example 1: Process Remote Bluespec Repository

```bash
python config_generator.py -u https://github.com/bluespec/Piccolo -p config/
```

### Example 2: Process Local Bluespec Project

```bash
python config_generator.py -u https://github.com/bluespec/Piccolo \
    -l /path/to/local/Piccolo \
    -p config/
```

### Example 3: Use Standalone Runner

```bash
# List all modules
python processor_ci/bluespec_runner.py -d /path/to/bsv/project --list-modules

# Analyze without compiling
python processor_ci/bluespec_runner.py -d /path/to/bsv/project --skip-verilog

# Full processing with compilation
python processor_ci/bluespec_runner.py -d /path/to/bsv/project -o config/
```

## Testing

### Test with Known Bluespec Projects

Test the implementation with these open-source Bluespec projects:

1. **Piccolo** - Small RISC-V core
   - https://github.com/bluespec/Piccolo

2. **Flute** - Mid-range RISC-V core
   - https://github.com/bluespec/Flute

3. **Toooba** - Superscalar RISC-V core
   - https://github.com/bluespec/Toooba

### Manual Test Cases

Create a simple test BSV project:

```bash
mkdir -p test_bsv/src
cat > test_bsv/src/TestCore.bsv <<'EOF'
package TestCore;

interface CoreIfc;
    method Action start();
    method Bit#(32) result();
endinterface

interface ALUIfc;
    method Bit#(32) compute(Bit#(32) a, Bit#(32) b);
endinterface

module mkALU(ALUIfc);
    method Bit#(32) compute(Bit#(32) a, Bit#(32) b);
        return a + b;
    endmethod
endmodule

module mkCore(CoreIfc);
    ALU alu <- mkALU();
    Reg#(Bit#(32)) result_reg <- mkReg(0);
    
    method Action start();
        let res = alu.compute(32'd10, 32'd20);
        result_reg <= res;
    endmethod
    
    method Bit#(32) result();
        return result_reg;
    endmethod
endmodule

endpackage
EOF
```

Test it:

```bash
python processor_ci/bluespec_runner.py -d test_bsv --list-modules
```

## Troubleshooting

### Issue: bsc not found
**Solution:** Install Bluespec Compiler and add to PATH

### Issue: Package not found errors
**Solution:** Ensure BSC_INSTALL_DIR is set and libraries are accessible

### Issue: Wrong top module detected
**Solution:** Check module naming conventions (mk* prefix), use --repo-name flag

## Performance Considerations

- **File Scanning:** BSV files are typically smaller than Chisel/Scala, so scanning is fast
- **Parsing:** Regex-based parsing is efficient for BSV's clean syntax
- **Compilation:** bsc can be slow for large projects, adjust timeout as needed

## Comparison with Other HDLs

| Aspect | Verilog | VHDL | Chisel | Bluespec |
|--------|---------|------|---------|----------|
| File Scanning | Fast | Fast | Medium | Fast |
| Module Extraction | Regex | Regex | Scala AST | Regex |
| Dependency Graph | Pattern match | Pattern match | AST analysis | Pattern match |
| Top Detection | Heuristics | Heuristics | Graph+Heuristics | mk*+Heuristics |
| Compilation | N/A | N/A | SBT (slow) | bsc (medium) |
| Success Rate | High | High | Medium | High |

## Future Enhancements

1. **Better Package Support:** Handle Bluespec package imports
2. **Simulation Support:** Add bsim integration
3. **Parameterization:** Handle parametric modules better
4. **Clock Domain Analysis:** Detect and document clock domains
5. **Interface Documentation:** Generate interface documentation
6. **Multiple Top Modules:** Support multiple synthesizable modules

## Contributing

When adding improvements:
1. Test with real Bluespec projects
2. Verify bsc compilation succeeds
3. Update regex patterns if BSV syntax changes
4. Add test cases for new patterns
5. Update documentation

## References

- Main Documentation: `BLUESPEC_SUPPORT.md`
- Implementation: `processor_ci/core/bluespec_manager.py`
- Runner: `processor_ci/bluespec_runner.py`
- Bluespec Language: http://wiki.bluespec.com/
