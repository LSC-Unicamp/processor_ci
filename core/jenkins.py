"""
This module contains the function `generate_jenkinsfile`, which is responsible for
generating a Jenkins pipeline configuration (Jenkinsfile) for FPGA simulation and build
pipelines. The function creates a Jenkins pipeline that includes stages for cloning the
repository, running simulations, and building FPGA designs in parallel. Additionally, it
provides support for different hardware description languages (VHDL and Verilog) and can
include pre-processing steps for Verilog file conversion.

Key steps in the pipeline include:
- Cloning the repository.
- Running a simulation for the provided FPGA files (VHDL or Verilog).
- Parallel execution of FPGA build stages, including synthesis, flashing, and testing.

The generated Jenkinsfile can be used to automate FPGA design verification and deployment
processes using Jenkins.

Functions:
    generate_jenkinsfile(config: dict, fpgas: list, main_script_path: str,
        lang_version: str, extra_flags: list = None) -> None:
        Generates a Jenkinsfile based on the provided configuration and FPGA details.

Arguments:
    config (dict): A dictionary containing project and FPGA configuration.
    fpgas (list): A list of FPGA names to be included in the build pipeline.
    main_script_path (str): The path to the main Python script used for synthesis and flashing.
    utilities_script_path (str): The path to the utilities script for additional pipeline steps.
    lang_version (str): The version of the hardware description language
    to be used (e.g., VHDL or Verilog). extra_flags (list, optional):
    Additional flags for the simulation command.
"""


def generate_jenkinsfile(
    config: dict,
    fpgas: list,
    main_script_path: str,
    lang_version: str,
    extra_flags: list = None,
) -> None:
    """
    Generates a Jenkinsfile for FPGA build and simulation pipelines.

    Args:
        config (dict): Configuration dictionary containing project and FPGA details.
        fpgas (list): List of FPGA names to be used in the pipeline.
        main_script_path (str): Path to the main Python script for synthesis and flashing.
        utilities_script_path (str): Path to the utilities script for additional pipeline steps.
        lang_version (str): The version of the VHDL or Verilog language to use.
        extra_flags (list, optional): List of extra flags for the simulation command.

    Returns:
        None
    """
    jenkinsfile = """
pipeline {{
    agent any
    stages {{
        stage('Git Clone') {{
            steps {{
                sh 'rm -rf *.xml'
                sh 'rm -rf {folder}'
                sh 'git clone --recursive --depth=1 {repository} {folder}'
            }}
        }}

        {pre_script}

        stage('Simulation') {{
            steps {{
                dir("{folder}") {{
                    {simulation_command}
                }}
            }}
        }}

         stage('Utilities')  {{
            steps {{
                dir("{folder}") {{
                    {utilities_command}
                }}            
            }}
        }}

        stage('FPGA Build Pipeline') {{
            parallel {{
                {fpga_parallel_stages}
            }}
        }}
    }}
    post {{
        always {{
            junit '**/*.xml'
        }}
    }}
}}
"""

    # Prepare file lists
    files = " ".join(config.get("files", []))
    sim_files = " ".join(config.get("sim_files", []))
    include_dirs = " ".join(f"-I {inc}" for inc in config.get("include_dirs", []))

    # Define extra flags if provided
    extra_flags_str = " ".join(extra_flags) if extra_flags else ""

    # Command for extra utilities in the pipeline
    utilities_command = (
        r'sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) '
        + '-c /eda/processor_ci/config -o /jenkins/processor_ci_utils/labels"'
    )

    # Determine simulation command based on file types
    is_vhdl = any(
        file.endswith(".vhdl") or file.endswith(".vhd")
        for file in config.get("files", [])
    )
    is_verilog = any(file.endswith(".v") for file in config.get("files", []))

    is_system_verilog = any(file.endswith(".sv") for file in config.get("files", []))

    if is_system_verilog:
        simulation_command = 'echo "simulation not supported for System Verilog files"'
    elif is_vhdl and not is_verilog:
        # VHDL simulation command
        simulation_command = f'sh "ghdl -a --std={lang_version} \
            {extra_flags_str} {include_dirs} {files} {sim_files}"'
    elif is_verilog and not is_vhdl:
        # Verilog simulation command
        simulation_command = (
            f'sh "iverilog -o simulation.out -g{lang_version} \
                {extra_flags_str}'
            + f' -s {config["top_module"]} {include_dirs} {files} {sim_files}"'
        )
    else:
        simulation_command = (
            'echo "simulation not supported for mixed VHDL and Verilog files"'
        )

    # Prepare FPGA stages for each FPGA in parallel
    fpga_parallel_stages = "\n                ".join(
        [
            """
                stage('{fpga}') {{
                    options {{
                        lock(resource: '{fpga}')
                    }}
                    stages {{
                        stage('Synthesis and PnR') {{
                            steps {{
                                dir("{folder}") {{
                                    echo 'Starting synthesis for FPGA {fpga}.'
                                sh 'python3 {main_script_path} -c /eda/processor_ci/config \\
                                            -p {folder} -b {fpga}'
                                }}
                            }}
                        }}
                        stage('Flash {fpga}') {{
                            steps {{
                                dir("{folder}") {{
                                    echo 'Flashing FPGA {fpga}.'
                                sh 'python3 {main_script_path} -c /eda/processor_ci/config \\
                                            -p {folder} -b {fpga} -l'
                                }}
                            }}
                        }}
                        stage('Test {fpga}') {{
                            steps {{
                                echo 'Testing FPGA {fpga}.'
                                sh 'echo "Test for FPGA in {port}"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c\
                                /eda/processor_ci_tests/config.json --p {port} -m {march} -k {sync_key} {ctm}'
                            }}
                        }}
                    }}
                }}""".format(
                fpga=fpga,
                folder=config["folder"],
                main_script_path=main_script_path,
                port="/dev/ttyACM0" if fpga == "colorlight_i9" else "/dev/ttyUSB1",
                march=config["march"],
                sync_key=(
                    "0x41525459" if fpga == "digilent_arty_a7_100t" else "0x434F4C4F"
                ),
                ctm="-ctm" if config["two_memory"] else "",
            )
            for fpga in fpgas
        ]
    )

    # python main.py -p /dev/ttyUSB2 -b 115200 -s 2 -c config.json -m rv32i -e coremark,dhrystone -k 0x4E455859
    pre_script = ""

    if "pre_script" in config.keys():
        pre_script = f"""
        stage('Verilog Convert') {{
            steps {{
                dir("{config['folder']}") {{
                    sh '{config['pre_script']}'
                }}
            }}
        }}
        """

    # Generate Jenkinsfile content
    jenkinsfile = jenkinsfile.format(
        repository=config["repository"],
        folder=config["folder"],
        pre_script=pre_script,
        top_module=config["top_module"],
        include_dirs=include_dirs,
        files=files,
        sim_files=sim_files,
        simulation_command=simulation_command,
        fpga_parallel_stages=fpga_parallel_stages,
        utilities_command=utilities_command,
    )

    # Save the Jenkinsfile with specified encoding
    with open("Jenkinsfile", "w", encoding="utf-8") as f:
        f.write(jenkinsfile)

    print("Jenkinsfile generated successfully.")
