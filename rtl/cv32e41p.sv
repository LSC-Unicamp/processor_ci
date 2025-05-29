`timescale 1ns / 1ps

`ifndef SIMULATION
`include "processor_ci_defines.vh"
`endif

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
    output logic [31:0] core_data_out, // Dados de entrada (para escrita)
    input  logic [31:0] core_data_in,  // Dados de saída (para leitura)

    input  logic        core_ack       // Confirmação da transação

    `ifdef ENABLE_SECOND_MEMORY
    output logic        data_mem_cyc;
    output logic        data_mem_stb;
    output logic        data_mem_we;
    output logic [31:0] data_mem_addr;
    output logic [31:0] data_mem_data_out;
    input  logic [31:0] data_mem_data_in;
    input  logic        data_mem_ack;
    `endif

    `endif
);
`ifndef SIMULATION
logic clk_core, rst_core;

// Fios do barramento entre Controller e Processor
logic        core_cyc;
logic        core_stb;
logic        core_we;
logic [31:0] core_addr;
logic [31:0] core_data_out;
logic [31:0] core_data_in;
logic        core_ack;

`ifdef ENABLE_SECOND_MEMORY
logic        data_mem_cyc;
logic        data_mem_stb;
logic        data_mem_we;
logic [31:0] data_mem_addr;
logic [31:0] data_mem_data_out;
logic [31:0] data_mem_data_in;
logic        data_mem_ack;
`endif
`endif

`ifndef SIMULATION
Controller #(
    .CLK_FREQ           (`CLOCK_FREQ),
    .BIT_RATE           (`BIT_RATE),
    .PAYLOAD_BITS       (`PAYLOAD_BITS),
    .BUFFER_SIZE        (`BUFFER_SIZE),
    .PULSE_CONTROL_BITS (`PULSE_CONTROL_BITS),
    .BUS_WIDTH          (`BUS_WIDTH),
    .WORD_SIZE_BY       (`WORD_SIZE_BY),
    .ID                 (`ID),
    .RESET_CLK_CYCLES   (`RESET_CLK_CYCLES),
    .MEMORY_FILE        (`MEMORY_FILE),
    .MEMORY_SIZE        (`MEMORY_SIZE)
) u_Controller (
    .clk                (sys_clk),

    .rst_n              (rst_n),
    
    // SPI signals
    .sck_i              (sck),
    .cs_i               (cs),
    .mosi_i             (mosi),
    .miso_o             (miso),
    
    // SPI callback signals
    .rw_i               (rw),
    .intr_o             (intr),
    
    // UART signals
    .rx                 (rx),
    .tx                 (tx),
    
    // Clock, reset, and bus signals
    .clk_core_o         (clk_core),
    .rst_core_o         (rst_core),
    
    // Barramento padrão (Wishbone)
    .core_cyc_i         (core_cyc),
    .core_stb_i         (core_stb),
    .core_we_i          (core_we),
    .core_addr_i        (core_addr),
    .core_data_i        (core_data_out),
    .core_data_o        (core_data_in),
    .core_ack_o         (core_ack)

    `ifdef ENABLE_SECOND_MEMORY
    ,
    .data_mem_cyc_i     (data_mem_cyc),
    .data_mem_stb_i     (data_mem_stb),
    .data_mem_we_i      (data_mem_we),
    .data_mem_addr_i    (data_mem_addr),
    .data_mem_data_i    (data_mem_data_out),
    .data_mem_data_o    (data_mem_data_in),
    .data_mem_ack_o     (data_mem_ack)
    `endif
);

// Core space

cv32e41p_core #(
    .PULP_XPULP         (0),
    .PULP_CLUSTER       (0),
    .FPU                (0),
    .Zcea               (0),
    .Zceb               (0),
    .Zcec               (0),
    .Zcee               (0),
    .ZFINX              (0),
    .NUM_MHPMCOUNTERS   (1)
) core_inst (
    // Clock and Reset
    .clk_i              (clk),
    .rst_ni             (rst_n),

    .pulp_clock_en_i    (1'b1),       // if not using PULP_CLUSTER, tie high or low
    .scan_cg_en_i       (1'b0),

    .boot_addr_i        (32'h0000_1000),
    .mtvec_addr_i       (32'h0000_2000),
    .dm_halt_addr_i     (32'h0000_3000),
    .hart_id_i          (32'd0),
    .dm_exception_addr_i(32'h0000_4000),

    // Instruction memory interface
    .instr_req_o        (instr_req),
    .instr_gnt_i        (instr_gnt),
    .instr_rvalid_i     (instr_rvalid),
    .instr_addr_o       (instr_addr),
    .instr_rdata_i      (instr_rdata),

    // Data memory interface
    .data_req_o         (data_req),
    .data_gnt_i         (data_gnt),
    .data_rvalid_i      (data_rvalid),
    .data_we_o          (data_we),
    .data_be_o          (data_be),
    .data_addr_o        (data_addr),
    .data_wdata_o       (data_wdata),
    .data_rdata_i       (data_rdata),

    // APU interface
    .apu_req_o          (),
    .apu_gnt_i          (1'b0),
    .apu_operands_o     (),
    .apu_op_o           (),
    .apu_flags_o        (),
    .apu_rvalid_i       (1'b0),
    .apu_result_i       (),
    .apu_flags_i        (),

    // Interrupts
    .irq_i              (1'b0),
    .irq_ack_o          (),
    .irq_id_o           (),

    // Debug interface
    .debug_req_i        (1'b0),
    .debug_havereset_o  (),
    .debug_running_o    (),
    .debug_halted_o     (),

    // CPU control
    .fetch_enable_i     (1'b1),
    .core_sleep_o       ()
);


endmodule
