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

neorv32_cpu #(
  // General
  .HART_ID              (0),
  .BOOT_ADDR            (32'h00000000),
  .DEBUG_PARK_ADDR      (32'h00000000),
  .DEBUG_EXC_ADDR       (32'h00000000),
  .ICC_EN               (1'b1),

  // RISC-V ISA Extensions
  .RISCV_ISA_C          (1'b1),
  .RISCV_ISA_E          (1'b1),
  .RISCV_ISA_M          (1'b1),
  .RISCV_ISA_U          (1'b1),
  .RISCV_ISA_Zaamo      (1'b1),
  .RISCV_ISA_Zalrsc     (1'b1),
  .RISCV_ISA_Zba        (1'b1),
  .RISCV_ISA_Zbb        (1'b1),
  .RISCV_ISA_Zbkb       (1'b1),
  .RISCV_ISA_Zbkc       (1'b1),
  .RISCV_ISA_Zbkx       (1'b1),
  .RISCV_ISA_Zbs        (1'b1),
  .RISCV_ISA_Zfinx      (1'b1),
  .RISCV_ISA_Zicntr     (1'b1),
  .RISCV_ISA_Zicond     (1'b1),
  .RISCV_ISA_Zihpm      (1'b1),
  .RISCV_ISA_Zknd       (1'b1),
  .RISCV_ISA_Zkne       (1'b1),
  .RISCV_ISA_Zknh       (1'b1),
  .RISCV_ISA_Zksed      (1'b1),
  .RISCV_ISA_Zksh       (1'b1),
  .RISCV_ISA_Zmmul      (1'b1),
  .RISCV_ISA_Zxcfu      (1'b1),
  .RISCV_ISA_Sdext      (1'b1),
  .RISCV_ISA_Sdtrig     (1'b1),
  .RISCV_ISA_Smpmp      (1'b1),

  // Tuning Options
  .CPU_FAST_MUL_EN      (1'b1),
  .CPU_FAST_SHIFT_EN    (1'b1),
  .CPU_RF_HW_RST_EN     (1'b1),

  // Physical Memory Protection (PMP)
  .PMP_NUM_REGIONS      (16),
  .PMP_MIN_GRANULARITY  (64),
  .PMP_TOR_MODE_EN      (1'b1),
  .PMP_NAP_MODE_EN      (1'b1),

  // Hardware Performance Monitors (HPM)
  .HPM_NUM_CNTS         (13),
  .HPM_CNT_WIDTH        (64)
) u_neorv32_cpu (
  // Global control
  .clk_i                (clk_core),
  .rstn_i               (rst_core),

  // Interrupts
  .msi_i                (0),
  .mei_i                (0),
  .mti_i                (0),
  .firq_i               (0),
  .dbi_i                (0),

  // Inter-core communication links
  .icc_tx_o             (),
  .icc_rx_i             (),

  // Instruction bus interface
  .ibus_req_o           (),
  .ibus_rsp_i           (),

  // Data bus interface
  .dbus_req_o           (),
  .dbus_rsp_i           (),

  // Memory synchronization
  .mem_sync_i           ()
);

endmodule
