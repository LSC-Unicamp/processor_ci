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

riscv_core
u_dut
//-----------------------------------------------------------------
// Ports
//-----------------------------------------------------------------
(
    // Inputs
     .clk_i            (clk_core)
    ,.rst_i            (rst_core)
    ,.mem_d_data_rd_i  (data_read)
    ,.mem_d_accept_i   (1'b1)
    ,.mem_d_ack_i      (1'b1)
    ,.mem_d_error_i    (1'b0)
    ,.mem_d_resp_tag_i ()
    ,.mem_i_accept_i   (1'b1)
    ,.mem_i_valid_i    (1'b1)
    ,.mem_i_error_i    (1'b0)
    ,.mem_i_inst_i     ()
    ,.intr_i           (1'b0)
    ,.reset_vector_i   (32'h80000000)
    ,.cpu_id_i         ('b0)

    // Outputs
    ,.mem_d_addr_o       ()
    ,.mem_d_data_wr_o    ()
    ,.mem_d_rd_o         ()
    ,.mem_d_wr_o         ()
    ,.mem_d_cacheable_o  ()
    ,.mem_d_req_tag_o    ()
    ,.mem_d_invalidate_o ()
    ,.mem_d_writeback_o  ()
    ,.mem_d_flush_o      ()
    ,.mem_i_rd_o         ()
    ,.mem_i_flush_o      ()
    ,.mem_i_invalidate_o ()
    ,.mem_i_pc_o         ()
);


// Clock inflaestructure

initial begin
    clk_o = 1'b0; // 50mhz or 100mhz
end

`ifdef DIFERENCIAL_CLK
logic clk_ref; // Sinal de clock single-ended

// Differential clock input
IBUFDS #(
    .DIFF_TERM    ("FALSE"), // Enable or disable differential terminator
    .IBUF_LOW_PWR ("TRUE"),  // Enable low power mode
    .IOSTANDARD   ("DIFF_SSTL15")
) ibufds_inst (
    .O  (clk_ref),   // Clock single-ended output
    .I  (clk_ref_p), // Differential input positive
    .IB (clk_ref_n)  // Differential input negative
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
