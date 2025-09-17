#!/usr/bin/env python3
"""
Quick Configuration Comparison Tool

A simplified tool for quickly comparing generated configurations with reference configs.
Useful for spot-checking individual processors or running small batch validations.

Usage:
------
python quick_validator.py tinyriscv          # Validate a single processor
python quick_validator.py --list-simulable  # List all simulable processors  
python quick_validator.py --list-all        # List all processors
python quick_validator.py --sample 5        # Validate a random sample of 5 processors
"""

import argparse
import json
import random
import sys
from pathlib import Path
from config_validator import ConfigValidator
from core.log import print_green, print_red, print_yellow


def print_comparison_summary(result):
    """Print a compact summary of a single validation result."""
    if 'error' in result:
        print_red(f"❌ {result.get('processor_name', 'Unknown')}: ERROR - {result['error']}")
        return
    
    name = result['processor_name']
    score = result['overall_score']
    
    # Score interpretation
    if score >= 0.9:
        status = "🎯 EXCELLENT"
        color_func = print_green
    elif score >= 0.7:
        status = "✅ GOOD"
        color_func = print_green
    elif score >= 0.5:
        status = "⚠️  FAIR"
        color_func = print_yellow
    else:
        status = "❌ POOR"
        color_func = print_red
    
    color_func(f"{status} {name}: {score:.3f}")
    
    # Show key differences
    if 'differences' in result and result['differences']:
        print("   Issues:")
        for field, diff in result['differences'].items():
            if field == 'top_module':
                print(f"     • Top module: got '{diff['generated']}', expected '{diff['reference']}'")
            elif field == 'files':
                gen_count = len(diff['generated']) if isinstance(diff['generated'], list) else 0
                ref_count = len(diff['reference']) if isinstance(diff['reference'], list) else 0
                print(f"     • Files: got {gen_count}, expected {ref_count} (score: {diff['score']:.2f})")
            elif field == 'include_dirs':
                print(f"     • Include dirs mismatch (score: {diff['score']:.2f})")
            else:
                print(f"     • {field}: mismatch (score: {diff['score']:.2f})")
    
    if 'matches' in result and result['matches']:
        matches = [k for k, v in result['matches'].items() if v]
        if matches:
            print(f"   ✓ Perfect matches: {', '.join(matches)}")


def list_processors(validator, simulable_only=True):
    """List available processors."""
    if simulable_only:
        simulable = validator.get_processor_list(is_simulable=True)
        print_green(f"Simulable processors ({len(simulable)}):")
        for i, proc in enumerate(simulable, 1):
            print(f"  {i:2d}. {proc}")
    else:
        simulable = validator.get_processor_list(is_simulable=True)
        non_simulable = validator.get_processor_list(is_simulable=False)
        
        print_green(f"Simulable processors ({len(simulable)}):")
        for i, proc in enumerate(simulable, 1):
            print(f"  {i:2d}. {proc}")
        
        print_yellow(f"\nNon-simulable processors ({len(non_simulable)}):")
        for i, proc in enumerate(non_simulable, 1):
            print(f"  {i:2d}. {proc}")


def validate_single(validator, processor_name):
    """Validate a single processor and show detailed results."""
    print_green(f"🔍 Validating {processor_name}...")
    
    # Determine if processor is simulable or not
    simulable_list = validator.get_processor_list(is_simulable=True)
    non_simulable_list = validator.get_processor_list(is_simulable=False)
    
    if processor_name in simulable_list:
        is_simulable = True
        print(f"   Type: Simulable")
    elif processor_name in non_simulable_list:
        is_simulable = False
        print(f"   Type: Non-simulable")
    else:
        print_red(f"❌ Processor '{processor_name}' not found in config directories")
        return False
    
    result = validator.validate_processor(processor_name, is_simulable, no_llama=True)
    print_comparison_summary(result)
    
    # Show more details if score is low
    if 'overall_score' in result and result['overall_score'] < 0.7:
        print("\n📊 Detailed Analysis:")
        if 'field_scores' in result:
            for field, score in result['field_scores'].items():
                status = "✓" if score >= 0.9 else "⚠" if score >= 0.5 else "✗"
                print(f"   {status} {field:15}: {score:.3f}")
    
    return True


def validate_sample(validator, sample_size):
    """Validate a random sample of processors."""
    simulable = validator.get_processor_list(is_simulable=True)
    sample_processors = random.sample(simulable, min(sample_size, len(simulable)))
    
    print_green(f"🎲 Randomly selected {len(sample_processors)} processors:")
    for proc in sample_processors:
        print(f"   • {proc}")
    print()
    
    results = []
    for i, proc in enumerate(sample_processors, 1):
        print_green(f"[{i}/{len(sample_processors)}] Validating {proc}...")
        result = validator.validate_processor(proc, is_simulable=True, no_llama=True)
        results.append(result)
        print_comparison_summary(result)
        print()
    
    # Summary stats
    valid_results = [r for r in results if 'overall_score' in r]
    if valid_results:
        avg_score = sum(r['overall_score'] for r in valid_results) / len(valid_results)
        good_count = len([r for r in valid_results if r['overall_score'] >= 0.7])
        
        print_green("📈 Sample Summary:")
        print(f"   Average Score: {avg_score:.3f}")
        print(f"   Good Results (≥0.7): {good_count}/{len(valid_results)}")
        print(f"   Success Rate: {good_count/len(valid_results)*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Quick configuration validation tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quick_validator.py tinyriscv          # Validate tinyriscv
  python quick_validator.py --list-simulable  # List simulable processors
  python quick_validator.py --sample 3        # Test 3 random processors
        """
    )
    
    parser.add_argument(
        'processor',
        nargs='?',
        help='Processor name to validate'
    )
    
    parser.add_argument(
        '--list-simulable',
        action='store_true',
        help='List all simulable processors'
    )
    
    parser.add_argument(
        '--list-all',
        action='store_true',
        help='List all processors (simulable and non-simulable)'
    )
    
    parser.add_argument(
        '--sample',
        type=int,
        metavar='N',
        help='Validate N random simulable processors'
    )
    
    parser.add_argument(
        '--config-path',
        default='config',
        help='Path to configuration directory (default: config)'
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = ConfigValidator(args.config_path)
    
    try:
        if args.list_simulable:
            list_processors(validator, simulable_only=True)
        elif args.list_all:
            list_processors(validator, simulable_only=False)
        elif args.sample:
            validate_sample(validator, args.sample)
        elif args.processor:
            validate_single(validator, args.processor)
        else:
            print_red("Please specify a processor name or use --help for options")
            return 1
            
    except KeyboardInterrupt:
        print_yellow("\n⏹️  Validation interrupted by user")
        return 1
    except Exception as e:
        print_red(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
