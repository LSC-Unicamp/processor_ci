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

riscv_top #(
    .CORE_ID(CORE_ID),
    .MEM_CACHE_ADDR_MIN(MEM_CACHE_ADDR_MIN),
    .MEM_CACHE_ADDR_MAX(MEM_CACHE_ADDR_MAX)
) u_riscv_top (
    // Inputs
    .clk_i               (clk_i),             // 1 bit
    .rst_i               (rst_i),             // 1 bit
    .axi_i_awready_i     (axi_i_awready_i),   // 1 bit
    .axi_i_wready_i      (axi_i_wready_i),    // 1 bit
    .axi_i_bvalid_i      (axi_i_bvalid_i),    // 1 bit
    .axi_i_bresp_i       (axi_i_bresp_i),     // 2 bits
    .axi_i_bid_i         (axi_i_bid_i),       // 4 bits
    .axi_i_arready_i     (axi_i_arready_i),   // 1 bit
    .axi_i_rvalid_i      (axi_i_rvalid_i),    // 1 bit
    .axi_i_rdata_i       (axi_i_rdata_i),     // 32 bits
    .axi_i_rresp_i       (axi_i_rresp_i),     // 2 bits
    .axi_i_rid_i         (axi_i_rid_i),       // 4 bits
    .axi_i_rlast_i       (axi_i_rlast_i),     // 1 bit
    .axi_d_awready_i     (axi_d_awready_i),   // 1 bit
    .axi_d_wready_i      (axi_d_wready_i),    // 1 bit
    .axi_d_bvalid_i      (axi_d_bvalid_i),    // 1 bit
    .axi_d_bresp_i       (axi_d_bresp_i),     // 2 bits
    .axi_d_bid_i         (axi_d_bid_i),       // 4 bits
    .axi_d_arready_i     (axi_d_arready_i),   // 1 bit
    .axi_d_rvalid_i      (axi_d_rvalid_i),    // 1 bit
    .axi_d_rdata_i       (axi_d_rdata_i),     // 32 bits
    .axi_d_rresp_i       (axi_d_rresp_i),     // 2 bits
    .axi_d_rid_i         (axi_d_rid_i),       // 4 bits
    .axi_d_rlast_i       (axi_d_rlast_i),     // 1 bit
    .intr_i              (intr_i),            // 1 bit
    .reset_vector_i      (reset_vector_i),    // 32 bits

    // Outputs
    .axi_i_awvalid_o     (axi_i_awvalid_o),   // 1 bit
    .axi_i_awaddr_o      (axi_i_awaddr_o),    // 32 bits
    .axi_i_awid_o        (axi_i_awid_o),      // 4 bits
    .axi_i_awlen_o       (axi_i_awlen_o),     // 8 bits
    .axi_i_awburst_o     (axi_i_awburst_o),   // 2 bits
    .axi_i_wvalid_o      (axi_i_wvalid_o),    // 1 bit
    .axi_i_wdata_o       (axi_i_wdata_o),     // 32 bits
    .axi_i_wstrb_o       (axi_i_wstrb_o),     // 4 bits
    .axi_i_wlast_o       (axi_i_wlast_o),     // 1 bit
    .axi_i_bready_o      (axi_i_bready_o),    // 1 bit
    .axi_i_arvalid_o     (axi_i_arvalid_o),   // 1 bit
    .axi_i_araddr_o      (axi_i_araddr_o),    // 32 bits
    .axi_i_arid_o        (axi_i_arid_o),      // 4 bits
    .axi_i_arlen_o       (axi_i_arlen_o),     // 8 bits
    .axi_i_arburst_o     (axi_i_arburst_o),   // 2 bits
    .axi_i_rready_o      (axi_i_rready_o),    // 1 bit
    .axi_d_awvalid_o     (axi_d_awvalid_o),   // 1 bit
    .axi_d_awaddr_o      (axi_d_awaddr_o),    // 32 bits
    .axi_d_awid_o        (axi_d_awid_o),      // 4 bits
    .axi_d_awlen_o       (axi_d_awlen_o),     // 8 bits
    .axi_d_awburst_o     (axi_d_awburst_o),   // 2 bits
    .axi_d_wvalid_o      (axi_d_wvalid_o),    // 1 bit
    .axi_d_wdata_o       (axi_d_wdata_o),     // 32 bits
    .axi_d_wstrb_o       (axi_d_wstrb_o),     // 4 bits
    .axi_d_wlast_o       (axi_d_wlast_o),     // 1 bit
    .axi_d_bready_o      (axi_d_bready_o),    // 1 bit
    .axi_d_arvalid_o     (axi_d_arvalid_o),   // 1 bit
    .axi_d_araddr_o      (axi_d_araddr_o),    // 32 bits
    .axi_d_arid_o        (axi_d_arid_o),      // 4 bits
    .axi_d_arlen_o       (axi_d_arlen_o),     // 8 bits
    .axi_d_arburst_o     (axi_d_arburst_o),   // 2 bits
    .axi_d_rready_o      (axi_d_rready_o)     // 1 bit
);


endmodule
