"""Gera arquivos .dot a partir de um JSON com informações de um grafo."""

import json


def generate_dot(graph, graph_name):
    """Gera o conteúdo do arquivo .dot a partir do grafo fornecido."""
    dot_content = f"digraph {graph_name} {{\n"

    for key, values in graph.items():
        for value in values:
            if key != "module":  # Remover o módulo 'module'
                dot_content += f"    {key} -> {value};\n"

    dot_content += "}\n"
    return dot_content


def main(json_input):
    """Função principal para gerar os arquivos .dot a partir de um JSON."""
    # Carregar o JSON
    data = json.loads(json_input)

    # Gerar conteúdo para o arquivo dot do module_graph
    module_graph_dot = generate_dot(data["module_graph"], "module_graph")

    # Gerar conteúdo para o arquivo dot do module_graph_inverse
    module_graph_inverse_dot = generate_dot(
        data["module_graph_inverse"], "module_graph_inverse"
    )

    # Salvar os arquivos .dot
    with open("module_graph.dot", "w", encoding="utf-8") as f:
        f.write(module_graph_dot)

    with open("module_graph_inverse.dot", "w", encoding="utf-8") as f:
        f.write(module_graph_inverse_dot)


if __name__ == "__main__":
    # Exemplo de JSON (substitua pelo seu JSON)
    json_data = """
    {
            "module_graph": {
        "ClkDivider": [
            "clk_divider_tb"
        ],
        "Debug": [
            "Debug"
        ],
        "ResetBootSystem": [
            "top",
            "top",
            "top",
            "top",
            "top",
            "top",
            "top",
            "top",
            "reset_tb"
        ],
        "top": [],
        "Alu": [
            "Core"
        ],
        "ALU_Control": [
            "Core"
        ],
        "Control_Unit": [
            "Core"
        ],
        "Core": [
            "core_tb"
        ],
        "CSR_Unit": [
            "Core"
        ],
        "Immediate_Generator": [
            "Core"
        ],
        "MDU": [
            "Core"
        ],
        "MUX": [
            "Core",
            "Core",
            "Core",
            "Core",
            "Core",
            "mux_tb"
        ],
        "PC": [
            "Core",
            "pc_tb"
        ],
        "Registers": [
            "Core",
            "registers_tb"
        ],
        "BUS": [
            "Risco_5_SOC",
            "core_tb"
        ],
        "FIFO": [
            "UART"
        ],
        "GPIO": [],
        "GPIOS": [
            "Risco_5_SOC",
            "gpio_tb"
        ],
        "LEDs": [
            "Risco_5_SOC",
            "core_tb"
        ],
        "Memory": [
            "Risco_5_SOC",
            "core_tb"
        ],
        "PWM": [
            "GPIOS",
            "GPIOS"
        ],
        "Risco_5_SOC": [
            "top",
            "top",
            "top",
            "top",
            "top",
            "top",
            "top",
            "top",
            "Risco_5_SOC",
            "soc_tb"
        ],
        "UART": [
            "Risco_5_SOC",
            "UART"
        ],
        "uart_tool_rx": [
            "UART"
        ],
        "uart_tool_tx": [
            "UART"
        ],
        "alu_tb": [],
        "clk_divider_tb": [],
        "core_tb": [],
        "fifo_tb": [],
        "gpio_tb": [],
        "immediate_generator_tb": [],
        "mux_tb": [],
        "pc_tb": [],
        "registers_tb": [],
        "reset_tb": [],
        "soc_tb": []
    },
    "module_graph_inverse": {
        "ClkDivider": [],
        "Debug": [
            "Debug"
        ],
        "ResetBootSystem": [],
        "top": [
            "ResetBootSystem",
            "Risco_5_SOC",
            "ResetBootSystem",
            "Risco_5_SOC",
            "ResetBootSystem",
            "Risco_5_SOC",
            "ResetBootSystem",
            "Risco_5_SOC",
            "ResetBootSystem",
            "Risco_5_SOC",
            "ResetBootSystem",
            "Risco_5_SOC",
            "ResetBootSystem",
            "Risco_5_SOC",
            "ResetBootSystem",
            "Risco_5_SOC"
        ],
        "Alu": [],
        "ALU_Control": [],
        "Control_Unit": [],
        "Core": [
            "PC",
            "MUX",
            "MUX",
            "MUX",
            "MUX",
            "MDU",
            "MUX",
            "Registers",
            "Control_Unit",
            "ALU_Control",
            "Alu",
            "Immediate_Generator",
            "CSR_Unit"
        ],
        "CSR_Unit": [],
        "Immediate_Generator": [],
        "MDU": [],
        "MUX": [],
        "PC": [],
        "Registers": [],
        "BUS": [],
        "FIFO": [],
        "GPIO": [],
        "GPIOS": [
            "PWM",
            "PWM"
        ],
        "LEDs": [],
        "Memory": [],
        "PWM": [],
        "Risco_5_SOC": [
            "Risco_5_SOC",
            "Memory",
            "BUS",
            "LEDs",
            "UART",
            "GPIOS"
        ],
        "UART": [
            "UART",
            "FIFO",
            "uart_tool_rx",
            "uart_tool_tx"
        ],
        "uart_tool_rx": [],
        "uart_tool_tx": [],
        "alu_tb": [],
        "clk_divider_tb": [
            "ClkDivider"
        ],
        "core_tb": [
            "Core",
            "Memory",
            "BUS",
            "LEDs"
        ],
        "fifo_tb": [],
        "gpio_tb": [
            "GPIOS"
        ],
        "immediate_generator_tb": [],
        "mux_tb": [
            "MUX"
        ],
        "pc_tb": [
            "PC"
        ],
        "registers_tb": [
            "Registers"
        ],
        "reset_tb": [
            "ResetBootSystem"
        ],
        "soc_tb": [
            "Risco_5_SOC"
        ]
    }
}

    """

    main(json_data)
