import re


def generate_instance(code: str, mapping: dict, instance_name="u_instancia"):
    """
    Gera uma instância em formato Verilog a partir de um módulo Verilog/SystemVerilog ou entidade VHDL.
    Inclui parâmetros/generics com valores default.

    Regras:
      - Entradas sem correspondência -> 1'b0
      - Saídas ou inouts sem correspondência -> ()
      - Parâmetros / generics -> incluídos com valor default, se existirem
    """

    # Detectar linguagem
    is_vhdl = bool(re.search(r"\bentity\b", code, re.IGNORECASE))
    is_verilog = bool(re.search(r"\bmodule\b", code))

    if not (is_vhdl or is_verilog):
        raise ValueError(
            "Não foi possível identificar se é Verilog/SystemVerilog ou VHDL."
        )

    reverse_map = {v: k for k, v in mapping.items()}
    ports = []
    params = []
    module_name = "unknown_module"

    # --------------------------
    # VERILOG / SYSTEMVERILOG
    # --------------------------
    if is_verilog:
        m = re.search(r"\bmodule\s+(\w+)", code)
        if m:
            module_name = m.group(1)

        # Capturar parâmetros/defines com valor default
        param_block = re.search(r"#\s*\((.*?)\)\s*\(", code, re.DOTALL)
        if param_block:
            param_lines = re.findall(
                r"parameter\s+(\w+)\s*=\s*([^,\n)]+)", param_block.group(1)
            )
            for name, value in param_lines:
                params.append((name.strip(), value.strip()))

        # Capturar todas as declarações de porta
        ports_raw = re.findall(r"\b(input|output|inout)\b[^;]*;", code)
        for decl in ports_raw:
            direction = re.match(r"(input|output|inout)", decl).group(1)
            # Pegar nomes de sinais (suporta múltiplos por linha)
            names = re.findall(r"(\w+)\s*(?:,|;)", decl)
            for n in names:
                ports.append((direction, n))

    # --------------------------
    # VHDL
    # --------------------------
    else:
        m = re.search(r"\bentity\s+(\w+)\b", code, re.IGNORECASE)
        if m:
            module_name = m.group(1)

        # Extrair generics (parâmetros)
        generic_match = re.search(
            r"generic\s*\((.*?)\)\s*;", code, re.DOTALL | re.IGNORECASE
        )
        if generic_match:
            generics = re.findall(
                r"(\w+)\s*:\s*.*?:=\s*([^;]+);?", generic_match.group(1)
            )
            for name, val in generics:
                params.append((name.strip(), val.strip()))

        # Extrair portas
        port_block_match = re.search(
            r"port\s*\((.*?)\);\s*end", code, re.DOTALL | re.IGNORECASE
        )
        if not port_block_match:
            raise ValueError("Bloco de portas VHDL não encontrado.")
        port_block = port_block_match.group(1)

        ports = re.findall(r"(\w+)\s*:\s*(in|out|inout)", port_block, re.IGNORECASE)
        ports = [(d.lower(), p) for p, d in ports]

    # --------------------------
    # Gerar instância Verilog
    # --------------------------
    lines = []

    # Adicionar parâmetros se existirem
    if params:
        lines.append(f"{module_name} #(")
        for name, val in params:
            lines.append(f"    .{name:<15} ({val}),")
        lines[-1] = lines[-1].rstrip(",")
        lines.append(f") {instance_name} (")
    else:
        lines.append(f"{module_name} {instance_name} (")

    # Adicionar portas
    for direction, port in ports:
        if port in reverse_map:
            signal = reverse_map[port]
        elif direction == "input" and (
            "dbg_" in port.lower() or "trace_" in port.lower()
        ):
            signal = "1'b0"
        elif direction == "input" and (
            "_en" in port.lower() or port.lower().endswith("_valid")
        ):
            signal = "1'b1"
        elif direction == "input":
            signal = "1'b0"
        else:
            signal = ""

        if signal:
            lines.append(f"    .{port:<15} ({signal}),")
        else:
            lines.append(f"    .{port:<15} (),")

    lines[-1] = lines[-1].rstrip(",")
    lines.append(");")

    return "\n".join(lines)
