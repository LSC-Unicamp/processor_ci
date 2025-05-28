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
    output logic [31:0] core_data_out,     // Dados de entrada (para escrita)
    input  logic [31:0] core_data_in,   // Dados de saída (para leitura)

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
`endif
// Core space

// Instância do tinyriscv
tinyriscv u_tinyriscv (
    .clk               (clk_core),
    .rst               (rst_core),

    // Barramento de memória de dados
    .rib_ex_addr_o     (data_mem_addr),
    .rib_ex_data_i     (data_mem_data_in),
    .rib_ex_data_o     (data_mem_data_out),
    .rib_ex_req_o      (data_mem_stb),
    .rib_ex_we_o       (data_mem_we),

    // Barramento de memória de instruções
    .rib_pc_addr_o     (core_addr),
    .rib_pc_data_i     (core_data_in),

    // Sinais JTAG (não utilizados aqui)
    .jtag_reg_addr_i   (5'b0),
    .jtag_reg_data_i   (32'b0),
    .jtag_reg_we_i     (1'b0),
    .jtag_reg_data_o   (),

    .rib_hold_flag_i   (1'b0),
    .jtag_halt_flag_i  (1'b0),
    .jtag_reset_flag_i (1'b0),

    // Interrupções
    .int_i             (32'b0)
);

assign core_cyc      = 1'b1;         // Sempre ativo para fetch
assign core_stb      = 1'b1;         // Sempre requisitando instruções
assign core_we       = 1'b0;         // Nunca escreve via fetch
assign core_data_out = 32'd0;        // Não escreve no barramento de instruções
assign core_ack      = 1'b1;         // ACK constante (caso sem espera)
assign data_mem_cyc  = data_mem_stb; // simples ciclo igual a strobe
    
endmodule



