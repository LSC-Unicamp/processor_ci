`timescale 1ns / 1ps

`ifndef SIMULATION
`include "processor_ci_defines.vh"
`endif

`define ENABLE_SECOND_MEMORY 1 // Habilita o segundo barramento de memória

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
    output logic [31:0] core_data_out, // Dados de entrada (para escrita)
    input  logic [31:0] core_data_in,  // Dados de saída (para leitura)

    input  logic        core_ack       // Confirmação da transação

    `ifdef ENABLE_SECOND_MEMORY
,
    output logic        data_mem_cyc,
    output logic        data_mem_stb,
    output logic        data_mem_we,
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

// AXI interface: Instruction memory
logic [3:0]  axi_i_awid, axi_i_arid;
logic [31:0] axi_i_awaddr, axi_i_araddr, axi_i_wdata;
logic [3:0]  axi_i_wstrb;
logic        axi_i_awvalid, axi_i_wvalid, axi_i_bready;
logic        axi_i_arvalid, axi_i_rready;
logic        axi_i_awready, axi_i_wready, axi_i_bvalid;
logic [1:0]  axi_i_bresp;
logic [3:0]  axi_i_bid;
logic        axi_i_arready, axi_i_rvalid;
logic [31:0] axi_i_rdata;
logic [1:0]  axi_i_rresp;
logic [3:0]  axi_i_rid;

// AXI interface: Data memory
logic [3:0]  axi_d_awid, axi_d_arid;
logic [31:0] axi_d_awaddr, axi_d_araddr, axi_d_wdata;
logic [3:0]  axi_d_wstrb;
logic        axi_d_awvalid, axi_d_wvalid, axi_d_bready;
logic        axi_d_arvalid, axi_d_rready;
logic        axi_d_awready, axi_d_wready, axi_d_bvalid;
logic [1:0]  axi_d_bresp;
logic [3:0]  axi_d_bid;
logic        axi_d_arready, axi_d_rvalid;
logic [31:0] axi_d_rdata;
logic [1:0]  axi_d_rresp;
logic [3:0]  axi_d_rid;


