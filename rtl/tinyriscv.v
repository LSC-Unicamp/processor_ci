`timescale 1ns / 1ps

`ifndef SIMULATION
`include "processor_ci_defines.vh"
`endif

`define ENABLE_SECOND_MEMORY 1 // Enable second memory bus

module processorci_top (
    input  sys_clk,    // System clock
    input  rst_n,      // System reset

    `ifndef SIMULATION
    // UART pins
    input  rx,
    output tx,

    // SPI pins
    input  sck,
    input  cs,
    input  mosi,
    output miso,

    // SPI control pins
    input  rw,
    output intr

    `else
    output core_cyc,      // Active transaction
    output core_stb,      // Active request
    output core_we,       // 1 = write, 0 = read

    output [3:0] core_wstrb,
    output [31:0] core_addr,
    output [31:0] core_data_out,
    input  [31:0] core_data_in,
    input         core_ack

    `ifdef ENABLE_SECOND_MEMORY
    ,
    output        data_mem_cyc,
    output        data_mem_stb,
    output        data_mem_we,
    output [3:0]  data_mem_wstrb,
    output [31:0] data_mem_addr,
    output [31:0] data_mem_data_out,
    input  [31:0] data_mem_data_in,
    input         data_mem_ack
    `endif

    `endif
);

// Internal clock and reset
wire clk_core;
wire rst_core;

`ifdef SIMULATION
assign clk_core = sys_clk;
assign rst_core = ~rst_n;
`else

// Wires between Controller and Processor
wire        core_cyc;
wire        core_stb;
wire        core_we;
wire [3:0]  core_wstrb;
wire [31:0] core_addr;
wire [31:0] core_data_out;
wire [31:0] core_data_in;
wire        core_ack;

`ifdef ENABLE_SECOND_MEMORY
wire        data_mem_cyc;
wire        data_mem_stb;
wire        data_mem_we;
wire [3:0]  data_mem_wstrb;
wire [31:0] data_mem_addr;
wire [31:0] data_mem_data_out;
wire [31:0] data_mem_data_in;
wire        data_mem_ack;
`endif
`endif

`ifndef SIMULATION
Controller u_Controller (
    .clk        (sys_clk),
    .rst_n      (rst_n),

    // SPI signals
    .sck_i      (sck),
    .cs_i       (cs),
    .mosi_i     (mosi),
    .miso_o     (miso),

    // SPI callback
    .rw_i       (rw),
    .intr_o     (intr),

    // UART
    .rx         (rx),
    .tx         (tx),

    // Core clock and reset
    .clk_core_o (clk_core),
    .rst_core_o (rst_core),

    // Standard bus (Wishbone)
    .core_cyc_i  (core_cyc),
    .core_stb_i  (core_stb),
    .core_we_i   (core_we),
    .core_addr_i (core_addr),
    .core_data_i (core_data_out),
    .core_data_o (core_data_in),
    .core_ack_o  (core_ack)

    `ifdef ENABLE_SECOND_MEMORY
    ,
    .data_mem_cyc_i   (data_mem_cyc),
    .data_mem_stb_i   (data_mem_stb),
    .data_mem_we_i    (data_mem_we),
    .data_mem_addr_i  (data_mem_addr),
    .data_mem_data_i  (data_mem_data_out),
    .data_mem_data_o  (data_mem_data_in),
    .data_mem_ack_o   (data_mem_ack)
    `endif
);
`endif

// TinyRV32 core
tinyriscv u_tinyriscv (
    .clk               (clk_core),
    .rst               (~rst_core),

    // Data memory bus
    .rib_ex_addr_o     (data_mem_addr),
    .rib_ex_data_i     (data_mem_data_in),
    .rib_ex_data_o     (data_mem_data_out),
    .rib_ex_req_o      (data_mem_stb),
    .rib_ex_we_o       (data_mem_we),

    // Instruction memory bus
    .rib_pc_addr_o     (core_addr),
    .rib_pc_data_i     (core_data_in),

    // JTAG signals
    .jtag_reg_addr_i   (5'b0),
    .jtag_reg_data_i   (32'b0),
    .jtag_reg_we_i     (1'b0),
    .jtag_reg_data_o   (),

    .rib_hold_flag_i   (1'b0),
    .jtag_halt_flag_i  (1'b0),
    .jtag_reset_flag_i (1'b0),

    // Interrupts
    .int_i             (32'b0)
);

// Assign fetch bus signals
assign core_cyc      = 1'b1;
assign core_stb      = 1'b1;
assign core_we       = 1'b0;
assign core_data_out = 32'd0;
assign data_mem_cyc  = data_mem_stb;

endmodule
