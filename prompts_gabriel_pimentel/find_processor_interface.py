import re
from pathlib import Path
import sys
import json
import ast
import argparse

# pip install ollama
from ollama import Client

SERVER_URL = 'http://enqii.lsc.ic.unicamp.br:11434'
client = Client(host=SERVER_URL)

find_interface_prompt = """You are an expert in hardware design and SoC integration. 
Your task is to analyze a HDL module and identify the memory bus interface(s).

The possible bus types are: AHB, AXI, Avalon, Wishbone, or Custom.

You are provided:
1. A dictionary of known bus signals (required and optional) for each bus type.
2. The module declaration (with ports and comments).

Steps:
1. Compare the module’s signals against the dictionary of required/optional signals.
2. Allow for alternate names (e.g. "rw_address" ~= "adr", "write_request" ~= "write").
3. Allow read-only memory interfaces (e.g., instruction fetch ports) to omit write-related signals (`we`, `writedata`) without being classified as Custom.
4. Use comments in the code if they mention the interface (e.g. "AHB master port").
5. Determine whether the processor exposes:
   - A single unified memory interface (shared instruction and data access).
   - Two separate memory interfaces (one for instruction fetch, one for data).
   Look for clues such as signal names containing "instr", "imem", "fetch", "idata" for instructions, and "data", "dmem", "store", "load" for data.
7. Validate signals against the true semantics of each bus standard before assigning confidence:
   - Both the name and the function must match (timing, purpose, driver). 
   - Check that the signal’s bit-width and input/output direction are consistent with the bus specification.
   - Treat `cyc` and `stb` signals from a Wishbone interface as potentially merged into a single signal (e.g., read_request can represent cyc & stb).
   - For Avalon interfaces, prefer mappings where separate `read` and `write` signals exist.
8. Decide which bus type(s) the module most closely matches.
9. If fewer than 70% of the required signals of any bus match, classify as "Custom" with Low confidence. 
10. Assign confidence as follows (after validation):
   - High: >=90% of required signals matched, and this bus has at least 2 more matches than the next closest bus.
   - Medium: >=90% of required signals matched, but another bus type is close (within +/- 1 match).
   - Low: >=70% of required signals matched
Provide your reasoning first (step-by-step analysis following Steps 1–10), and then give the final structured result in the required JSON format:
{{
  "bus_type": One of [AHB, AXI, Avalon, Wishbone, Custom]
  "memory_interface": Single or Dual
  "confidence": High/Medium/Low (based on number of matches and comments)
}}

Dictionary of bus signals:
{{
    "Wishbone": {{
    "required": ["adr", "dat_i", "dat_o", "we", "cyc", "stb", "ack"],
    "optional": ["sel", "err", "rty", "stall"]
    }},

    "Avalon": {{
    "required": ["waitrequest", "address", "read", "readdata", "write", "writedata"],
    "optional": ["byteenable", "burstcount", "readdatavalid", "response", "chipselect"]
    }},

    "AXI": {{
    "required": ["araddr", "arvalid", "arready", "rdata", "rvalid", "rready",
                "awaddr", "awvalid", "awready", "wdata", "wvalid", "wready",
                "bresp", "bvalid", "bready"],
    "optional": ["arsize", "arburst", "arlen", "arprot", "arcache",
                "awsize", "awburst", "awlen", "awprot", "awcache",
                "wstrb", "wlast", "rlast"]
    }},

    "AHB": {{
    "required": ["haddr", "hwrite", "htrans", "hsize", "hready", "hresp"],
    "optional": ["hburst", "hprot", "hmastlock", "hmaster", "hexcl", "hexokay", "hwdata", "hrdata"]
    }}
}}

Module declaration:
{core_declaration}
"""

def send_prompt(prompt: str, model: str = 'qwen2.5:32b') -> tuple[bool, str]:
    """
    Sends a prompt to the specified server and receives the model's response.

    Args:
        prompt (str): The prompt to be sent to the model.
        model (str, optional): The model to use. Default is 'qwen2.5:32b'.

    Returns:
        tuple: A tuple containing a boolean value (indicating success)
               and the model's response as a string.
    """
    response = client.generate(prompt=prompt, model=model)

    # print("Full response:", response)  # Debug: show the full response

    if not response or 'response' not in response:
        return 0, ''

    return 1, response['response']

