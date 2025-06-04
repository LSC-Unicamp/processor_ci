#!/usr/bin/env python3

import sys
import json
import subprocess
from pathlib import Path

# Diretórios principais
BASE_DIR = Path(__file__).parent.resolve()
RTL_DIR = BASE_DIR / "rtl"
CONFIG_DIR = BASE_DIR / "config"
INTERNAL_DIR = BASE_DIR / "internal"
BUILD_DIR = BASE_DIR / "build"
PROCESSADOR_BASE = Path("/eda/processadores")

def analyze_all_vhdl_files(vhdl_files):
    """Analisar todos os arquivos VHDL de uma vez."""
    print(f"[INFO] Analisando arquivos VHDL:")
    for f in vhdl_files:
        print(f"  {f}")
    cmd = ["ghdl", "-a", *map(str, vhdl_files)]
    print(f"[CMD] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def synthesize_vhdl_entity(entity_name, output_file):
    """Sintetizar a entidade principal para Verilog."""
    print(f"[INFO] Sintetizando entidade VHDL: {entity_name}")
    cmd = [
        "ghdl", "--synth", entity_name,
        "--out=verilog", "-o", str(output_file)
    ]
    print(f"[CMD] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) != 2:
        print("Uso: simulate.py <nome_do_processador>")
        sys.exit(1)

    cpu_name = sys.argv[1]

    # Mensagens informativas
    print("[INFO] Iniciando simulação do processador...")
    print("[INFO] Processador:", cpu_name)
    print("[INFO] Diretório base:", BASE_DIR)
    print("[INFO] Diretório RTL:", RTL_DIR)
    print("[INFO] Diretório de configuração:", CONFIG_DIR)
    print("[INFO] Diretório interno:", INTERNAL_DIR)
    print("[INFO] Diretório de build:", BUILD_DIR)
    print("[INFO] Verificando arquivos...")

    config_file = CONFIG_DIR / f"{cpu_name}.json"
    top_module_file = RTL_DIR / f"{cpu_name}.sv"

    if not config_file.exists():
        print(f"[ERRO] Configuração não encontrada: {config_file}")
        sys.exit(1)

    if not top_module_file.exists():
        print(f"[ERRO] Top module do processador não encontrado: {top_module_file}")
        sys.exit(1)

    with open(config_file) as f:
        config = json.load(f)

    file_list = config.get("files", [])
    include_dirs = config.get("include_dirs", [])

    # Separar arquivos VHDL e outros
    vhdl_files = []
    other_files = []

    for file_rel in file_list:
        src_file = PROCESSADOR_BASE / cpu_name / file_rel
        if not src_file.exists():
            print(f"[AVISO] Arquivo não encontrado: {src_file}")
            continue

        if src_file.suffix.lower() in [".vhdl", ".vhd"]:
            vhdl_files.append(src_file)
        else:
            other_files.append(str(src_file))

    # Analisa todos os arquivos VHDL juntos (na ordem que apareceram)
    if vhdl_files:
        analyze_all_vhdl_files(vhdl_files)
        # Supondo que o nome da entidade VHDL principal é igual ao nome do processador
        verilog_output = PROCESSADOR_BASE / cpu_name / f"{cpu_name}.v"
        synthesize_vhdl_entity(cpu_name, verilog_output)
        other_files.append(str(verilog_output))

    # Adiciona tops e arquivos fixos
    other_files.append(str(top_module_file))
    other_files.append(str(INTERNAL_DIR / "verification_top.sv"))
    other_files.append(str(INTERNAL_DIR / "memory.sv"))
    other_files.append(str(INTERNAL_DIR / "axi4_to_wishbone.sv"))
    other_files.append(str(INTERNAL_DIR / "axi4lite_to_wishbone.sv"))
    other_files.append(str(INTERNAL_DIR / "ahblite_to_wishbone.sv"))

    # Prepara diretório de build
    BUILD_DIR.mkdir(exist_ok=True)

    # Monta lista de -I para include_dirs
    include_flags = []
    for inc_dir in include_dirs:
        # Monta caminho absoluto dos include dirs
        inc_path = PROCESSADOR_BASE / cpu_name / inc_dir
        if inc_path.exists():
            include_flags.append(f"-I{inc_path}")
        else:
            print(f"[AVISO] Diretório de include não encontrado: {inc_path}")

    verilator_cmd = [
        "verilator", "--cc", "--exe", "--build",
        "--trace",  # habilita trace
        "-Wno-fatal",
        "-DSIMULATION",
        "--top-module", "verification_top",
        str(INTERNAL_DIR / "soc_main.cpp"),
        *include_flags,
        *other_files,
        "-CFLAGS", "-std=c++17"
    ]

    print(f"[CMD] {' '.join(verilator_cmd)}")
    print("[INFO] Rodando Verilator...")
    subprocess.run(verilator_cmd, check=True, cwd=BUILD_DIR)

    sim_executable = BUILD_DIR / "obj_dir" / "Vverification_top"
    if sim_executable.exists():
        print("[INFO] Iniciando simulação...")
        subprocess.run([str(sim_executable)], check=True)
    else:
        print("[ERRO] Executável de simulação não encontrado.")

if __name__ == "__main__":
    main()
