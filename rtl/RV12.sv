`timescale 1ns / 1ps

`ifndef SIMULATION
`include "processor_ci_defines.vh"
`endif

`define ENABLE_SECOND_MEMORY 1

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
    .wb_wstrb   (core_wstrb),
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
    .wb_wstrb   (data_mem_wstrb),
    .wb_adr     (data_mem_addr),
    .wb_dat_w   (data_mem_data_out),
    .wb_dat_r   (data_mem_data_in),
    .wb_ack     (data_mem_ack)
);

riscv_top_ahb3lite #(
  .MXLEN               (32),
  .ALEN                (32),
  .PC_INIT             (32'h000),
  .HAS_USER            (0),
  .HAS_SUPER           (0),
  .HAS_HYPER           (0),
  .HAS_BPU             (1),
  .HAS_FPU             (0),
  .HAS_MMU             (0),
  .HAS_RVM             (1),
  .HAS_RVA             (0),
  .HAS_RVC             (1),
  .IS_RV32E            (0),
  .MULT_LATENCY        (0),
  .BREAKPOINTS         (0),
  .PMA_CNT             (1),
  .PMP_CNT             (0),
  .BP_GLOBAL_BITS      (2),
  .BP_LOCAL_BITS       (10),
  .RSB_DEPTH           (4),
  .ICACHE_SIZE         (0),
  .ICACHE_BLOCK_SIZE   (32),
  .ICACHE_WAYS         (2),
  .ICACHE_REPLACE_ALG  (0),
  .DCACHE_SIZE         (0),
  .DCACHE_BLOCK_SIZE   (32),
  .DCACHE_WAYS         (2),
  .DCACHE_REPLACE_ALG  (0),
  .TECHNOLOGY          ("GENERIC"),
  .MNMIVEC_DEFAULT     (32'h1FC),
  .MTVEC_DEFAULT       (32'h1C0),
  .HTVEC_DEFAULT       (32'h180),
  .STVEC_DEFAULT       (32'h140),
  .JEDEC_BANK          (8'd10),
  .JEDEC_MANUFACTURER_ID (7'h6e),
  .HARTID              (32'd0),
  .STRICT_AHB          (1)
) riscv_top_ahb3lite_inst (
  .HRESETn             (~rst_core),
  .HCLK                (clk_core),

  .pma_cfg_i           (0),
  .pma_adr_i           (0),

  .ins_HSEL            (),
  .ins_HADDR           (imem_haddr),
  .ins_HWDATA          (imem_hwdata),
  .ins_HRDATA          (imem_hrdata),
  .ins_HWRITE          (imem_hwrite),
  .ins_HSIZE           (imem_hsize),
  .ins_HBURST          (imem_hburst),
  .ins_HPROT           (imem_hprot),
  .ins_HTRANS          (imem_htrans),
  .ins_HMASTLOCK       (imem_hmastlock),
  .ins_HREADY          (imem_hready),
  .ins_HRESP           (imem_hresp),

  .dat_HSEL            (),
  .dat_HADDR           (dmem_haddr),
  .dat_HWDATA          (dmem_hwdata),
  .dat_HRDATA          (dmem_hrdata),
  .dat_HWRITE          (dmem_hwrite),
  .dat_HSIZE           (dmem_hsize),
  .dat_HBURST          (dmem_hburst),
  .dat_HPROT           (dmem_hprot),
  .dat_HTRANS          (dmem_htrans),
  .dat_HMASTLOCK       (dmem_hmastlock),
  .dat_HREADY          (dmem_hready),
  .dat_HRESP           (dmem_hresp),

  .ext_nmi             (),
  .ext_tint            (),
  .ext_sint            (),
  .ext_int             (),

  .dbg_stall           (),
  .dbg_strb            (),
  .dbg_we              (),
  .dbg_addr            (),
  .dbg_dati            (),
  .dbg_dato            (),
  .dbg_ack             (),
  .dbg_bp              ()
);


endmodule
