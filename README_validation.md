# Configuration Validation Tools

This directory contains tools to validate the accuracy of the automated processor configuration generator by comparing its output with existing reference configurations.

## Overview

The validation system includes two main tools:

1. **`config_validator.py`** - Comprehensive validation with detailed reporting
2. **`quick_validator.py`** - Fast, user-friendly validation for quick testing

Both tools work by:
1. Loading reference configurations from the config folders
2. Running the config generator on the same repository
3. Comparing the generated config with the reference
4. Providing detailed similarity metrics and scores

## Tools

### config_validator.py

A comprehensive validation tool that provides detailed analysis and reporting.

**Features:**
- Batch validation of multiple processors
- Detailed similarity scoring for each configuration field
- Comprehensive reporting with statistics and analysis
- Support for both simulable and non-simulable processors
- Field-by-field performance analysis
- Common issues identification

**Usage:**
```bash
# Validate a single processor
python config_validator.py --processor tinyriscv

# Validate all simulable processors
python config_validator.py --batch-simulable

# Validate all non-simulable processors
python config_validator.py --batch-non-simulable

# Validate everything (both simulable and non-simulable)
python config_validator.py --validate-all

# Limit validation to first N processors (for testing)
python config_validator.py --batch-simulable --max-processors 5

# Custom output report file
python config_validator.py --batch-simulable --output-report my_report.json

# Use LLAMA for more accurate top module identification (slower)
python config_validator.py --processor tinyriscv --use-llama
```

**Output:**
- Console summary with scores and statistics
- Detailed JSON report with comprehensive analysis
- Top performers and problem cases identification
- Common issues analysis across all validations

### quick_validator.py

A streamlined tool for fast, user-friendly validation.

**Features:**
- Quick single processor validation
- Clean, readable output format
- Processor listing functionality
- Random sampling for quick testing
- Detailed analysis for low-scoring processors

**Usage:**
```bash
# Validate a single processor
python quick_validator.py tinyriscv

# List all simulable processors
python quick_validator.py --list-simulable

# List all processors (simulable and non-simulable)
python quick_validator.py --list-all

# Validate a random sample of processors
python quick_validator.py --sample 5
```

**Output Example:**
```
🎯 EXCELLENT tinyriscv: 1.000
   ✓ Perfect matches: top_module, files, include_dirs, language_version, sim_files, extra_flags, march, two_memory
```

## Scoring System

The validation system uses a weighted scoring approach:

### Field Weights
- **Top Module** (30%): Most critical - correct identification of the main module
- **Files** (25%): Very important - accurate file list for simulation
- **Include Directories** (15%): Important for compilation
- **Language Version** (10%): Verilog vs SystemVerilog detection
- **Sim Files** (10%): Testbench files
- **Extra Flags** (5%): Additional compiler flags
- **March** (3%): RISC-V architecture specification
- **Two Memory** (2%): Memory configuration flag

### Score Interpretation
- **≥0.9**: 🎯 EXCELLENT - Configuration is highly accurate
- **0.7-0.89**: ✅ GOOD - Minor differences, likely acceptable
- **0.5-0.69**: ⚠️ FAIR - Significant differences, needs review
- **<0.5**: ❌ POOR - Major issues, requires investigation

### Comparison Methods

#### Top Module Comparison
- Exact match: 1.0
- Same module name, different path: 0.9
- Partial name match: 0.7
- Fuzzy string similarity: 0.0-0.7

#### File List Comparison
- Uses Jaccard similarity coefficient
- Considers both exact path matches and basename matches
- Accounts for different directory structures

#### Include Directories
- Normalized path comparison
- Jaccard similarity for multiple directories

## Configuration Structure

The tools expect configurations in this structure:
```
config/
├── simulable/          # Processors that can be simulated
│   ├── tinyriscv.json
│   ├── picorv32.json
│   └── ...
└── non_simulable/      # Processors with compilation issues
    ├── cva6.json
    ├── rocket-chip.json
    └── ...
```

Each configuration file follows this format:
```json
{
    "name": "tinyriscv",
    "folder": "tinyriscv",
    "sim_files": ["tb/tinyriscv_soc_tb.v"],
    "files": ["rtl/core/tinyriscv.v", "rtl/utils/gen_dff.v"],
    "include_dirs": ["rtl/core"],
    "repository": "https://github.com/liangkangnan/tinyriscv.git",
    "top_module": "tinyriscv",
    "extra_flags": [],
    "language_version": "2005",
    "march": "rv32i",
    "two_memory": false
}
```

## Example Workflows

### Quick Check of a Specific Processor
```bash
# Check if the generator works correctly for a known good processor
python quick_validator.py tinyriscv
```

### Batch Validation for Quality Assessment
```bash
# Validate all simulable processors and generate a comprehensive report
python config_validator.py --batch-simulable --output-report simulable_validation.json
```

### Testing Configuration Changes
```bash
# Test a small sample to verify changes to the generator
python quick_validator.py --sample 3
```

### Comprehensive Analysis
```bash
# Full validation of all processors with detailed reporting
python config_validator.py --validate-all --output-report full_validation.json
```

## Report Analysis

The detailed JSON reports include:

### Summary Statistics
- Total processors validated
- Success/failure counts
- Average scores by category
- Distribution of score ranges

### Detailed Results
- Individual processor results with full comparison data
- Field-by-field scores and differences
- Missing/extra fields identification
- Error details for failed validations

### Performance Analysis
- Field performance statistics across all processors
- Common issues identification
- Top performers and problem cases
- Recommendations for improvement

### Example Report Usage
```python
import json

# Load validation report
with open('validation_report.json', 'r') as f:
    report = json.load(f)

# Check overall performance
avg_score = report['summary']['average_score']
print(f"Average validation score: {avg_score:.3f}")

# Find processors with low scores
problem_cases = [r for r in report['detailed_results'] 
                if 'overall_score' in r and r['overall_score'] < 0.5]
print(f"Processors needing attention: {len(problem_cases)}")

# Analyze common issues
common_issues = report['common_issues']
print(f"Top module mismatches: {common_issues['top_module_mismatches']}")
```

## Troubleshooting

### Common Issues

1. **ImportError**: Make sure you're running from the processor_ci directory
2. **File not found**: Ensure config directories exist and contain JSON files
3. **Repository access**: Some repos may require authentication or be unavailable
4. **Simulation failures**: Some processors may have compilation issues

### Performance Tips

- Use `--max-processors` to limit batch validations during testing
- The `--no-llama` flag is used by default for faster processing
- Use `quick_validator.py` for interactive testing
- Use `config_validator.py` for comprehensive analysis

### Debugging

For detailed debugging information, check:
- Console output during validation
- Log files in the `logs/` directory
- Temporary configuration files (paths shown in debug output)
- Simulation error messages in the output

## Future Enhancements

Potential improvements to the validation system:

1. **Regression Testing**: Automated validation in CI/CD pipelines
2. **Trend Analysis**: Track validation scores over time
3. **Configuration Suggestions**: Automatic fixes for common issues
4. **Custom Metrics**: Domain-specific validation criteria
5. **Interactive Dashboard**: Web interface for validation results
6. **Parallel Processing**: Faster batch validation using multiprocessing
