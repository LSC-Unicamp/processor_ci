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

core inst_core
(
    .clk              (clk),
    .rst_n            (rst_n),
    .halt_req_i       (halt_req),
    .hx_valid         (hx_valid),
    .soft_rst         (soft_rst_en),
    .core_ex_trap_valid  (core_ex_trap_valid),
    .core_ex_trap_ready  (core_ex_trap_ready),
//m1 内核
    .core_axi_awaddr  (core_axi_awaddr ),
    .core_axi_awprot  (core_axi_awprot ),
    .core_axi_awvalid (core_axi_awvalid),
    .core_axi_awready (core_axi_awready),
    .core_axi_wdata   (core_axi_wdata  ),
    .core_axi_wstrb   (core_axi_wstrb  ),
    .core_axi_wvalid  (core_axi_wvalid ),
    .core_axi_wready  (core_axi_wready ),
    .core_axi_bresp   (core_axi_bresp  ),
    .core_axi_bvalid  (core_axi_bvalid ),
    .core_axi_bready  (core_axi_bready ),
    .core_axi_araddr  (core_axi_araddr ),
    .core_axi_arprot  (core_axi_arprot ),
    .core_axi_arvalid (core_axi_arvalid),
    .core_axi_arready (core_axi_arready),
    .core_axi_rdata   (core_axi_rdata  ),
    .core_axi_rresp   (core_axi_rresp  ),
    .core_axi_rvalid  (core_axi_rvalid ),
    .core_axi_rready  (core_axi_rready ),
//s0 iram指令存储器
    .iram_axi_awaddr  (iram_axi_awaddr ),
    .iram_axi_awprot  (3'h0),
    .iram_axi_awvalid (iram_axi_awvalid),
    .iram_axi_awready (iram_axi_awready),
    .iram_axi_wdata   (iram_axi_wdata  ),
    .iram_axi_wstrb   (iram_axi_wstrb  ),
    .iram_axi_wvalid  (iram_axi_wvalid ),
    .iram_axi_wready  (iram_axi_wready ),
    .iram_axi_bresp   (),
    .iram_axi_bvalid  (),
    .iram_axi_bready  (1'b0),
    .iram_axi_araddr  (iram_axi_araddr ),
    .iram_axi_arprot  (3'h0),
    .iram_axi_arvalid (iram_axi_arvalid),
    .iram_axi_arready (iram_axi_arready),
    .iram_axi_rdata   (iram_axi_rdata  ),
    .iram_axi_rresp   (),
    .iram_axi_rvalid  (iram_axi_rvalid ),
    .iram_axi_rready  (iram_axi_rready )
);

endmodule
