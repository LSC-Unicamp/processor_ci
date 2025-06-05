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

logic [2:0] iwb_cti, dwb_cti;
logic sync_ack, sync_data_ack;
logic [31:0] sync_data, sync_data_mem;

always_ff @( posedge clk_core ) begin
    sync_ack <= core_ack;
    sync_data_ack <= data_mem_ack;
    sync_data <= data_mem_ack;
    sync_data_mem <= data_mem_data_in;
end


mor1kx #(
    .OPTION_OPERAND_WIDTH         (32),
    .OPTION_CPU0                  ("CAPPUCCINO"),
    .FEATURE_DATACACHE            ("ENABLED"), // NONE
    .OPTION_DCACHE_BLOCK_WIDTH    (5),
    .OPTION_DCACHE_SET_WIDTH      (9),
    .OPTION_DCACHE_WAYS           (2),
    .OPTION_DCACHE_LIMIT_WIDTH    (32),
    .OPTION_DCACHE_SNOOP          ("NONE"),
    .FEATURE_DMMU                 ("NONE"),
    .FEATURE_DMMU_HW_TLB_RELOAD   ("NONE"),
    .OPTION_DMMU_SET_WIDTH        (6),
    .OPTION_DMMU_WAYS             (1),
    .FEATURE_INSTRUCTIONCACHE     ("ENABLED"), // NONE
    .OPTION_ICACHE_BLOCK_WIDTH    (5),
    .OPTION_ICACHE_SET_WIDTH      (9),
    .OPTION_ICACHE_WAYS           (2),
    .OPTION_ICACHE_LIMIT_WIDTH    (32),
    .FEATURE_IMMU                 ("NONE"),
    .FEATURE_IMMU_HW_TLB_RELOAD   ("NONE"),
    .OPTION_IMMU_SET_WIDTH        (6),
    .OPTION_IMMU_WAYS             (1),
    .FEATURE_TIMER                ("ENABLED"),
    .FEATURE_DEBUGUNIT            ("NONE"),
    .FEATURE_PERFCOUNTERS         ("NONE"),
    .OPTION_PERFCOUNTERS_NUM      (0),
    .FEATURE_MAC                  ("NONE"),
    .FEATURE_SYSCALL              ("ENABLED"),
    .FEATURE_TRAP                 ("ENABLED"),
    .FEATURE_RANGE                ("ENABLED"),
    .FEATURE_PIC                  ("NONE"), //ENABLED
    .OPTION_PIC_TRIGGER           ("LEVEL"),
    .OPTION_PIC_NMI_WIDTH         (0),
    .FEATURE_DSX                  ("ENABLED"),
    .FEATURE_OVERFLOW             ("ENABLED"),
    .FEATURE_CARRY_FLAG           ("ENABLED"),
    .FEATURE_FASTCONTEXTS         ("NONE"),
    .OPTION_RF_CLEAR_ON_INIT      (0),
    .OPTION_RF_NUM_SHADOW_GPR     (0),
    .OPTION_RF_ADDR_WIDTH         (5),
    .OPTION_RF_WORDS              (32),
    .OPTION_RESET_PC              (0),
    .FEATURE_MULTIPLIER           ("THREESTAGE"),
    .FEATURE_DIVIDER              ("SERIAL"),
    .FEATURE_ADDC                 ("ENABLED"),
    .FEATURE_SRA                  ("ENABLED"),
    .FEATURE_ROR                  ("NONE"),
    .FEATURE_EXT                  ("NONE"),
    .FEATURE_CMOV                 ("ENABLED"),
    .FEATURE_FFL1                 ("ENABLED"),
    .FEATURE_ATOMIC               ("ENABLED"),
    .FEATURE_CUST1                ("NONE"),
    .FEATURE_CUST2                ("NONE"),
    .FEATURE_CUST3                ("NONE"),
    .FEATURE_CUST4                ("NONE"),
    .FEATURE_CUST5                ("NONE"),
    .FEATURE_CUST6                ("NONE"),
    .FEATURE_CUST7                ("NONE"),
    .FEATURE_CUST8                ("NONE"),
    .FEATURE_FPU                  ("ENABLED"), // NONE
    .OPTION_SHIFTER               ("BARREL"),
    .FEATURE_STORE_BUFFER         ("ENABLED"),
    .OPTION_STORE_BUFFER_DEPTH_WIDTH (8),
    .FEATURE_MULTICORE            ("NONE"),
    .FEATURE_TRACEPORT_EXEC       ("NONE"),
    .FEATURE_BRANCH_PREDICTOR     ("SIMPLE"),
    .BUS_IF_TYPE                  ("WISHBONE32"),
    .IBUS_WB_TYPE                 ("B3_READ_BURSTING"), //("B3_READ_BURSTING"),
    .DBUS_WB_TYPE                 ("CLASSIC")
) u_mor1kx (
    .clk                           (clk_core),                  // 1 bit
    .rst                           (rst_core),                  // 1 bit

    // Instruction Wishbone interface
    .iwbm_adr_o                    (core_addr),           // 32 bits
    .iwbm_stb_o                    (core_stb),           // 1 bit
    .iwbm_cyc_o                    (core_cyc),           // 1 bit
    .iwbm_sel_o                    (core_wstrb),           // 4 bits
    .iwbm_we_o                     (core_we),            // 1 bit
    .iwbm_cti_o                    (iwb_cti),           // 3 bits
    .iwbm_bte_o                    (),           // 2 bits
    .iwbm_dat_o                    (core_data_out),           // 32 bits
    .iwbm_err_i                    (0),           // 1 bit
    .iwbm_ack_i                    (core_ack),           // 1 bit
    .iwbm_dat_i                    (core_data_in),           // 32 bits
    .iwbm_rty_i                    (0),           // 1 bit

    // Data Wishbone interface
    .dwbm_adr_o                    (data_mem_addr),           // 32 bits
    .dwbm_stb_o                    (data_mem_stb),           // 1 bit
    .dwbm_cyc_o                    (data_mem_cyc),           // 1 bit
    .dwbm_sel_o                    (data_mem_wstrb),           // 4 bits
    .dwbm_we_o                     (data_mem_we),            // 1 bit
    .dwbm_cti_o                    (dwb_cti),           // 3 bits
    .dwbm_bte_o                    (),           // 2 bits
    .dwbm_dat_o                    (data_mem_data_out),           // 32 bits
    .dwbm_err_i                    (0),           // 1 bit
    .dwbm_ack_i                    (data_mem_ack),           // 1 bit
    .dwbm_dat_i                    (data_mem_data_in),           // 32 bits
    .dwbm_rty_i                    (0),           // 1 bit

    .irq_i                         (0),                // 32 bits

    // Debug interface
    .du_addr_i                     (0),            // 16 bits
    .du_stb_i                      (0),             // 1 bit
    .du_dat_i                      (0),             // 32 bits
    .du_we_i                       (0),              // 1 bit
    .du_dat_o                      (),             // 32 bits
    .du_ack_o                      (),             // 1 bit
    .du_stall_i                    (0),           // 1 bit
    .du_stall_o                    (),           // 1 bit

    // Traceport execution output
    .traceport_exec_valid_o        (),    // 1 bit
    .traceport_exec_pc_o           (),       // 32 bits
    .traceport_exec_jb_o           (),       // 1 bit
    .traceport_exec_jal_o          (),      // 1 bit
    .traceport_exec_jr_o           (),       // 1 bit
    .traceport_exec_jbtarget_o     (), // 32 bits
    .traceport_exec_insn_o         (),     // `OR1K_INSN_WIDTH bits
    .traceport_exec_wbdata_o       (),   // 32 bits
    .traceport_exec_wbreg_o        (),    // 5 bits
    .traceport_exec_wben_o         (),     // 1 bit

    // Multicore identifiers
    .multicore_coreid_i            (0),   // 32 bits
    .multicore_numcores_i          (1), // 32 bits

    .snoop_adr_i                   (0),          // 32 bits
    .snoop_en_i                    (0)            // 1 bit
);


endmodule
