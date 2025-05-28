`timescale 1ns / 1ps

`include "processor_ci_defines.vh"

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
    .sck   (sck),
    .cs    (cs),
    .mosi  (mosi),
    .miso  (miso),
    
    // SPI callback signals
    .rw    (rw),
    .intr  (intr),
    
    // UART signals
    .rx      (rx),
    .tx      (tx)
);



endmodule