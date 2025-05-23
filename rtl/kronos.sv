
`timescale 1ns / 1ps
`include "processor_ci_defines.vh"
`define ENABLE_SECOND_MEMORY 1

module processorci_top (
    `ifdef DIFERENCIAL_CLK
    input  logic clk_ref_p,
    input  logic clk_ref_n,
    `else
    input  logic clk,
    `endif

    input  logic rst,

    // UART pins
    input  logic rx,
    output logic tx
    `ifndef DIFERENCIAL_CLK
    ,

    // SPI pins
    input  logic sck,
    input  logic cs,
    input  logic mosi,
    output logic miso,

    //SPI control pins
    input  logic rw,
    output logic intr
    `endif
);

logic clk_o, rst_n;
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
    `ifdef HIGH_CLK
    .clk                (clk_o),
    `else
    .clk                (clk),
    `endif

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

// Instância do processador kronos_core
kronos_core #(
    .BOOT_ADDR             (32'h00000000),
    .FAST_BRANCH           (1'b1),
    .EN_COUNTERS           (1'b1),
    .EN_COUNTERS64B        (1'b1),
    .CATCH_ILLEGAL_INSTR   (1'b1),
    .CATCH_MISALIGNED_JMP  (1'b1),
    .CATCH_MISALIGNED_LDST (1'b1)
) kronos_core_inst (
    .clk            (clk_core),
    .rstz           (~rst_core),

    // Interface de instruções
    .instr_addr     (core_addr),
    .instr_data     (core_data_in),
    .instr_req      (core_stb),
    .instr_ack      (core_ack),

    // Interface de dados
    .data_addr      (data_mem_addr),
    .data_rd_data   (data_mem_data_in),
    .data_wr_data   (data_mem_data_out),
    .data_mask      (), // depende da largura de escrita; pode ser ajustado se necessário
    .data_wr_en     (data_mem_we),
    .data_req       (data_mem_stb),
    .data_ack       (data_mem_ack),

    // Interrupções
    .software_interrupt (1'b0),
    .timer_interrupt    (1'b0),
    .external_interrupt (1'b0)
);


// Clock inflaestructure

initial begin
    clk_o = 1'b0; // 50mhz or 100mhz
end

`ifdef DIFERENCIAL_CLK
logic clk_ref; // Sinal de clock single-ended

// Instância do buffer diferencial
IBUFDS #(
    .DIFF_TERM    ("FALSE"), // Habilita ou desabilita o terminador diferencial
    .IBUF_LOW_PWR ("TRUE"),  // Ativa o modo de baixa potência
    .IOSTANDARD   ("DIFF_SSTL15")
) ibufds_inst (
    .O  (clk_ref),   // Clock single-ended de saída
    .I  (clk_ref_p), // Entrada diferencial positiva
    .IB (clk_ref_n)  // Entrada diferencial negativa
);


always_ff @(posedge clk_ref) begin
    clk_o <= ~clk_o;
end
`else
always_ff @(posedge clk) begin
    clk_o <= ~clk_o;
end
`endif


// Reset Inflaestructure


ResetBootSystem #(
    .CYCLES(20)
) ResetBootSystem(
    `ifdef HIGH_CLK
    .clk     (clk_o),
    `else
    .clk     (clk),
    `endif
    
    .rst_n_o (rst_n)
);
    
endmodule


