import find_processor_interface
import sys
import re
import json

wishbone_prompt = """You are a hardware engineer. Your task is to connect a processor interface to a wrapper interface following the rules of a Wishbone memory-mapped bus. You will be given:

1. A processor interface (Verilog/VHDL module).
2. A wrapper interface (Verilog/VHDL module).
3. The Wishbone specification with required and optional signals.
4. Information about single or dual memory interfaces.

Your task has two parts:

---

**Part 1: Map signals to the wrapper**

- Create a JSON where the key is the wrapper signal and the value is the processor signal or an expression to generate it.
- Use comments in the code if they mention the interface (e.g. "AHB master port")
- Match inputs to inputs and outputs to outputs.
- Both the name and the function must match (timing, purpose, driver).
- Connect signals with the same bit width.
- Use the Wishbone mapping:
    "Wishbone": {{
        "required": ["adr", "dat_i", "dat_o", "we", "cyc", "stb", "ack"],
        "optional": ["sel", "err", "rty", "stall"]
    }}
- Allow for alternate names (e.g. "rw_address" ~= "adr", "write_request" ~= "write")
- If needed, generate expressions to convert signals (e.g., `"core_we": "wstrb != 0"`, `"core_stb & core_cyc": "read_request | write_request"`)
- If the sel signal is missing, complete it with "4'b1111" or the equivalent in VHDL.
- If an input signal is missing (e.g. ack) leave it open using `null`
- Check the reset signal polarity (rst or rst_n) and invert if needed.
- Treat `cyc` and `stb` signals from a Wishbone interface as potentially merged into a single signal (e.g., read_request can represent cyc & stb). 
- If there is only a single memory interface, leave dual-memory signals (data_mem_*) unconnected (use `null`).

Example format:
{{
  "sys_clk": "clk",
  "rst_n": "rst_n",
  "core_cyc": "cyc_o",
  "core_stb": "stb_o",
  "core_we": "we_o",
  "core_addr": "addr_o",
  "core_data_out": "data_o",
  "core_data_in": "data_i",
  "core_ack": "ack_i",
  "core_sel": "4'b1111",
  "data_mem_cyc": null,
  ...
}}

---

Wrapper interface:
module processorci_top (
    input logic sys_clk, // Clock de sistema
    input logic rst_n,   // Reset do sistema

    `ifndef SIMULATION
    // UART pins
    input  logic rx,
    output logic tx,

    // SPI pins
    input  logic sck,
    input  logic cs,
    input  logic mosi,
    output logic miso,

    //SPI control pins
    input  logic rw,
    output logic intr

    `else
    output logic        core_cyc,      // Indica uma transação ativa
    output logic        core_stb,      // Indica uma solicitação ativa
    output logic        core_we,       // 1 = Write, 0 = Read

    output logic [31:0] core_addr,     // Endereço
    output logic [3:0]  core_sel,     // Máscara de escrita (byte enable)
    output logic [31:0] core_data_out, // Dados de entrada (para escrita)
    input  logic [31:0] core_data_in,  // Dados de saída (para leitura)

    input  logic        core_ack       // Confirmação da transação

    `ifdef ENABLE_SECOND_MEMORY
,
    output logic        data_mem_cyc,
    output logic        data_mem_stb,
    output logic        data_mem_we,
    output logic [3:0]  data_mem_sel,
    output logic [31:0] data_mem_addr,
    output logic [31:0] data_mem_data_out,
    input  logic [31:0] data_mem_data_in,
    input  logic        data_mem_ack
    `endif

    `endif
);

Processor interface:

{processor_interface}

Memory interface: {memory_interface}

---

**Final output format**

You must first give your reasoning and then output the json in this format:

```
Connections:
{{
    "sys_clk" : "clk",
    ...
}}
```
"""

############################################################################

