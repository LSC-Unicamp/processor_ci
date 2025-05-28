`timescale 1ns / 1ps

`ifndef SIMULATION
`include "processor_ci_defines.vh"
`endif

`define ENABLE_SECOND_MEMORY 1 // Habilita o segundo barramento de memória

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
    output logic [31:0] core_data,     // Dados de entrada (para escrita)
    input  logic [31:0] core_data,     // Dados de saída (para leitura)

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
    .core_we_i          (1'b0), //core_we = 0
    .core_addr_i        (core_addr),
    .core_data_i        (1'b0), // core_data_out = 0 because we never write to instruction memory
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
logic core_cyc_stb;
logic data_mem_cyc_stb;

aukv aukv_inst(
    .i_clk          (clk_core),
    .i_rstn         (~rst_core),       // Reset ativo baixo
    .i_irq          (1'b0),              // IRQ fixo como inativo
    .o_ack          (),                  // Sem interligação de ACK

    // Sinais de memória de dados
    .o_data_mem_en      (data_mem_cyc_stb),
    .o_data_mem_we      (data_mem_we),
    .o_data_mem_addr    (data_mem_addr),
    .o_data_mem_data    (data_mem_data_out),
    .o_data_mem_strobe  (),              // Sem strobe
    .i_data_mem_valid   (data_mem_ack),
    .i_data_mem_data    (data_mem_data_in),

    // Sinais de memória de instruções
    .o_code_mem_en      (core_cyc_stb),
    .o_code_mem_addr    (core_addr),
    .i_code_mem_data    (core_data_in),
    .i_code_mem_valid   (core_ack)
);


assign core_cyc = core_cyc_stb;
assing core_stb = core_cyc_stb;
assign data_mem_cyc = data_mem_cyc_stb;
assign data_mem_stb = data_mem_cyc_stb;
assign core_we = 1'b0; // core_we = 0
assign core_data_out = 32'b0; // core_data_out = 0 because we never write to instruction memory


endmodule
