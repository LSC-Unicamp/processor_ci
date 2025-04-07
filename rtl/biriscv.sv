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

riscv_top #(
     .CORE_ID                (0),
     .ICACHE_AXI_ID          (0),
     .DCACHE_AXI_ID          (0),
     .SUPPORT_BRANCH_PREDICTION (1),
     .SUPPORT_MULDIV         (1),
     .SUPPORT_SUPER          (0),
     .SUPPORT_MMU            (0),
     .SUPPORT_DUAL_ISSUE     (1),
     .SUPPORT_LOAD_BYPASS    (1),
     .SUPPORT_MUL_BYPASS     (1),
     .SUPPORT_REGFILE_XILINX (0),
     .EXTRA_DECODE_STAGE     (0),
     .MEM_CACHE_ADDR_MIN     (32'h00000000),
     .MEM_CACHE_ADDR_MAX     (32'h8fffffff),
     .NUM_BTB_ENTRIES        (32),
     .NUM_BTB_ENTRIES_W      (5),
     .NUM_BHT_ENTRIES        (512),
     .NUM_BHT_ENTRIES_W      (9),
     .RAS_ENABLE             (1),
     .GSHARE_ENABLE          (0),
     .BHT_ENABLE             (1),
     .NUM_RAS_ENTRIES        (8),
     .NUM_RAS_ENTRIES_W      (3)
) u_riscv_top (
     .clk_i                  (clk_i),
     .rst_i                  (rst_i),
     .axi_i_awready_i        (axi_i_awready_i),
     .axi_i_wready_i         (axi_i_wready_i),
     .axi_i_bvalid_i         (axi_i_bvalid_i),
     .axi_i_bresp_i          (axi_i_bresp_i),
     .axi_i_bid_i            (axi_i_bid_i),
     .axi_i_arready_i        (axi_i_arready_i),
     .axi_i_rvalid_i         (axi_i_rvalid_i),
     .axi_i_rdata_i          (axi_i_rdata_i),
     .axi_i_rresp_i          (axi_i_rresp_i),
     .axi_i_rid_i            (axi_i_rid_i),
     .axi_i_rlast_i          (axi_i_rlast_i),
     .axi_d_awready_i        (axi_d_awready_i),
     .axi_d_wready_i         (axi_d_wready_i),
     .axi_d_bvalid_i         (axi_d_bvalid_i),
     .axi_d_bresp_i          (axi_d_bresp_i),
     .axi_d_bid_i            (axi_d_bid_i),
     .axi_d_arready_i        (axi_d_arready_i),
     .axi_d_rvalid_i         (axi_d_rvalid_i),
     .axi_d_rdata_i          (axi_d_rdata_i),
     .axi_d_rresp_i          (axi_d_rresp_i),
     .axi_d_rid_i            (axi_d_rid_i),
     .axi_d_rlast_i          (axi_d_rlast_i),
     .intr_i                 (intr_i),
     .reset_vector_i         (reset_vector_i),

     .axi_i_awvalid_o        (axi_i_awvalid_o),
     .axi_i_awaddr_o         (axi_i_awaddr_o),
     .axi_i_awid_o           (axi_i_awid_o),
     .axi_i_awlen_o          (axi_i_awlen_o),
     .axi_i_awburst_o        (axi_i_awburst_o),
     .axi_i_wvalid_o         (axi_i_wvalid_o),
     .axi_i_wdata_o          (axi_i_wdata_o),
     .axi_i_wstrb_o          (axi_i_wstrb_o),
     .axi_i_wlast_o          (axi_i_wlast_o),
     .axi_i_bready_o         (axi_i_bready_o),
     .axi_i_arvalid_o        (axi_i_arvalid_o),
     .axi_i_araddr_o         (axi_i_araddr_o),
     .axi_i_arid_o           (axi_i_arid_o),
     .axi_i_arlen_o          (axi_i_arlen_o),
     .axi_i_arburst_o        (axi_i_arburst_o),
     .axi_i_rready_o         (axi_i_rready_o),
     .axi_d_awvalid_o        (axi_d_awvalid_o),
     .axi_d_awaddr_o         (axi_d_awaddr_o),
     .axi_d_awid_o           (axi_d_awid_o),
     .axi_d_awlen_o          (axi_d_awlen_o),
     .axi_d_awburst_o        (axi_d_awburst_o),
     .axi_d_wvalid_o         (axi_d_wvalid_o),
     .axi_d_wdata_o          (axi_d_wdata_o),
     .axi_d_wstrb_o          (axi_d_wstrb_o),
     .axi_d_wlast_o          (axi_d_wlast_o),
     .axi_d_bready_o         (axi_d_bready_o),
     .axi_d_arvalid_o        (axi_d_arvalid_o),
     .axi_d_araddr_o         (axi_d_araddr_o),
     .axi_d_arid_o           (axi_d_arid_o),
     .axi_d_arlen_o          (axi_d_arlen_o),
     .axi_d_arburst_o        (axi_d_arburst_o),
     .axi_d_rready_o         (axi_d_rready_o)
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
