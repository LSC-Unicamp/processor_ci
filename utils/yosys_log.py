import re
from os import path
import json
import argparse
import sys
from datetime import datetime


def parse_nextpnr_log(filename, core, board):
    total_luts = None
    available_luts = None
    logic_luts = None
    carry_luts = None
    max_freq = None

    with open(filename, 'r') as f:
        content = f.read()

        luts_match = re.search(r'Total LUT4s:\s+(\d+)/(\d+)\s', content)
        if luts_match:
            total_luts = int(luts_match.group(1))
            available_luts = int(luts_match.group(2))
        else:
            print('Warning: It was not possible to find LUTs')

        luts_logic_match = re.search(r'logic LUTs:\s+(\d+)/\d+', content)
        if luts_logic_match:
            logic_luts = int(luts_logic_match.group(1))
        else:
            print('Warning: It was not possible to find logic LUTs')

        luts_carry_match = re.search(r'carry LUTs:\s+(\d+)/\d+', content)
        if luts_carry_match:
            carry_luts = int(luts_carry_match.group(1))
        else:
            print('Warning: It was not possible to find carry LUTs')

        freq_match = re.findall(
            r'Max frequency for clock .+?: (\d+\.\d+) MHz', content
        )
        if freq_match:
            max_freq = float(freq_match[-1])
        else:
            print('Warning: It was not possible to find max frequency')

    results = {
        'processor': core,
        'board': board,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'luts': {
            # "available": available_luts,
            'used': total_luts,
            'logic': logic_luts,
            'carry': carry_luts,
        },
        'max_freq_mhz': max_freq,
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
        description='Parse nextpnr log file for synthesis information'
    )
    parser.add_argument(
        '--directory',
        '-d',
        default='.',
        help='Directory where the log file is',
    )
    parser.add_argument('--board', '-b', help='Board name', required=True)
    parser.add_argument('--core', '-c', help='Core name', required=True)
    parser.add_argument(
        '--output-folder',
        '-o',
        default='.',
        help='Output folder',
    )
    args = parser.parse_args()
    input = path.join(args.directory, f'{args.board}_synth_out.txt')

    results = parse_nextpnr_log(
        input,
        args.core,
        args.board,
    )

    if not all(results.values()):
        print('Error: Some information could not be found')
        sys.exit(1)

    output = path.join(
        args.output_folder, f'synth_{args.core}_{args.board}.json'
    )

    out = write_results(results, output)
