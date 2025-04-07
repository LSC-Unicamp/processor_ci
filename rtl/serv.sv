`timescale 1ns / 1ps
`include "processor_ci_defines.vh"
// `define ENABLE_SECOND_MEMORY 1

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

serv_top #(
    .RESET_PC       (0),
    .PRE_REGISTER   (1),
    .RESET_STRATEGY ("MINI"),
    .WITH_CSR       (1),
    .DEBUG          (0),
    .MDU            (0),
    .COMPRESSED     (0),
    .ALIGN          (0),
    .W              (1)
) cpu (
    .clk          (clk_core),
    .i_rst        (rst_core),
    .i_timer_irq  (0),

    .o_rf_rreq    (),
    .o_rf_wreq    (),
    .i_rf_ready   (),
    .o_wreg0      (),
    .o_wreg1      (),
    .o_wen0       (),
    .o_wen1       (),
    .o_wdata0     (),
    .o_wdata1     (),
    .o_rreg0      (),
    .o_rreg1      (),
    .i_rdata0     (),
    .i_rdata1     (),

    .o_ibus_adr   (),
    .o_ibus_cyc   (),
    .i_ibus_rdt   (),
    .i_ibus_ack   (),

    .o_dbus_adr   (),
    .o_dbus_dat   (),
    .o_dbus_sel   (),
    .o_dbus_we    (),
    .o_dbus_cyc   (),
    .i_dbus_rdt   (),
    .i_dbus_ack   (),

    //Extension
    .o_ext_funct3 (),
    .i_ext_ready  (),
    .i_ext_rd     (),
    .o_ext_rs1    (),
    .o_ext_rs2    (),
    //MDU
    .o_mdu_valid  ()
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
