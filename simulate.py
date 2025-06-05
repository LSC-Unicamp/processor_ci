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

def run_ghdl_import(cpu_name, vhdl_files):
    """Importar todos os arquivos VHDL com GHDL -i."""
    print("[INFO] Importando arquivos VHDL com GHDL (-i)...")
    cmd = [
        "ghdl", "-i", "--std=08",
        f"--work={cpu_name}",
        f"--workdir={BUILD_DIR}",
        f"-P{BUILD_DIR}"
    ] + list(map(str, vhdl_files))
    print(f"[CMD] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def run_ghdl_elaborate(cpu_name, top_module):
    """Elaborar com GHDL -m."""
    print("[INFO] Elaborando projeto com GHDL (-m)...")
    cmd = [
        "ghdl", "-m", "--std=08",
        f"--work={cpu_name}",
        f"--workdir={BUILD_DIR}",
        f"-P{BUILD_DIR}",
        f"{top_module}"
    ]
    print(f"[CMD] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def synthesize_to_verilog(cpu_name, output_file, top_module):
    """Sintetizar o VHDL com GHDL para Verilog."""
    print(f"[INFO] Sintetizando {cpu_name} para Verilog...")
    cmd = [
        "ghdl", "synth", "--latches", "--std=08",
        f"--work={cpu_name}",
        f"--workdir={BUILD_DIR}",
        f"-P{BUILD_DIR}",
        "--out=verilog", top_module
    ]
    print(f"[CMD] {' '.join(cmd)} > {output_file}")
    with open(output_file, "w") as f:
        subprocess.run(cmd, stdout=f, check=True)

def main():
    if len(sys.argv) != 2:
        print("Uso: simulate.py <nome_do_processador>")
        sys.exit(1)

    cpu_name = sys.argv[1]

    print("[INFO] Iniciando simulação do processador:", cpu_name)

    config_file = CONFIG_DIR / f"{cpu_name}.json"
    top_module_file = RTL_DIR / f"{cpu_name}.sv"

    if not config_file.exists():
        print(f"[ERRO] Configuração não encontrada: {config_file}")
        sys.exit(1)

    if not top_module_file.exists():
        print(f"[ERRO] Top module não encontrado: {top_module_file}")
        sys.exit(1)

    with open(config_file) as f:
        config = json.load(f)

    file_list = config.get("files", [])
    include_dirs = config.get("include_dirs", [])
    top_module = config.get("top_module", cpu_name)

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

    if vhdl_files:
        BUILD_DIR.mkdir(exist_ok=True)
        run_ghdl_import(cpu_name, vhdl_files)
        run_ghdl_elaborate(cpu_name, top_module)

        verilog_output = BUILD_DIR / f"{cpu_name}.v"
        synthesize_to_verilog(cpu_name, verilog_output, top_module)
        other_files.append(str(verilog_output))

    other_files.append(str(top_module_file))
    other_files += [
        str(INTERNAL_DIR / "verification_top.sv"),
        str(INTERNAL_DIR / "memory.sv"),
        str(INTERNAL_DIR / "axi4_to_wishbone.sv"),
        str(INTERNAL_DIR / "axi4lite_to_wishbone.sv"),
        str(INTERNAL_DIR / "ahblite_to_wishbone.sv")
    ]

    include_flags = []
    for inc_dir in include_dirs:
        inc_path = PROCESSADOR_BASE / cpu_name / inc_dir
        if inc_path.exists():
            include_flags.append(f"-I{inc_path}")
        else:
            print(f"[AVISO] Diretório de include não encontrado: {inc_path}")

    verilator_cmd = [
        "verilator", "--cc", "--exe", "--build",
        "--trace", "-Wno-fatal", "-DSIMULATION", "-DSYNTHESIS",
        "-Wall", "-Wno-UNOPTFLAT", "-Wno-IMPLICIT",
        "-Wno-TIMESCALEMOD", "-Wno-UNUSED",
        "--top-module", "verification_top",
        str(INTERNAL_DIR / "soc_main.cpp"),
        *other_files,
        *include_flags,
        "-CFLAGS", "-std=c++17"
    ]

    print(f"[CMD] {' '.join(verilator_cmd)}")
    subprocess.run(verilator_cmd, check=True, cwd=BUILD_DIR)

    sim_executable = BUILD_DIR / "obj_dir" / "Vverification_top"
    if sim_executable.exists():
        print("[INFO] Executando simulação...")
        subprocess.run([str(sim_executable)], check=True)
    else:
        print("[ERRO] Executável de simulação não encontrado.")

if __name__ == "__main__":
    main()
