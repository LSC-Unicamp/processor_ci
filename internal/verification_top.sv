`timescale 1ns / 1ps

`undef TRACE_EXECUTION
`define SYNTHESIS 1

module verification_top (
    input logic clk,  // Clock de sistema
    input logic rst_n // Reset do sistema
);


// Fios do barramento entre Controller e a primeira memória
logic        core_cyc;
logic        core_stb;
logic        core_we;
logic [31:0] core_addr;
logic [31:0] core_data_out;
logic [31:0] core_data_in;
logic        core_ack;

`ifdef ENABLE_SECOND_MEMORY
// Fios do barramento entre Controller e Second Memory
logic        data_mem_cyc;
logic        data_mem_stb;
logic        data_mem_we;
logic [31:0] data_mem_addr;
logic [31:0] data_mem_data_out;
logic [31:0] data_mem_data_in;
logic        data_mem_ack;
`endif


processorci_top ptop (
    .sys_clk           (clk),     
    .rst_n             (rst_n),   

    .core_cyc          (core_cyc),
    .core_stb          (core_stb),
    .core_we           (core_we),
    .core_addr         (core_addr),
    .core_data_out     (core_data_out),
    .core_data_in      (core_data_in),
    .core_ack          (core_ack)

    `ifdef ENABLE_SECOND_MEMORY
    ,
    .data_mem_cyc      (data_mem_cyc),
    .data_mem_stb      (data_mem_stb),
    .data_mem_we       (data_mem_we),
    .data_mem_addr     (data_mem_addr),
    .data_mem_data_out (data_mem_data_out),
    .data_mem_data_in  (data_mem_data_in),
    .data_mem_ack      (data_mem_ack)
    `endif
);

// Instância da primeira memória
Memory #(
    .MEMORY_FILE ("/eda/processor_ci/internal/memory.hex"), // Arquivo de memória inicial
    .MEMORY_SIZE (4096)
) Memory (
    .clk    (clk),
    
    .cyc_i  (core_cyc),
    .stb_i  (core_stb),
    .we_i   (core_we),
    
    .addr_i (core_addr),
    .data_i (core_data_out),
    .data_o (core_data_in),

    .ack_o  (core_ack)
);

`ifdef ENABLE_SECOND_MEMORY
// Instância da segunda memória
Memory #(
    .MEMORY_FILE (""),
    .MEMORY_SIZE (4096)
) SecondMemory (
    .clk    (clk),
    
    .cyc_i  (data_mem_cyc),
    .stb_i  (data_mem_stb),
    .we_i   (data_mem_we),

    .addr_i (data_mem_addr),
    .data_i (data_mem_data_out),
    .data_o (data_mem_data_in),

    .ack_o  (data_mem_ack)
);
`endif

endmodule