ahb_prompt = """You are a hardware engineer. Your task is to connect a processor interface to a wrapper interface following the rules of a Wishbone memory-mapped bus. You will be given:

1. A processor interface (Verilog/VHDL module).
2. A adapter interface (Verilog/VHDL module).
3. The AHB specification with required and optional signals.
4. Information about single or dual memory interfaces.

Your task has two parts:

---

**Part 1: Map signals to the adapter**

- Create a JSON where the key is the adapter signal and the value is the processor signal or an expression to generate it.
- It's a connection: match processor outputs to adapter inputs and vice-versa.
- Use comments in the code if they mention the interface (e.g. "AHB master port")
- Both the name and the function must match (timing, purpose, driver).
- Connect signals with the same bit width.
- Use the AHB mapping:
    "AHB": {{
    "required": ["haddr", "hwrite", "htrans", "hsize", "hready", "hresp"],
    "optional": ["hburst", "hprot", "hmastlock", "hmaster", "hexcl", "hexokay", "hwdata", "hrdata"]
    }}
- Allow for alternate names (e.g. "rw_address" ~= "adr", "write_request" ~= "write").
- If an input signal is missing (e.g. ack) leave it open using `null`
- Check the reset signal polarity and invert if needed (e.g. "rst_n": "!reset").
- If there is a dual memory interface, consider two adapters and put a prefix (adapter_instr or adapter_data) before the AHB signal.

Example format:
{{
  "sys_clk": "HCLK",
  "rst_n": "HRESETn",
  "htrans": "HTRANS",
  ...
}}
or
{{
  "sys_clk": "HCLK",
  "rst_n": "HRESETn",
  "adapter_instr_htrans": "INSTR_HTRANS",
  "adapter_data_htrans": "DATA_HTRANS",
  ...
}}

---

Adapter interface:
module ahb_to_wishbone #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    input logic                   HCLK,
    input logic                   HRESETn,

    // AHB Interface
    input  logic [ADDR_WIDTH-1:0] HADDR,
    input  logic [1:0]            HTRANS,
    input  logic                  HWRITE,
    input  logic [2:0]            HSIZE,
    input  logic [2:0]            HBURST,
    input  logic [3:0]            HPROT,
    input  logic                  HLOCK,
    input  logic [DATA_WIDTH-1:0] HWDATA,
    input  logic                  HREADY,
    output logic [DATA_WIDTH-1:0] HRDATA,
    output logic                  HREADYOUT,
    output logic [1:0]            HRESP,

    // Wishbone Interface
    output logic                  wb_cyc,
    output logic                  wb_stb,
    output logic                  wb_we,
    output logic [3:0]            wb_wstrb,
    output logic [ADDR_WIDTH-1:0] wb_adr,
    output logic [DATA_WIDTH-1:0] wb_dat_w,
    input  logic [DATA_WIDTH-1:0] wb_dat_r,
    input  logic                  wb_ack
);

Processor interface:

{processor_interface}

Memory interface: {memory_interface}

---

**Final output format**

You must first give your reasoning and then output the json in this format:

```
Connections:
{{
    "sys_clk" : "clk",
    ...
}}
```
"""

############################################################################

axi_prompt = """You are a hardware engineer. Your task is to connect a processor interface to a wrapper interface following the rules of a Wishbone memory-mapped bus. You will be given:

1. A processor interface (Verilog/VHDL module).
2. A adapter interface (Verilog/VHDL module).
3. The AHB specification with required and optional signals.
4. Information about single or dual memory interfaces.

Your task has two parts:

---

**Part 1: Map signals to the adapter**

- Create a JSON where the key is the adapter signal and the value is the processor signal or an expression to generate it.
- It's a connection: match processor outputs to adapter inputs and vice-versa.
- Use comments in the code if they mention the interface (e.g. "AHB master port")
- Both the name and the function must match (timing, purpose, driver).
- Connect signals with the same bit width.
- Use the AXI mapping:
    "AXI": {{
    "required": ["araddr", "arvalid", "arready", "rdata", "rvalid", "rready",
                "awaddr", "awvalid", "awready", "wdata", "wvalid", "wready",
                "bresp", "bvalid", "bready"],
    "optional": ["arsize", "arburst", "arlen", "arprot", "arcache",
                "awsize", "awburst", "awlen", "awprot", "awcache",
                "wstrb", "wlast", "rlast"]
    }}
- Allow for alternate names (e.g. "rw_address" ~= "adr", "write_request" ~= "write").
- Check the reset signal polarity and invert if needed (e.g. "rst_n": "!reset").
- If there is a dual memory interface, consider two adapters and put a prefix (adapter_instr or adapter_data) before the AXI signal.

Example format:
{{
  "sys_clk": "clk",
  "rst_n": "reset_n",
  "awaddr": "s_awaddr",
  ...
}}
or
{{
  "sys_clk": "HCLK",
  "rst_n": "HRESETn",
  "adapter_instr_awaddr": "instr_mem_awaddr",
  "adapter_data_awaddr": "data_mem_awaddr",
  ...
}}

---

Adapter interface:
module AXI4Lite_to_Wishbone #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    input  logic                  ACLK,
    input  logic                  ARESETN,

    // AXI4-Lite Slave Interface
    input  logic [ADDR_WIDTH-1:0] AWADDR,
    input  logic [2:0]            AWPROT,
    input  logic                  AWVALID,
    output logic                  AWREADY,

    input  logic [DATA_WIDTH-1:0] WDATA,
    input  logic [(DATA_WIDTH/8)-1:0] WSTRB,
    input  logic                  WVALID,
    output logic                  WREADY,

    output logic [1:0]            BRESP,
    output logic                  BVALID,
    input  logic                  BREADY,

    input  logic [ADDR_WIDTH-1:0] ARADDR,
    input  logic [2:0]            ARPROT,
    input  logic                  ARVALID,
    output logic                  ARREADY,

    output logic [DATA_WIDTH-1:0] RDATA,
    output logic [1:0]            RRESP,
    output logic                  RVALID,
    input  logic                  RREADY,

    // Wishbone Master Interface
    output logic [ADDR_WIDTH-1:0] wb_adr_o,
    output logic [DATA_WIDTH-1:0] wb_dat_o,
    output logic                  wb_we_o,
    output logic                  wb_stb_o,
    output logic                  wb_cyc_o,
    output logic [(DATA_WIDTH/8)-1:0] wb_sel_o,
    input  logic [DATA_WIDTH-1:0] wb_dat_i,
    input  logic                  wb_ack_i,
    input  logic                  wb_err_i
);

Processor interface:

{processor_interface}

Memory interface: {memory_interface}

---

**Final output format**

You must first give your reasoning and then output the json in this format:

```
Connections:
{{
    "sys_clk" : "clk",
    ...
}}
```
"""

