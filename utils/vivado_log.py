import re
from os import path
import json
import argparse
import sys
from datetime import datetime


def parse_vivado_utilization(filename, core, board):
    total_luts = None
    available_luts = None
    logic_luts = None
    memory_luts = None

    with open(filename, 'r') as f:
        content = f.read()

        luts_match = re.search(
            r'Slice LUTs\s+\|\s+(\d+)\s+\|[^|]+\|[^|]+\|\s+(\d+)', content
        )
        if luts_match:
            total_luts = int(luts_match.group(1))
            available_luts = int(luts_match.group(2))
        else:
            print(
                'Warning: It was not possible to find total and available LUTs'
            )

        logic_match = re.search(r'LUT as Logic\s+\|\s+(\d+)', content)
        if logic_match:
            logic_luts = int(logic_match.group(1))
        else:
            print('Warning: It was not possible to find logic LUTs')

        memory_match = re.search(r'LUT as Memory\s+\|\s+(\d+)', content)
        if memory_match:
            memory_luts = int(memory_match.group(1))
        else:
            print('Warning: It was not possible to find memory LUTs')

    results = {
        'processor': core,
        'board': board,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'luts': {
            # "available": available_luts,
            'used': total_luts,
            'logic': logic_luts,
            'memory': memory_luts,
        },
    }

    return results


def parse_vivado_timing(filename):
    with open(filename, 'r') as f:
        content = f.read()
        current_clock = re.search(
            r'sys_clk_pin\s+\S+\s+\S+\s+(\d+\.\d+)', content
        )
        slack = re.search(r'Slack \(MET\) :\s+(\d+\.\d+)', content)
        if current_clock and slack:
            current_clock = float(current_clock.group(1))
            slack = float(slack.group(1))
            required_period = current_clock - slack
            period = required_period * 10**-9
            frequency_mhz = int(1 / (period * 10**6))
        else:
            print('Warning: It was not possible to find minimum period')
            frequency_mhz = None

        results = {
            'max_freq_mhz': frequency_mhz,
        }

        return results


def write_results(results, output):
    if output in ['-', 'stdout']:
        json.dump(results, sys.stdout, indent=2)
        return True
    elif '/' in output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        return True
    else:
        if path.isdir('/eda/synth_results'):
            output = f'/eda/synth_results/{output}'
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
            return True
        else:
            print('Error: Directory /eda/synth_results does not exist')
            return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Parse Vivado utilization report for synthesis information'
    )
    parser.add_argument('--timing-file', '-t')
    parser.add_argument('--utilization-file', '-u')
    parser.add_argument(
        '--directory', '-d', help='Directory to read files', default='.'
    )
    parser.add_argument(
        '--board',
        '-b',
        help='Board name',
        required=True,
    )
    parser.add_argument(
        '--core',
        '-c',
        help='Core name',
        required=True,
    )
    parser.add_argument(
        '--output-folder',
        '-o',
        default='.',
        help='Output folder',
    )
    args = parser.parse_args()
    if not args.timing_file:
        args.timing_file = f'{args.board}_timing.rpt'
    if not args.utilization_file:
        args.utilization_file = f'{args.board}_utilization_place.rpt'

    area_results = parse_vivado_utilization(
        path.join(args.directory, args.utilization_file), args.core, args.board
    )
    timing_results = parse_vivado_timing(
        path.join(args.directory, args.timing_file)
    )
    results = {**area_results, **timing_results}

    # test if all values are present
    if not all(results.values()):
        print('Error: Some values are missing')
        sys.exit(1)

    out = write_results(
        results,
        path.join(args.output_folder, f'synth_{args.core}_{args.board}.json'),
    )
