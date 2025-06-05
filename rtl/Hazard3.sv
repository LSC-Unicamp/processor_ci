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

// AHB - Instruction bus
logic [31:0] haddr;
logic        hwrite;
logic [2:0]  hsize;
logic [2:0]  hburst;
logic        hmastlock;
logic [3:0]  hprot;
logic [1:0]  htrans;
logic [31:0] hwdata;
logic [31:0] hrdata;
logic        hready;
logic        hresp;

ahb_to_wishbone #( // bus adapter
    .ADDR_WIDTH(32),
    .DATA_WIDTH(32)
) ahb2wb_inst (
    // Clock & Reset
    .HCLK       (clk_core),
    .HRESETn    (~rst_core),

    // AHB interface
    .HADDR      (haddr),
    .HTRANS     (htrans),
    .HWRITE     (hwrite),
    .HSIZE      (hsize),
    .HBURST     (hburst),
    .HPROT      (hprot),
    .HLOCK      (hmastlock),
    .HWDATA     (hwdata),
    .HREADY     (hready),
    .HRDATA     (hrdata),
    .HREADYOUT  (hready), // normalmente igual a HREADY em designs simples
    .HRESP      (hresp),

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

hazard3_cpu_1port #(
	// These must have the values given here for you to end up with a useful SoC:
	.RESET_VECTOR        (32'h0000_0000),
	.MTVEC_INIT          (32'h0000_0000),
	.CSR_M_MANDATORY     (1),
	.CSR_M_TRAP          (1),
	.DEBUG_SUPPORT       (1),
	.NUM_IRQS            (1),
	.RESET_REGFILE       (0),
	// Can be overridden from the defaults in hazard3_config.vh during
	// instantiation of example_soc():
	.EXTENSION_A         (1),
	.EXTENSION_C         (1),
	.EXTENSION_M         (1),
	.EXTENSION_ZBA       (1),
	.EXTENSION_ZBB       (1),
	.EXTENSION_ZBC       (1),
	.EXTENSION_ZBS       (1),
	.EXTENSION_ZBKB      (1),
	.EXTENSION_ZIFENCEI  (0),
	.EXTENSION_XH3BEXTM  (0),
	.EXTENSION_XH3IRQ    (0),
	.EXTENSION_XH3PMPM   (0),
	.EXTENSION_XH3POWER  (0),
	.CSR_COUNTER         (0),
	.U_MODE              (0),
	.PMP_REGIONS         (0),
	.PMP_GRAIN           (0),
	.PMP_HARDWIRED       (0),
	.PMP_HARDWIRED_ADDR  (0),
	.PMP_HARDWIRED_CFG   (0),
	.MVENDORID_VAL       (0),
	.BREAKPOINT_TRIGGERS (0),
	.IRQ_PRIORITY_BITS   (0),
	.MIMPID_VAL          (0),
	.MHARTID_VAL         (0),
	.REDUCED_BYPASS      (0),
	.MULDIV_UNROLL       (1),
	.MUL_FAST            (0),
	.MUL_FASTER          (1),
	.MULH_FAST           (1),
	.FAST_BRANCHCMP      (1),
	.BRANCH_PREDICTOR    (1)
) cpu (
	.clk                        (clk_core),
	.clk_always_on              (clk_core),
	.rst_n                      (~rst_core),

	.pwrup_req                  (),
	.pwrup_ack                  (1),   // Tied back
	.clk_en                     (),
	.unblock_out                (),
	.unblock_in                 (1), // Tied back

	.haddr                      (haddr),
	.hwrite                     (hwrite),
	.htrans                     (htrans),
	.hsize                      (hsize),
	.hburst                     (hburst),
	.hprot                      (hprot),
	.hmastlock                  (hmastlock),
	.hexcl                      (),
	.hready                     (hready),
	.hresp                      (hresp),
	.hexokay                    (),
	.hwdata                     (hwdata),
	.hrdata                     (hrdata),

	.dbg_req_halt               (0),
	.dbg_req_halt_on_reset      (0),
	.dbg_req_resume             (0),
	.dbg_halted                 (),
	.dbg_running                (),

	.dbg_data0_rdata            (0),
	.dbg_data0_wdata            (),
	.dbg_data0_wen              (),

	.dbg_instr_data             (0),
	.dbg_instr_data_vld         (0),
	.dbg_instr_data_rdy         (),
	.dbg_instr_caught_exception (),
	.dbg_instr_caught_ebreak    (),

	.dbg_sbus_addr              (0),
	.dbg_sbus_write             (0),
	.dbg_sbus_size              (0),
	.dbg_sbus_vld               (0),
	.dbg_sbus_rdy               (),
	.dbg_sbus_err               (),
	.dbg_sbus_wdata             (0),
	.dbg_sbus_rdata             (),

	.irq                        (0),

	.soft_irq                   (1'b0),
	.timer_irq                  (0)
);

endmodule
