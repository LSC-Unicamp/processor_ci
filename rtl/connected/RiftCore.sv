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

    output logic [3:0]  core_wstrb,
    output logic [31:0] core_addr,     // Endereço
    output logic [31:0] core_data_out, // Dados de entrada (para escrita)
    input  logic [31:0] core_data_in,  // Dados de saída (para leitura)

    input  logic        core_ack       // Confirmação da transação

    `ifdef ENABLE_SECOND_MEMORY
,
    output logic        data_mem_cyc,
    output logic        data_mem_stb,
    output logic        data_mem_we,
    output logic [3:0]  data_mem_wstrb,
    output logic [31:0] data_mem_addr,
    output logic [31:0] data_mem_data_out,
    input  logic [31:0] data_mem_data_in,
    input  logic        data_mem_ack
    `endif

    `endif
);
logic clk_core, rst_core;
`ifdef SIMULATION
assign clk_core = sys_clk;
assign rst_core = ~rst_n;
`else

// Fios do barramento entre Controller e Processor
logic        core_cyc;
logic        core_stb;
logic        core_we;
logic [3:0]  core_wstrb;
logic [31:0] core_addr;
logic [31:0] core_data_out;
logic [31:0] core_data_in;
logic        core_ack;

`ifdef ENABLE_SECOND_MEMORY
logic        data_mem_cyc;
logic        data_mem_stb;
logic        data_mem_we;
logic [3:0]  data_mem_wstrb;
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

riftCore i_riftCore(
	
	.isExternInterrupt(1'b0),
	.isRTimerInterrupt(1'b0),
	.isSoftwvInterrupt(1'b0),

	.MEM_AWID         (),
	.MEM_AWADDR       (CACHE_AWADDR),
	.MEM_AWLEN        (CACHE_AWLEN),
	.MEM_AWSIZE       (CACHE_AWSIZE),
	.MEM_AWBURST      (CACHE_AWBURST),
	.MEM_AWLOCK       (),
	.MEM_AWCACHE      (),
	.MEM_AWPROT       (),
	.MEM_AWQOS        (),
	.MEM_AWUSER       (),
	.MEM_AWVALID      (CACHE_AWVALID),
	.MEM_AWREADY      (CACHE_AWREADY),
	.MEM_WDATA        (CACHE_WDATA),
	.MEM_WSTRB        (CACHE_WSTRB),
	.MEM_WLAST        (CACHE_WLAST),
	.MEM_WUSER        (),
	.MEM_WVALID       (CACHE_WVALID),
	.MEM_WREADY       (CACHE_WREADY),
	.MEM_BID          (1'b0),
	.MEM_BRESP        (CACHE_BRESP),
	.MEM_BUSER        (1'b0),
	.MEM_BVALID       (CACHE_BVALID),
	.MEM_BREADY       (CACHE_BREADY),
	.MEM_ARID         (),
	.MEM_ARADDR       (CACHE_ARADDR),
	.MEM_ARLEN        (CACHE_ARLEN),
	.MEM_ARSIZE       (CACHE_ARSIZE),
	.MEM_ARBURST      (CACHE_ARBURST),
	.MEM_ARLOCK       (),
	.MEM_ARCACHE      (),
	.MEM_ARPROT       (),
	.MEM_ARQOS        (),
	.MEM_ARUSER       (),
	.MEM_ARVALID      (CACHE_ARVALID),
	.MEM_ARREADY      (CACHE_ARREADY),
	.MEM_RID          (1'b0),
	.MEM_RDATA        (CACHE_RDATA),
	.MEM_RRESP        (CACHE_RRESP),
	.MEM_RLAST        (CACHE_RLAST),
	.MEM_RUSER        (CACHE_RUSER),
	.MEM_RVALID       (CACHE_RVALID),
	.MEM_RREADY       (CACHE_RREADY),

	.SYS_AWADDR      (SYS_AWADDR),
	.SYS_AWVALID     (SYS_AWVALID),
	.SYS_AWREADY     (SYS_AWREADY),
	.SYS_WDATA       (SYS_WDATA),
	.SYS_WSTRB       (SYS_WSTRB),
	.SYS_WVALID      (SYS_WVALID),
	.SYS_WREADY      (SYS_WREADY),
	.SYS_BRESP       (SYS_BRESP),
	.SYS_BVALID      (SYS_BVALID),
	.SYS_BREADY      (SYS_BREADY),
	.SYS_ARADDR      (SYS_ARADDR),
	.SYS_ARVALID     (SYS_ARVALID),
	.SYS_ARREADY     (SYS_ARREADY),
	.SYS_RDATA       (SYS_RDATA),
	.SYS_RRESP       (SYS_RRESP),
	.SYS_RVALID      (SYS_RVALID),
	.SYS_RREADY      (SYS_RREADY),

	.CLK(CLK),
	.RSTn(RSTn)
	
);

endmodule