############################################################################
def connect_interfaces(interface_info, processor_interface):
    if interface_info["bus_type"] == "Wishbone":
        prompt = wishbone_prompt.format(
            processor_interface=processor_interface,
            memory_interface=interface_info["memory_interface"],
        )
    elif interface_info["bus_type"] == "AHB":
        prompt = ahb_prompt.format(
            processor_interface=processor_interface,
            memory_interface=interface_info["memory_interface"],
        )
    elif interface_info["bus_type"] == "AXI":
        prompt = axi_prompt.format(
            processor_interface=processor_interface,
            memory_interface=interface_info["memory_interface"],
        )
    else:
        print("Defaulting to Wishbone.")
        prompt = wishbone_prompt.format(
            processor_interface=processor_interface,
            memory_interface=interface_info["memory_interface"],
        )
    
    success, response = find_processor_interface.send_prompt(prompt)
    if not success:
        print("Error communicating with the server.")
        return None, None
    # print("Full response from server:") # debug
    # print(response)

    connections = filter_connections_from_response(response)
    return connections

def filter_connections_from_response(response):
    def clean_json_block(block: str):
        # Remove comments (// ...)
        block = re.sub(r"//.*", "", block)
        # Remove trailing commas
        block = re.sub(r",\s*}", "}", block)
        block = re.sub(r",\s*]", "]", block)
        return block.strip()

    # Regex to capture Connections and Defaults blocks (with optional ** markdown formatting)
    connections_match = re.search(r"\*{0,2}Connections\*{0,2}:\s*({.*?})", response, re.DOTALL)

    if not connections_match:
        print("Could not find Connections in the response.")
        return None
    
    connections_str = clean_json_block(connections_match.group(1))

    print("Extracted Connections JSON:") # debug
    print(connections_str) # debug

    connections = json.loads(connections_str)

    return connections



def main():
    file_path = sys.argv[1]
    matches = find_processor_interface.extract_full_module(file_path)

    if not matches:
        print("No module/entity declarations found.")
        return
    else:
        for line_no, snippet in matches:
            print("=" * 60)
            print(f"Declaration match at line {line_no}:")
            print("=" * 60)
            print(snippet)
            print()

    # only get first declaration as it's the most probable option
    interface_and_ports = find_processor_interface.extract_interface_and_memory_ports(matches[0][1])
    if not interface_and_ports:
        print("No bus interface type or memory port information found.")
        return
    else:
        print("=" * 60)
        print("Bus interface type and number of memory ports:")
        print("=" * 60)
        print(interface_and_ports)
        print()

    connections = connect_interfaces(interface_and_ports, matches[0][1])
    if not connections:
        print("No connections generated.")
        return
    else:
        print("=" * 60)
        print("Signal connections:")
        print("=" * 60)
        print(connections)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python connect_interface.py <file.v|file.sv|file.vhd>")
        sys.exit(1)
    main()