def filter_processor_interface_from_response(response: str) -> str:
    """
    It is expected a response with the following json format:
    {   
        "bus_type": One of [AHB, AXI, Avalon, Wishbone, Custom],
        "memory_interface": Single or Dual,
        "confidence": High/Medium/Low (based on number of matches and comments)
    }
    This function extracts and returns only the JSON part of the response.
    """
    # --- 1. Find last {...} block ---
    start = response.rfind("{")
    end   = response.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in response.")
    candidate = response[start:end+1]

    # --- 2. Small fixes for common LLM mistakes ---
    candidate = re.sub(r',\s*([}\]])', r'\1', candidate)      # remove trailing commas
    candidate = candidate.replace("'", '"')                   # single → double quotes
    candidate = re.sub(r'([,{]\s*)(\w+)(\s*):', r'\1"\2"\3:', candidate)  # quote keys
    candidate = re.sub(r'//.*$', '', candidate, flags=re.MULTILINE)  # remove JavaScript-style comments

    # --- 3. Try parsing ---
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        try:
            # fallback: try Python dict style with ast.literal_eval
            parsed = ast.literal_eval(candidate)
        except (ValueError, SyntaxError):
            raise ValueError(f"Failed to parse JSON from response: {candidate}")

    # --- 4. Keep only expected keys ---
    allowed_keys = {"bus_type", "memory_interface", "confidence"}
    filtered = {k: parsed[k] for k in allowed_keys if k in parsed}

    return filtered  


def extract_full_module(file_path, context=10):
    """
    Extracts full Verilog/SystemVerilog/VHDL module declarations (with ports)
    or VHDL entity declarations, plus N lines of context before and after.
    """
    lines = Path(file_path).read_text(encoding="utf-8").splitlines()

    # Patterns
    verilog_module_pattern = re.compile(r'^\s*module\s+\w+')
    vhdl_entity_pattern   = re.compile(r'^\s*entity\s+\w+')
    
    results = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if verilog_module_pattern.match(line):
            # start context
            start = max(0, i - context)
            # capture until the end of module declaration (line with ');')
            j = i
            while j < len(lines) and not re.search(r'\)\s*;', lines[j]):
                j += 1
            # include the line with ');
            if j < len(lines):
                j += 1
            end = min(len(lines), j + context)
            snippet = "\n".join(lines[start:end])
            results.append((i+1, snippet))
            i = j  # skip ahead
        elif vhdl_entity_pattern.match(line):
            # start context
            start = max(0, i - context)
            # capture until end <entity_name>;
            entity_name = re.search(r'entity\s+(\w+)', line).group(1)
            j = i
            # match both 'end <name>;' and 'end entity <name>;'
            while j < len(lines) and not re.search(
                rf'end\s+(entity\s+)?{entity_name}\s*;', lines[j], re.IGNORECASE
            ):
                j += 1
            if j < len(lines):
                j += 1
            end = min(len(lines), j + context)
            snippet = "\n".join(lines[start:end])
            results.append((i+1, snippet))
            i = j
        else:
            i += 1
    return results

def extract_interface_and_memory_ports(core_declaration, model='qwen2.5:32b'):
    
    prompt = find_interface_prompt.format(core_declaration=core_declaration)
    success, response = send_prompt(prompt, model=model)
    
    if not success:
        print("Error communicating with the server.")
        return None
    json_info = filter_processor_interface_from_response(response)
    return json_info

def main(file_path: str, context: int, model: str, output: str):
    matches = extract_full_module(file_path, context)

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
    interface_and_ports = extract_interface_and_memory_ports(matches[0][1], model=model)
    if not interface_and_ports:
        print("No bus interface type or memory port information found.")
        return
    else:
        print("=" * 60)
        print("Bus interface type and number of memory ports:")
        print("=" * 60)
        print(json.dumps(interface_and_ports, indent=2))

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(interface_and_ports, f, indent=2)
            print(f"\nOutput saved to {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find processor interface in HDL files.")
    parser.add_argument("file", help="Path to the HDL file (Verilog/SystemVerilog/VHDL)")
    parser.add_argument("-c", "--context", type=int, default=10, help="Number of context lines to include")
    parser.add_argument("-m", "--model", type=str, default="qwen2.5:32b", help="Model to use for the LLM")
    parser.add_argument("-o", "--output", type=str, help="Path to save the output JSON", required=False)
    args = parser.parse_args()

    main(args.file, args.context, args.model, args.output)
