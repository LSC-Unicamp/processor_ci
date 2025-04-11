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

// AHB - Instruction bus
logic [31:0] imem_haddr;
logic        imem_hwrite;
logic [2:0]  imem_hsize;
logic [2:0]  imem_hburst;
logic        imem_hmastlock;
logic [3:0]  imem_hprot;
logic [1:0]  imem_htrans;
logic [31:0] imem_hwdata;
logic [31:0] imem_hrdata;
logic        imem_hready;
logic        imem_hresp;

// AHB - Data bus
logic [31:0] dmem_haddr;
logic        dmem_hwrite;
logic [2:0]  dmem_hsize;
logic [2:0]  dmem_hburst;
logic        dmem_hmastlock;
logic [3:0]  dmem_hprot;
logic [1:0]  dmem_htrans;
logic [31:0] dmem_hwdata;
logic [31:0] dmem_hrdata;
logic        dmem_hready;
logic        dmem_hresp;

ahb_to_wishbone #( // Instruction bus adapter
    .ADDR_WIDTH(32),
    .DATA_WIDTH(32)
) ahb2wb_inst (
    // Clock & Reset
    .HCLK       (clk_core),
    .HRESETn    (~rst_core),

    // AHB interface
    .HADDR      (imem_haddr),
    .HTRANS     (imem_htrans),
    .HWRITE     (imem_hwrite),
    .HSIZE      (imem_hsize),
    .HBURST     (imem_hburst),
    .HPROT      (imem_hprot),
    .HLOCK      (imem_hmastlock),
    .HWDATA     (imem_hwdata),
    .HREADY     (imem_hready),
    .HRDATA     (imem_hrdata),
    .HREADYOUT  (imem_hready), // normalmente igual a HREADY em designs simples
    .HRESP      (imem_hresp),

    // Wishbone interface
    .wb_cyc     (core_cyc),
    .wb_stb     (core_stb),
    .wb_we      (core_we),
    .wb_adr     (core_addr),
    .wb_dat_w   (core_data_out),
    .wb_dat_r   (core_data_in),
    .wb_ack     (core_ack)
);


ahb_to_wishbone #( // Data bus adapter
    .ADDR_WIDTH(32),
    .DATA_WIDTH(32)
) ahb2wb_data (
    // Clock & Reset
    .HCLK       (clk_core),
    .HRESETn    (~rst_core),

    // AHB interface
    .HADDR      (dmem_haddr),
    .HTRANS     (dmem_htrans),
    .HWRITE     (dmem_hwrite),
    .HSIZE      (dmem_hsize),
    .HBURST     (dmem_hburst),
    .HPROT      (dmem_hprot),
    .HLOCK      (dmem_hmastlock),
    .HWDATA     (dmem_hwdata),
    .HREADY     (dmem_hready),
    .HRDATA     (dmem_hrdata),
    .HREADYOUT  (dmem_hready),
    .HRESP      (dmem_hresp),

    // Wishbone interface
    .wb_cyc     (data_mem_cyc),
    .wb_stb     (data_mem_stb),
    .wb_we      (data_mem_we),
    .wb_adr     (data_mem_addr),
    .wb_dat_w   (data_mem_data_out),
    .wb_dat_r   (data_mem_data_in),
    .wb_ack     (data_mem_ack)
);


airi5c_core airi5c(
    .rst_ni              (~rst_core),
    .clk_i               (clk_core),
    .testmode_i          (0),

    .ndmreset_o          (),
    .ext_interrupts_i    (0),
    .system_timer_tick_i (0),

    // Instruction memory (AHB)
    .imem_haddr_o        (imem_haddr),
    .imem_hwrite_o       (imem_hwrite),
    .imem_hsize_o        (imem_hsize),
    .imem_hburst_o       (imem_hburst),
    .imem_hmastlock_o    (imem_hmastlock),
    .imem_hprot_o        (imem_hprot),
    .imem_htrans_o       (imem_htrans),
    .imem_hwdata_o       (imem_hwdata),
    .imem_hrdata_i       (imem_hrdata),
    .imem_hready_i       (imem_hready),
    .imem_hresp_i        (imem_hresp),

    // Data memory (AHB)
    .dmem_haddr_o        (dmem_haddr),
    .dmem_hwrite_o       (dmem_hwrite),
    .dmem_hsize_o        (dmem_hsize),
    .dmem_hburst_o       (dmem_hburst),
    .dmem_hmastlock_o    (dmem_hmastlock),
    .dmem_hprot_o        (dmem_hprot),
    .dmem_htrans_o       (dmem_htrans),
    .dmem_hwdata_o       (dmem_hwdata),
    .dmem_hrdata_i       (dmem_hrdata),
    .dmem_hready_i       (dmem_hready),
    .dmem_hresp_i        (dmem_hresp),

    .lock_custom_i       (0),

    .dmi_addr_i          (0),
    .dmi_en_i            (0),
    .dmi_error_o         (),
    .dmi_wen_i           (0),
    .dmi_wdata_i         (0),
    .dmi_rdata_o         (),
    .dmi_dm_busy_o       ()
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
