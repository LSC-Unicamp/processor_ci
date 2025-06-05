import re
import sys


def detect_language(text):
    if 'entity' in text and 'port' in text:
        return 'vhdl'
    if 'module' in text:
        return 'verilog'
    return 'unknown'


# --- VHDL Parsing ---
def parse_vhdl_generics(text):
    generics = []
    generic_block = re.search(
        r'generic\s*\((.*?)\);\s*port', text, re.DOTALL | re.IGNORECASE
    )
    if not generic_block:
        return generics

    for line in generic_block.group(1).splitlines():
        line = line.strip().rstrip(';')
        match = re.match(r'(\w+)\s*:\s*\w+\s*:=\s*(.+)', line)
        if match:
            name = match.group(1)
            default_value = match.group(2).strip()
            generics.append((name, default_value))
    return generics


def parse_vhdl_ports(text):
    ports = []
    port_block = re.search(
        r'port\s*\((.*?)\);\s*end', text, re.DOTALL | re.IGNORECASE
    )
    if not port_block:
        return ports

    for line in port_block.group(1).splitlines():
        line = line.strip().rstrip(';')
        match = re.match(
            r'(\w+)\s*:\s*(in|out)\s+(std_logic|std_logic_vector\((.*?)\))',
            line,
            re.IGNORECASE,
        )
        if match:
            name = match.group(1)
            direction = 'input' if match.group(2).lower() == 'in' else 'output'
            width = match.group(4)
            if width:
                range_match = re.match(
                    r'(\d+)\s+downto\s+(\d+)', width, re.IGNORECASE
                )
                if range_match:
                    msb = int(range_match.group(1))
                    lsb = int(range_match.group(2))
                    width_str = f'[{msb}:{lsb}]'
                else:
                    width_str = '[0:0]'
            else:
                width_str = '[0:0]'
            ports.append((direction, width_str, name))
    return ports


# --- Verilog Parsing ---
def parse_sv_params(text):
    params = []
    param_block = re.search(r'#\s*\((.*?)\)\s*\(', text, re.DOTALL)
    if not param_block:
        return params

    for line in param_block.group(1).splitlines():
        line = line.strip().rstrip(',')
        match = re.match(r'parameter\s+(\w+)\s*=\s*([^,]+)', line)
        if match:
            name = match.group(1)
            value = match.group(2).strip()
            params.append((name, value))
    return params


def parse_sv_ports(text):
    ports = []
    inside_ports = False
    for line in text.splitlines():
        line = line.strip().rstrip(',')
        if '(' in line and 'input' not in line and 'output' not in line:
            inside_ports = True
            continue
        if inside_ports and line.startswith(');'):
            break
        match = re.match(
            r'(input|output)\s+(?:logic|wire|bit|reg)?\s*(\[[^\]]+\])?\s*([\w\d_]+)',
            line,
        )
        if match:
            direction = match.group(1)
            width = match.group(2) if match.group(2) else '[0:0]'
            name = match.group(3)
            ports.append((direction, width, name))
    return ports


# --- Utilities ---
def width_comment(width):
    if width == '[0:0]':
        return '1 bit'
    match = re.match(r'\[(\d+):(\d+)\]', width)
    if match:
        msb = int(match.group(1))
        lsb = int(match.group(2))
        return f'{abs(msb - lsb) + 1} bits'
    return '? bits'


def generate_instance(module_name, ports, params=[]):
    instance = ''
    if params:
        instance += f'{module_name} #(\n'
        for name, value in params:
            instance += f'    .{name:<20} ({value}),\n'
        instance = instance.rstrip(',\n') + '\n) '
    else:
        instance += f'{module_name} '

    instance += f'u_{module_name} (\n'
    for direction, width, name in ports:
        comment = width_comment(width)
        instance += (
            f"    .{name:<20} ({name}),{' '*(30 - len(name))}// {comment}\n"
        )
    instance = instance.rstrip(',\n') + '\n);'
    return instance


# --- Main ---
def main():
    if len(sys.argv) < 2:
        print('Uso: python inst_gen_all.py <arquivo.vhd | .sv | .v>')
        return

    filename = sys.argv[1]
    with open(filename, 'r') as f:
        content = f.read()

    lang = detect_language(content)
    if lang == 'verilog':
        mod_match = re.search(r'module\s+(\w+)', content)
        if not mod_match:
            print('Módulo Verilog não encontrado.')
            return
        module_name = mod_match.group(1)
        ports = parse_sv_ports(content)
        params = parse_sv_params(content)

    elif lang == 'vhdl':
        ent_match = re.search(r'entity\s+(\w+)', content, re.IGNORECASE)
        if not ent_match:
            print('Entidade VHDL não encontrada.')
            return
        module_name = ent_match.group(1)
        ports = parse_vhdl_ports(content)
        params = parse_vhdl_generics(content)

    else:
        print('Formato de código não reconhecido (esperado: Verilog ou VHDL).')
        return

    print(generate_instance(module_name, ports, params))


if __name__ == '__main__':
    main()
