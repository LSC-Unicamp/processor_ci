#!/usr/bin/env python3
"""
Configuration Validator

This script validates the config generator by comparing its output with existing configurations.
It helps assess the accuracy of the automated configuration generation process.

Features:
- Compares generated configs with existing reference configs
- Provides detailed similarity metrics and scoring
- Generates comprehensive reports on accuracy
- Supports batch validation of multiple processors
- Identifies common patterns in mismatches

Usage:
------
python config_validator.py --validate-all
python config_validator.py --processor tinyriscv
python config_validator.py --batch-simulable
python config_validator.py --batch-non-simulable
"""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import difflib

# Import from the config generator
from config_generator_core import generate_processor_config
from core.log import print_green, print_red, print_yellow


class ConfigValidator:
    """Validates configuration generation accuracy by comparing with reference configs."""
    
    def __init__(self, config_base_path: str = "config"):
        self.config_base_path = Path(config_base_path)
        self.simulable_path = self.config_base_path / "simulable"
        self.non_simulable_path = self.config_base_path / "non_simulable"
        self.results = []
        
    def load_reference_config(self, processor_name: str, is_simulable: bool = True) -> Dict:
        """Load the reference configuration for a processor."""
        folder = "simulable" if is_simulable else "non_simulable"
        config_path = self.config_base_path / folder / f"{processor_name}.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Reference config not found: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_repo_url(self, reference_config: Dict) -> str:
        """Extract repository URL from reference config."""
        return reference_config.get('repository', '')
    
    def compare_configs(self, generated: Dict, reference: Dict) -> Dict:
        """Compare generated config with reference config and return detailed metrics."""
        comparison = {
            'processor_name': reference.get('name', 'unknown'),
            'overall_score': 0.0,
            'field_scores': {},
            'matches': {},
            'differences': {},
            'missing_fields': [],
            'extra_fields': [],
            'detailed_analysis': {}
        }
        
        # Define field weights for scoring
        field_weights = {
            'top_module': 0.3,      # Most important
            'files': 0.25,          # Very important
            'include_dirs': 0.15,   # Important
            'language_version': 0.1,
            'sim_files': 0.1,
            'extra_flags': 0.05,
            'march': 0.03,
            'two_memory': 0.02
        }
        
        total_score = 0.0
        
        for field, weight in field_weights.items():
            if field in reference:
                if field in generated:
                    score = self._compare_field(field, generated[field], reference[field])
                    comparison['field_scores'][field] = score
                    total_score += score * weight
                    
                    if score == 1.0:
                        comparison['matches'][field] = True
                    else:
                        comparison['differences'][field] = {
                            'generated': generated[field],
                            'reference': reference[field],
                            'score': score
                        }
                else:
                    comparison['missing_fields'].append(field)
                    comparison['field_scores'][field] = 0.0
            else:
                # Field not in reference but in generated
                if field in generated:
                    comparison['extra_fields'].append(field)
        
        # Check for extra fields in generated config
        for field in generated:
            if field not in reference and field not in comparison['extra_fields']:
                comparison['extra_fields'].append(field)
        
        comparison['overall_score'] = total_score
        comparison['detailed_analysis'] = self._detailed_analysis(generated, reference)
        
        return comparison
    
    def _compare_field(self, field_name: str, generated_value: Any, reference_value: Any) -> float:
        """Compare a specific field and return similarity score (0.0 to 1.0)."""
        if generated_value == reference_value:
            return 1.0
        
        if field_name == 'top_module':
            return self._compare_top_module(generated_value, reference_value)
        elif field_name == 'files':
            return self._compare_file_lists(generated_value, reference_value)
        elif field_name == 'include_dirs':
            return self._compare_path_lists(generated_value, reference_value)
        elif field_name == 'sim_files':
            return self._compare_file_lists(generated_value, reference_value)
        elif field_name in ['language_version', 'march']:
            return 1.0 if str(generated_value) == str(reference_value) else 0.0
        elif field_name == 'extra_flags':
            return self._compare_lists(generated_value, reference_value)
        elif field_name == 'two_memory':
            return 1.0 if bool(generated_value) == bool(reference_value) else 0.0
        else:
            return 1.0 if generated_value == reference_value else 0.0
    
    def _compare_top_module(self, generated: str, reference: str) -> float:
        """Compare top module names with fuzzy matching."""
        if generated == reference:
            return 1.0
        
        # Extract module names (remove path if present)
        gen_module = os.path.basename(generated) if '/' in generated else generated
        ref_module = os.path.basename(reference) if '/' in reference else reference
        
        if gen_module == ref_module:
            return 0.9  # Same module name, different path
        
        # Check if one is contained in the other
        if gen_module.lower() in ref_module.lower() or ref_module.lower() in gen_module.lower():
            return 0.7
        
        # Use sequence matching for similarity
        matcher = difflib.SequenceMatcher(None, gen_module.lower(), ref_module.lower())
        similarity = matcher.ratio()
        
        return max(0.0, similarity - 0.3)  # Penalize low similarities
    
    def _compare_file_lists(self, generated: List[str], reference: List[str]) -> float:
        """Compare file lists with path normalization."""
        if not reference:  # Empty reference list
            return 1.0 if not generated else 0.5
        
        if not generated:  # Empty generated list
            return 0.0
        
        # Normalize paths
        gen_files = {os.path.normpath(f) for f in generated}
        ref_files = {os.path.normpath(f) for f in reference}
        
        # Exact match
        if gen_files == ref_files:
            return 1.0
        
        # Calculate Jaccard similarity
        intersection = len(gen_files & ref_files)
        union = len(gen_files | ref_files)
        
        if union == 0:
            return 1.0
        
        jaccard = intersection / union
        
        # Also consider basename matches (files with same name but different paths)
        gen_basenames = {os.path.basename(f) for f in generated}
        ref_basenames = {os.path.basename(f) for f in reference}
        
        basename_intersection = len(gen_basenames & ref_basenames)
        basename_union = len(gen_basenames | ref_basenames)
        basename_jaccard = basename_intersection / basename_union if basename_union > 0 else 0
        
        # Return weighted combination
        return 0.7 * jaccard + 0.3 * basename_jaccard
    
    def _compare_path_lists(self, generated: List[str], reference: List[str]) -> float:
        """Compare path lists (include directories)."""
        if not reference:
            return 1.0 if not generated else 0.5
        
        if not generated:
            return 0.0
        
        gen_paths = {os.path.normpath(p) for p in generated}
        ref_paths = {os.path.normpath(p) for p in reference}
        
        if gen_paths == ref_paths:
            return 1.0
        
        intersection = len(gen_paths & ref_paths)
        union = len(gen_paths | ref_paths)
        
        return intersection / union if union > 0 else 0.0
    
    def _compare_lists(self, generated: List, reference: List) -> float:
        """Compare generic lists."""
        if not reference:
            return 1.0 if not generated else 0.5
        
        if not generated:
            return 0.0
        
        gen_set = set(generated)
        ref_set = set(reference)
        
        if gen_set == ref_set:
            return 1.0
        
        intersection = len(gen_set & ref_set)
        union = len(gen_set | ref_set)
        
        return intersection / union if union > 0 else 0.0
    
    def _detailed_analysis(self, generated: Dict, reference: Dict) -> Dict:
        """Provide detailed analysis of the comparison."""
        analysis = {
            'file_analysis': {},
            'recommendations': [],
            'critical_issues': []
        }
        
        # Analyze files in detail
        if 'files' in generated and 'files' in reference:
            gen_files = set(generated['files'])
            ref_files = set(reference['files'])
            
            analysis['file_analysis'] = {
                'only_in_generated': list(gen_files - ref_files),
                'only_in_reference': list(ref_files - gen_files),
                'common_files': list(gen_files & ref_files),
                'total_generated': len(gen_files),
                'total_reference': len(ref_files)
            }
        
        # Generate recommendations
        if 'top_module' in generated and 'top_module' in reference:
            if generated['top_module'] != reference['top_module']:
                analysis['critical_issues'].append(
                    f"Top module mismatch: generated '{generated['top_module']}' vs reference '{reference['top_module']}'"
                )
        
        return analysis
    
    def validate_processor(self, processor_name: str, is_simulable: bool = True, 
                          use_cache: bool = False, no_llama: bool = True) -> Dict:
        """Validate a single processor configuration."""
        print_green(f"[VALIDATOR] Validating processor: {processor_name}")
        
        try:
            # Load reference configuration
            reference_config = self.load_reference_config(processor_name, is_simulable)
            repo_url = self.extract_repo_url(reference_config)
            
            if not repo_url:
                print_red(f"[ERROR] No repository URL found for {processor_name}")
                return {'error': 'No repository URL'}
            
            print_green(f"[VALIDATOR] Repository URL: {repo_url}")
            
            # Generate configuration using the config generator
            print_green(f"[VALIDATOR] Generating configuration for {processor_name}...")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    generated_config = generate_processor_config(
                        url=repo_url,
                        config_path=temp_dir,
                        plot_graph=False,
                        add_to_config=False,
                        no_llama=no_llama,
                        model='qwen2.5:32b'
                    )
                    
                    if not generated_config:
                        print_red(f"[ERROR] Failed to generate config for {processor_name}")
                        return {'error': 'Generation failed'}
                    
                    # Compare configurations
                    comparison = self.compare_configs(generated_config, reference_config)
                    comparison['processor_name'] = processor_name
                    comparison['is_simulable'] = is_simulable
                    comparison['repository'] = repo_url
                    comparison['validation_time'] = time.time()
                    
                    print_green(f"[VALIDATOR] Validation complete for {processor_name}")
                    print_green(f"[VALIDATOR] Overall score: {comparison['overall_score']:.2f}")
                    
                    return comparison
                    
                except Exception as e:
                    print_red(f"[ERROR] Exception during config generation for {processor_name}: {e}")
                    return {'error': str(e), 'processor_name': processor_name}
                    
        except FileNotFoundError as e:
            print_red(f"[ERROR] Reference config not found for {processor_name}: {e}")
            return {'error': 'Reference config not found', 'processor_name': processor_name}
        except Exception as e:
            print_red(f"[ERROR] Unexpected error validating {processor_name}: {e}")
            return {'error': str(e), 'processor_name': processor_name}
    
    def validate_batch(self, processor_list: List[str], is_simulable: bool = True, 
                      max_processors: int = None) -> List[Dict]:
        """Validate multiple processors in batch."""
        print_green(f"[VALIDATOR] Starting batch validation of {len(processor_list)} processors")
        
        if max_processors:
            processor_list = processor_list[:max_processors]
            print_yellow(f"[VALIDATOR] Limited to first {max_processors} processors")
        
        results = []
        
        for i, processor_name in enumerate(processor_list, 1):
            print_green(f"\n[VALIDATOR] Progress: {i}/{len(processor_list)} - {processor_name}")
            
            # Remove .json extension if present
            clean_name = processor_name.replace('.json', '')
            
            result = self.validate_processor(clean_name, is_simulable)
            results.append(result)
            
            # Brief summary
            if 'overall_score' in result:
                score = result['overall_score']
                status = "✅ GOOD" if score > 0.8 else "⚠️  FAIR" if score > 0.5 else "❌ POOR"
                print_green(f"[VALIDATOR] {processor_name}: {score:.2f} {status}")
            else:
                print_red(f"[VALIDATOR] {processor_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        return results
    
    def get_processor_list(self, is_simulable: bool = True) -> List[str]:
        """Get list of processors from config directory."""
        folder = self.simulable_path if is_simulable else self.non_simulable_path
        
        if not folder.exists():
            print_red(f"[ERROR] Config folder not found: {folder}")
            return []
        
        json_files = list(folder.glob("*.json"))
        processor_names = [f.stem for f in json_files]
        
        print_green(f"[VALIDATOR] Found {len(processor_names)} processors in {folder}")
        return sorted(processor_names)
    
    def generate_report(self, results: List[Dict], output_file: str = None) -> None:
        """Generate a comprehensive validation report."""
        if not results:
            print_red("[VALIDATOR] No results to report")
            return
        
        # Filter out error results for statistics
        valid_results = [r for r in results if 'overall_score' in r]
        error_results = [r for r in results if 'error' in r]
        
        report = {
            'summary': {
                'total_processors': len(results),
                'successful_validations': len(valid_results),
                'failed_validations': len(error_results),
                'average_score': sum(r['overall_score'] for r in valid_results) / len(valid_results) if valid_results else 0,
                'high_scores': len([r for r in valid_results if r['overall_score'] > 0.8]),
                'medium_scores': len([r for r in valid_results if 0.5 < r['overall_score'] <= 0.8]),
                'low_scores': len([r for r in valid_results if r['overall_score'] <= 0.5])
            },
            'detailed_results': results,
            'top_performers': sorted(valid_results, key=lambda x: x['overall_score'], reverse=True)[:10],
            'problem_cases': sorted(valid_results, key=lambda x: x['overall_score'])[:10],
            'common_issues': self._analyze_common_issues(valid_results),
            'field_performance': self._analyze_field_performance(valid_results)
        }
        
        # Print summary to console
        print_green("\n" + "="*80)
        print_green("VALIDATION REPORT SUMMARY")
        print_green("="*80)
        print_green(f"Total Processors: {report['summary']['total_processors']}")
        print_green(f"Successful Validations: {report['summary']['successful_validations']}")
        print_green(f"Failed Validations: {report['summary']['failed_validations']}")
        print_green(f"Average Score: {report['summary']['average_score']:.3f}")
        print_green(f"High Scores (>0.8): {report['summary']['high_scores']}")
        print_green(f"Medium Scores (0.5-0.8): {report['summary']['medium_scores']}")
        print_green(f"Low Scores (≤0.5): {report['summary']['low_scores']}")
        
        if report['top_performers']:
            print_green("\nTOP PERFORMERS:")
            for i, result in enumerate(report['top_performers'][:5], 1):
                print_green(f"  {i}. {result['processor_name']}: {result['overall_score']:.3f}")
        
        if report['problem_cases']:
            print_yellow("\nPROBLEM CASES:")
            for i, result in enumerate(report['problem_cases'][:5], 1):
                print_yellow(f"  {i}. {result['processor_name']}: {result['overall_score']:.3f}")
        
        # Save detailed report to file
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            print_green(f"\n[VALIDATOR] Detailed report saved to: {output_file}")
        
        return report
    
    def _analyze_common_issues(self, results: List[Dict]) -> Dict:
        """Analyze common issues across validations."""
        issues = {
            'top_module_mismatches': 0,
            'file_list_issues': 0,
            'include_dir_issues': 0,
            'language_version_issues': 0,
            'missing_fields': {},
            'low_scores_by_field': {}
        }
        
        for result in results:
            if 'differences' in result:
                if 'top_module' in result['differences']:
                    issues['top_module_mismatches'] += 1
                if 'files' in result['differences']:
                    issues['file_list_issues'] += 1
                if 'include_dirs' in result['differences']:
                    issues['include_dir_issues'] += 1
                if 'language_version' in result['differences']:
                    issues['language_version_issues'] += 1
            
            if 'missing_fields' in result:
                for field in result['missing_fields']:
                    issues['missing_fields'][field] = issues['missing_fields'].get(field, 0) + 1
            
            if 'field_scores' in result:
                for field, score in result['field_scores'].items():
                    if score < 0.5:
                        issues['low_scores_by_field'][field] = issues['low_scores_by_field'].get(field, 0) + 1
        
        return issues
    
    def _analyze_field_performance(self, results: List[Dict]) -> Dict:
        """Analyze performance by field across all validations."""
        field_stats = {}
        
        for result in results:
            if 'field_scores' in result:
                for field, score in result['field_scores'].items():
                    if field not in field_stats:
                        field_stats[field] = []
                    field_stats[field].append(score)
        
        field_performance = {}
        for field, scores in field_stats.items():
            field_performance[field] = {
                'average_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'perfect_matches': len([s for s in scores if s == 1.0]),
                'total_cases': len(scores)
            }
        
        return field_performance


def main():
    """Main entry point for the configuration validator."""
    parser = argparse.ArgumentParser(description='Validate processor configurations')
    
    parser.add_argument(
        '--processor',
        type=str,
        help='Validate a specific processor by name'
    )
    
    parser.add_argument(
        '--batch-simulable',
        action='store_true',
        help='Validate all simulable processors'
    )
    
    parser.add_argument(
        '--batch-non-simulable', 
        action='store_true',
        help='Validate all non-simulable processors'
    )
    
    parser.add_argument(
        '--validate-all',
        action='store_true',
        help='Validate all processors (both simulable and non-simulable)'
    )
    
    parser.add_argument(
        '--max-processors',
        type=int,
        help='Maximum number of processors to validate (for testing)'
    )
    
    parser.add_argument(
        '--output-report',
        type=str,
        default='validation_report.json',
        help='Output file for detailed validation report'
    )
    
    parser.add_argument(
        '--config-path',
        type=str,
        default='config',
        help='Path to configuration directory'
    )
    
    parser.add_argument(
        '--use-llama',
        action='store_true',
        help='Use LLAMA for top module identification (slower but potentially more accurate)'
    )
    
    args = parser.parse_args()
    
    # Create validator instance
    validator = ConfigValidator(args.config_path)
    
    all_results = []
    
    try:
        if args.processor:
            # Validate single processor
            # Check if it's simulable or non-simulable
            simulable_list = validator.get_processor_list(is_simulable=True)
            non_simulable_list = validator.get_processor_list(is_simulable=False)
            
            if args.processor in simulable_list:
                result = validator.validate_processor(args.processor, is_simulable=True, no_llama=not args.use_llama)
                all_results.append(result)
            elif args.processor in non_simulable_list:
                result = validator.validate_processor(args.processor, is_simulable=False, no_llama=not args.use_llama)
                all_results.append(result)
            else:
                print_red(f"[ERROR] Processor '{args.processor}' not found in config directories")
                return 1
                
        elif args.batch_simulable:
            # Validate all simulable processors
            simulable_list = validator.get_processor_list(is_simulable=True)
            results = validator.validate_batch(simulable_list, is_simulable=True, max_processors=args.max_processors)
            all_results.extend(results)
            
        elif args.batch_non_simulable:
            # Validate all non-simulable processors  
            non_simulable_list = validator.get_processor_list(is_simulable=False)
            results = validator.validate_batch(non_simulable_list, is_simulable=False, max_processors=args.max_processors)
            all_results.extend(results)
            
        elif args.validate_all:
            # Validate all processors
            simulable_list = validator.get_processor_list(is_simulable=True)
            non_simulable_list = validator.get_processor_list(is_simulable=False)
            
            if args.max_processors:
                total_limit = args.max_processors
                sim_limit = min(len(simulable_list), total_limit // 2)
                non_sim_limit = min(len(non_simulable_list), total_limit - sim_limit)
            else:
                sim_limit = non_sim_limit = None
            
            print_green("[VALIDATOR] Validating simulable processors...")
            sim_results = validator.validate_batch(simulable_list, is_simulable=True, max_processors=sim_limit)
            all_results.extend(sim_results)
            
            print_green("[VALIDATOR] Validating non-simulable processors...")
            non_sim_results = validator.validate_batch(non_simulable_list, is_simulable=False, max_processors=non_sim_limit)
            all_results.extend(non_sim_results)
            
        else:
            print_red("[ERROR] Please specify what to validate. Use --help for options.")
            return 1
        
        # Generate comprehensive report
        if all_results:
            validator.generate_report(all_results, args.output_report)
        else:
            print_red("[ERROR] No validation results to report")
            return 1
            
    except KeyboardInterrupt:
        print_yellow("\n[VALIDATOR] Validation interrupted by user")
        if all_results:
            print_green("[VALIDATOR] Generating report for completed validations...")
            validator.generate_report(all_results, args.output_report)
        return 1
    except Exception as e:
        print_red(f"[ERROR] Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