axi4_to_wishbone_simple #(
    .ADDR_WIDTH(32),
    .DATA_WIDTH(32),
    .ID_WIDTH(4)
) Instr_mem (
    .clk              (clk_core),
    .rst_n            (~rst_core),

    // AXI Write Address Channel
    .S_AXI_AWID       (axi_i_awid),
    .S_AXI_AWADDR     (axi_i_awaddr),
    .S_AXI_AWVALID    (axi_i_awvalid),
    .S_AXI_AWREADY    (axi_i_awready),

    // AXI Write Data Channel
    .S_AXI_WDATA      (axi_i_wdata),
    .S_AXI_WSTRB      (axi_i_wstrb),
    .S_AXI_WVALID     (axi_i_wvalid),
    .S_AXI_WREADY     (axi_i_wready),

    // AXI Write Response Channel
    .S_AXI_BID        (axi_i_bid),
    .S_AXI_BRESP      (axi_i_bresp),
    .S_AXI_BVALID     (axi_i_bvalid),
    .S_AXI_BREADY     (axi_i_bready),

    // AXI Read Address Channel
    .S_AXI_ARID       (axi_i_arid),
    .S_AXI_ARADDR     (axi_i_araddr),
    .S_AXI_ARVALID    (axi_i_arvalid),
    .S_AXI_ARREADY    (axi_i_arready),

    // AXI Read Data Channel
    .S_AXI_RID        (axi_i_rid),
    .S_AXI_RDATA      (axi_i_rdata),
    .S_AXI_RRESP      (axi_i_rresp),
    .S_AXI_RVALID     (axi_i_rvalid),
    .S_AXI_RREADY     (axi_i_rready),

    // Wishbone Interface
    .WB_CYC           (core_cyc),
    .WB_STB           (core_stb),
    .WB_WE            (core_we),
    .WB_ADDR          (core_addr),
    .WB_WDATA         (core_data_out),
    .WB_SEL           (4'b1111), // write strobe = all bytes enabled
    .WB_RDATA         (core_data_in),
    .WB_ACK           (core_ack)
);

axi4_to_wishbone_simple #(
    .ADDR_WIDTH(32),
    .DATA_WIDTH(32),
    .ID_WIDTH(4)
) Data_mem (
    .clk              (clk_core),
    .rst_n            (~rst_core),

    // AXI Write Address Channel
    .S_AXI_AWID       (axi_d_awid),
    .S_AXI_AWADDR     (axi_d_awaddr),
    .S_AXI_AWVALID    (axi_d_awvalid),
    .S_AXI_AWREADY    (axi_d_awready),

    // AXI Write Data Channel
    .S_AXI_WDATA      (axi_d_wdata),
    .S_AXI_WSTRB      (axi_d_wstrb),
    .S_AXI_WVALID     (axi_d_wvalid),
    .S_AXI_WREADY     (axi_d_wready),

    // AXI Write Response Channel
    .S_AXI_BID        (axi_d_bid),
    .S_AXI_BRESP      (axi_d_bresp),
    .S_AXI_BVALID     (axi_d_bvalid),
    .S_AXI_BREADY     (axi_d_bready),

    // AXI Read Address Channel
    .S_AXI_ARID       (axi_d_arid),
    .S_AXI_ARADDR     (axi_d_araddr),
    .S_AXI_ARVALID    (axi_d_arvalid),
    .S_AXI_ARREADY    (axi_d_arready),

    // AXI Read Data Channel
    .S_AXI_RID        (axi_d_rid),
    .S_AXI_RDATA      (axi_d_rdata),
    .S_AXI_RRESP      (axi_d_rresp),
    .S_AXI_RVALID     (axi_d_rvalid),
    .S_AXI_RREADY     (axi_d_rready),

    // Wishbone Interface
    .WB_CYC           (data_mem_cyc),
    .WB_STB           (data_mem_stb),
    .WB_WE            (data_mem_we),
    .WB_ADDR          (data_mem_addr),
    .WB_WDATA         (data_mem_data_out),
    .WB_SEL           (4'b1111),
    .WB_RDATA         (data_mem_data_in),
    .WB_ACK           (data_mem_ack)
);



riscv_top #(
    .CORE_ID                  (0),
    .ICACHE_AXI_ID            (0),
    .DCACHE_AXI_ID            (1),
    .SUPPORT_BRANCH_PREDICTION(1),
    .SUPPORT_MULDIV           (1),
    .SUPPORT_SUPER            (0),
    .SUPPORT_MMU              (0),
    .SUPPORT_DUAL_ISSUE       (1),
    .SUPPORT_LOAD_BYPASS      (1),
    .SUPPORT_MUL_BYPASS       (1),
    .SUPPORT_REGFILE_XILINX   (0),
    .EXTRA_DECODE_STAGE       (0),
    .MEM_CACHE_ADDR_MIN       (32'h00000000),
    .MEM_CACHE_ADDR_MAX       (32'h8fffffff),
    .NUM_BTB_ENTRIES          (32),
    .NUM_BTB_ENTRIES_W        (5),
    .NUM_BHT_ENTRIES          (512),
    .NUM_BHT_ENTRIES_W        (9),
    .RAS_ENABLE               (1),
    .GSHARE_ENABLE            (0),
    .BHT_ENABLE               (1),
    .NUM_RAS_ENTRIES          (8),
    .NUM_RAS_ENTRIES_W        (3)
) u_riscv_top (
    .clk_i              (clk_core),
    .rst_i              (rst_core),
    .intr_i             (intr),               // IRQ externa

    // Reset vector
    .reset_vector_i     (32'h00000000),

    // AXI4 INSTRUCTION interface
    .axi_i_awvalid_o    (axi_i_awvalid),
    .axi_i_awaddr_o     (axi_i_awaddr),
    .axi_i_awid_o       (axi_i_awid),
    .axi_i_awlen_o      (), // opcional
    .axi_i_awburst_o    (), // opcional
    .axi_i_wvalid_o     (axi_i_wvalid),
    .axi_i_wdata_o      (axi_i_wdata),
    .axi_i_wstrb_o      (axi_i_wstrb),
    .axi_i_wlast_o      (), // opcional
    .axi_i_bready_o     (axi_i_bready),
    .axi_i_arvalid_o    (axi_i_arvalid),
    .axi_i_araddr_o     (axi_i_araddr),
    .axi_i_arid_o       (axi_i_arid),
    .axi_i_arlen_o      (), // opcional
    .axi_i_arburst_o    (), // opcional
    .axi_i_rready_o     (axi_i_rready),
    .axi_i_awready_i    (axi_awready),
    .axi_i_wready_i     (axi_wready),
    .axi_i_bvalid_i     (axi_bvalid),
    .axi_i_bresp_i      (axi_bresp),
    .axi_i_bid_i        (axi_bid),
    .axi_i_arready_i    (axi_arready),
    .axi_i_rvalid_i     (axi_rvalid),
    .axi_i_rdata_i      (axi_rdata),
    .axi_i_rresp_i      (axi_rresp),
    .axi_i_rid_i        (axi_rid),
    .axi_i_rlast_i      (1'b1), // se não usa bursts, sempre 1

    // AXI4 DATA interface
    .axi_d_awvalid_o    (axi_d_awvalid),
    .axi_d_awaddr_o     (axi_d_awaddr),
    .axi_d_awid_o       (axi_d_awid),
    .axi_d_awlen_o      (), // opcional
    .axi_d_awburst_o    (), // opcional
    .axi_d_wvalid_o     (axi_d_wvalid),
    .axi_d_wdata_o      (axi_d_wdata),
    .axi_d_wstrb_o      (axi_d_wstrb),
    .axi_d_wlast_o      (), // opcional
    .axi_d_bready_o     (axi_d_bready),
    .axi_d_arvalid_o    (axi_d_arvalid),
    .axi_d_araddr_o     (axi_d_araddr),
    .axi_d_arid_o       (axi_d_arid),
    .axi_d_arlen_o      (), // opcional
    .axi_d_arburst_o    (), // opcional
    .axi_d_rready_o     (axi_d_rready),
    .axi_d_awready_i    (axi_awready),
    .axi_d_wready_i     (axi_wready),
    .axi_d_bvalid_i     (axi_bvalid),
    .axi_d_bresp_i      (axi_bresp),
    .axi_d_bid_i        (axi_bid),
    .axi_d_arready_i    (axi_arready),
    .axi_d_rvalid_i     (axi_rvalid),
    .axi_d_rdata_i      (axi_rdata),
    .axi_d_rresp_i      (axi_rresp),
    .axi_d_rid_i        (axi_rid),
    .axi_d_rlast_i      (1'b1) // se não usa bursts, sempre 1
);



endmodule
