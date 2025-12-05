# Enhanced Chisel Support - Multi-Module Projects

## Overview

Enhanced the Chisel support to handle complex multi-module SBT projects where there can be multiple `build.sbt` files in different directories.

## Problem

In many Chisel projects, especially larger ones, the project structure follows SBT's multi-module pattern:

```
project-root/
├── build.sbt                    # Root aggregator build
├── core/
│   ├── build.sbt               # Core submodule build
│   └── src/main/scala/core/
│       ├── CPU.scala           # Top module here
│       └── ALU.scala
├── utils/
│   ├── build.sbt               # Utils submodule build
│   └── src/main/scala/utils/
│       └── Counter.scala
└── peripherals/
    ├── build.sbt               # Peripherals submodule build
    └── src/main/scala/periph/
        └── UART.scala
```

The previous implementation would:
1. Only look for `build.sbt` at the root
2. Not consider the submodule where the top module actually lives
3. Place the main App in a generic location

## Solution

### 1. Smart build.sbt Discovery

Implemented `find_build_sbt()` with multiple strategies:

**Strategy 1: Proximity to Top Module**
- If we know the top module location, walk up from its file to find the nearest `build.sbt`
- This ensures we use the correct submodule's build configuration

**Strategy 2: Content Analysis**
- If multiple `build.sbt` files exist, analyze their content
- Prefer files that reference the top module or have Chisel dependencies

**Strategy 3: Root Preference**
- If a root-level `build.sbt` exists and strategies 1-2 don't apply, use it

**Strategy 4: First Found Fallback**
- As a last resort, use the first `build.sbt` found

### 2. Package-Aware Main App Generation

Enhanced `generate_main_app()` to:

1. **Detect the top module's package** by parsing its Scala file
2. **Place the main App in the same package** as the top module
3. **Find the correct src/main/scala directory** by walking up from the module file
4. **Generate imports appropriately** based on package structure

### 3. Intelligent build.sbt Configuration

Updated `configure_build_sbt()` to:

1. **Find the correct build.sbt** using the enhanced discovery
2. **Verify Chisel dependencies** are present
3. **Create build.sbt in the right location** if needed:
   - Near the top module if possible
   - At the project root as fallback

## Code Changes

### Modified Functions

#### `find_build_sbt(directory, top_module, modules)`
```python
# New signature adds top_module and modules parameters
# Returns the most appropriate build.sbt for the project
```

Key features:
- Walks up from top module file to find nearest `build.sbt`
- Handles multiple `build.sbt` files intelligently
- Analyzes content to find relevant build files

#### `configure_build_sbt(directory, top_module, modules)`
```python
# Enhanced to use smart discovery
# Creates build.sbt near top module if needed
```

Key features:
- Uses enhanced `find_build_sbt()`
- Determines optimal location for new `build.sbt`
- Verifies Chisel dependencies are present

#### `generate_main_app(directory, top_module, modules)`
```python
# New modules parameter for package detection
# Places App in top module's package
```

Key features:
- Extracts package from top module file
- Places main App in correct package directory
- Finds appropriate src/main/scala base directory

#### `get_module_package(file_path)` - NEW
```python
# Extracts package name from Scala file
# Returns: Optional[str]
```

## Test Coverage

### Test 1: Basic Functionality (test_chisel.py)
- Tests 1-4: Original functionality
- Test 5: Multiple build.sbt discovery
- Test 6: Package detection and main App generation

### Test 2: Multi-Module Projects (test_chisel_multimodule.py)
- Creates realistic multi-module SBT project
- Tests discovery of correct submodule build.sbt
- Verifies package detection across modules
- Confirms main App placement in correct package

## Example Scenarios

### Scenario 1: Single Module Project
```
project/
├── build.sbt
└── src/main/scala/
    └── CPU.scala
```
Result: Uses root `build.sbt`, detects package, places App appropriately

### Scenario 2: Multi-Module Project
```
project/
├── build.sbt                 # Root aggregator
├── core/
│   ├── build.sbt            # ← Found and used
│   └── src/main/scala/core/
│       └── CPU.scala        # ← Top module
└── utils/
    ├── build.sbt
    └── src/main/scala/utils/
        └── Helper.scala
```
Result: Finds `core/build.sbt`, detects `package core`, places App in `core/src/main/scala/core/`

### Scenario 3: No build.sbt Near Top Module
```
project/
└── src/main/scala/
    └── TopLevel.scala        # ← Top module
```
Result: Creates `build.sbt` at root with proper Chisel dependencies

## Benefits

1. **Handles Real-World Projects**: Works with complex multi-module structures
2. **Correct Package Resolution**: Main App uses the same package as top module
3. **Proper Build Configuration**: Uses the right build.sbt for the submodule
4. **Reduces Manual Intervention**: Automatically finds and configures correctly
5. **Maintains Clean Structure**: Doesn't pollute wrong directories with files

## API Changes

All changes are backward compatible - if `modules` parameter is not provided, functions fall back to simpler behavior.

### Function Signatures

```python
# Before
find_build_sbt(directory: str) -> Optional[str]
configure_build_sbt(directory: str, top_module: str = None) -> str
generate_main_app(directory: str, top_module: str, package_name: str = "generated") -> str

# After (backward compatible)
find_build_sbt(directory: str, top_module: str = None, modules: List[Tuple[str, str]] = None) -> Optional[str]
configure_build_sbt(directory: str, top_module: str = None, modules: List[Tuple[str, str]] = None) -> str
generate_main_app(directory: str, top_module: str, modules: List[Tuple[str, str]] = None) -> str
```

## Integration

The `process_chisel_project()` function now passes `modules` to all relevant functions:

```python
# Step 5: Generate main App with package detection
main_app = generate_main_app(directory, top_module, modules)

# Step 6: Configure build.sbt with smart discovery
build_sbt = configure_build_sbt(directory, top_module, modules)
```

## Testing

All tests pass:
```bash
# Basic tests
python test_chisel.py
# [SUCCESS] All tests passed!

# Multi-module tests
python test_chisel_multimodule.py
# [SUCCESS] All multi-module tests passed!
```

## Future Enhancements

- [ ] Handle SBT meta-build (project/build.sbt)
- [ ] Support for cross-compilation targets
- [ ] Detection of custom resolver configurations
- [ ] Integration with SBT build matrix
- [ ] Support for Mill build tool (alternative to SBT)
