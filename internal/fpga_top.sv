`timescale 1ns / 1ps

`include "processor_ci_defines.vh"

`define SYNTH
`define SYNTHESIS

module fpga_top(
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

processorci_top ptop (
    `ifdef HIGH_CLK
    .sys_clk (clk_o),
    `else
    .sys_clk (clk),
    `endif

    .rst_n   (rst_n),   // Reset do sistema

    // SPI signals
    .sck     (sck),
    .cs      (cs),
    .mosi    (mosi),
    .miso    (miso),
    
    // SPI callback signals
    .rw      (rw),
    .intr    (intr),
    
    // UART signals
    .rx      (rx),
    .tx      (tx)
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