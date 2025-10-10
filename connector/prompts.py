
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