# ProcessorCI

[![Pylint](https://github.com/LSC-Unicamp/processor_ci/actions/workflows/pylint.yml/badge.svg)](https://github.com/LSC-Unicamp/processor_ci/actions/workflows/pylint.yml)  
[![Python Code Format Check](https://github.com/LSC-Unicamp/processor_ci/actions/workflows/blue.yml/badge.svg)](https://github.com/LSC-Unicamp/processor_ci/actions/workflows/blue.yml)  

- **Não fala Inglês? [clique aqui](./README.pt.md)**

Welcome to ProcessorCI!

**ProcessorCI** is a project aimed at modernizing processor verification by integrating established verification techniques, continuous integration, and FPGA usage.

## About this Module

This repository contains utility scripts to configure processors, perform synthesis, load onto FPGAs, and other tasks related to ProcessorCI.

## Getting Started

### Installation

1. **Clone the Repository**  
Clone the repository to your local development environment:

```bash
git clone https://github.com/LSC-Unicamp/processor_ci.git  
cd processor_ci
```

2. **Set up a Virtual Environment and Install Dependencies**  

```bash
python3 -m venv env
. env/bin/activate
pip install -r requirements.txt
```

**Note**: Every time you use the project, activate the virtual environment with:

```bash
. env/bin/activate
```

### Adding a New Processor

The process to add a processor consists of three steps:

1. Generate the configuration file (`config.json`).  
2. Establish the connections for Verilog modules.  
3. Integrate the pipeline file into Jenkins.  

#### 1. Generating Configurations  

To generate the Jenkins pipeline, fill out a JSON file with the processor's characteristics and add a new entry to `config.json`. Example:  

```json
"darkriscv": {
    "name": "darkriscv",
    "folder": "darkriscv",
    "sim_files": [],
    "files": ["rtl/darkriscv.v"],
    "include_dirs": ["rtl"],
    "repository": "https://github.com/darklife/darkriscv",
    "top_module": "darkriscv",
    "extra_flags": [],
    "language_version": "2005"
}
```

To simplify this, the script `config_generator.py` can generate an initial configuration:  

```bash
python3 config_generator.py -u PROCESSOR_URL -c
```

This command will clone the repository, list the files, and add a new entry to `config.json`. You can change the configuration file path using the `-p` flag. To disable AI-based models, use the `-n` flag.

After generation, review the configuration to ensure its correctness.

#### 2. Establishing Connections  

The script will create a Verilog file corresponding to the processor. Edit this file to connect the processor's main module to the ProcessorCI's top module. If you manually filled out `config.json`, create a file based on the template:

```bash
cp rtl/template.v rtl/<repository_name>.v
```

Example connection:

```verilog
Controller #(
    ...
) Controller(
    ...
    .clk_core  (clk_core),
    .reset_core(reset_core),
    
    .core_memory_response  (core_memory_response),
    .core_read_memory      (memory_read),
    .core_write_memory     (memory_write),
    .core_address_memory   (address),
    .core_write_data_memory(core_write_data),
    .core_read_data_memory (core_read_data),

    //sync memory bus
    .core_read_data_memory_sync     (),
    .core_memory_read_response_sync (),
    .core_memory_write_response_sync(),

    // Data memory
    .core_memory_response_data  (),
    .core_read_memory_data      (1'b0),
    .core_write_memory_data     (1'b0),
    .core_address_memory_data   (32'h00000000),
    .core_write_data_memory_data(32'h00000000),
    .core_read_data_memory_data ()
);
Core #(
    .BOOT_ADDRESS(32'h00000000)
) Core(
    .clk            (clk_core),
    .reset          (reset_core),
    .memory_response(core_memory_response),
    .memory_read    (memory_read),
    .memory_write   (memory_write),
    .write_data     (core_write_data),
    .read_data      (core_read_data),
    .address        (address)
);
```

More details are available in the [Controller documentation](https://lsc-unicamp.github.io/processor_ci-controller/).  

#### 3. Integrating with Jenkins  

After configuration, create a new item in Jenkins and copy the generated pipeline into it. Currently, there is no automated integration with the official Jenkins. If you want to integrate a new processor, open an *Issue* with the name, URL, and configuration.  

### Usage  

After configuring and integrating the processor into the infrastructure, you can interact with it using the project's scripts. The main interactions involve synthesis and loading onto various FPGAs. An example usage:

```bash
cd processor_repository/
# Perform synthesis
python3 /path_to_script/main.py -c /path_to_config/config.json -p risc-v -b digilent_nexys4_ddr
# Perform loading
python3 /path_to_script/main.py -c /path_to_config/config.json -p risc-v -b digilent_nexys4_ddr -l
```

- `-c /path_to_config/config.json`: Path to the processor configuration file.  
- `-p risc-v`: Name of the processor to be synthesized.  
- `-b digilent_nexys4_ddr`: Target FPGA for synthesis and loading.  
- `-l`: Load the design onto the FPGA after synthesis.  

## Usage Options  

The ProcessorCI scripts offer various options configurable via flags. Below are the main flags and functionalities:

### Available Flags in the Configuration Script

- `-c, --generate-config`: Generate initial processor configurations from the repository URL.  

Example:

```bash
python3 config_generator.py -c -u PROCESSOR_URL
```

Details:  

- Clones the processor repository.  
- Analyzes repository files to identify modules and testbenches.  
- Generates a JSON file with processor configurations.  
- Optionally adds the generated configuration to the central file (`config.json`) using the `-a` flag.  

### Examples of Main Script Usage  

1. **Configure a processor for a specific board:**

```bash
python3 main.py -c config.json -p processor_name -b board_name
```

2. **Define a custom path for toolchains:**

```bash
python3 main.py -c config.json -p processor_name -b board_name -t /custom/toolchain/path
```

3. **Load the bitstream onto the FPGA after the build:**

```bash
python3 main.py -c config.json -p processor_name -b board_name -l
```

**Requirements:**

- A valid JSON configuration file containing data about processors and boards.  
- Ensure the toolchain path and board configurations are correctly set in your environment.

## Questions and Suggestions  

The official documentation is available at: [processorci.ic.unicamp.br](https://processorci.ic.unicamp.br/).  
Questions and suggestions can be submitted in the Issues section on GitHub. Contributions are welcome, and all Pull Requests will be reviewed and merged when possible.  

## Contributing to the Project  

**Contributions**: If you wish to contribute improvements, see the [CONTRIBUTING.md](./CONTRIBUTING.md) file.  

## License  

This project is licensed under the [MIT License](./LICENSE), granting full freedom of use.  