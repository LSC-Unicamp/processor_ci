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

    output logic [31:0] core_addr,     // Endereço
    output logic [31:0] core_data_out, // Dados de entrada (para escrita)
    input  logic [31:0] core_data_in,  // Dados de saída (para leitura)

    input  logic        core_ack       // Confirmação da transação

    `ifdef ENABLE_SECOND_MEMORY
    output logic        data_mem_cyc;
    output logic        data_mem_stb;
    output logic        data_mem_we;
    output logic [31:0] data_mem_addr;
    output logic [31:0] data_mem_data_out;
    input  logic [31:0] data_mem_data_in;
    input  logic        data_mem_ack;
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

    cv32e40x_core #(
                 .NUM_MHPMCOUNTERS (NUM_MHPMCOUNTERS)
                )
    cv32e40x_core_i
        (
         // Clock and Reset
         .clk_i                  ( clk_core                 ),
         .rst_ni                 ( ~rst_core                ),

         .scan_cg_en_i           ( '0                    ),

         // Control interface: more or less static
         .boot_addr_i            ( 0             ),
         .mtvec_addr_i           ( '0                    ), // TODO
         .dm_halt_addr_i         ( 32'h1A11_0800        ),
         .mhartid_i              ( 0               ),
         .mimpid_i               ( 0                ),
         .dm_exception_addr_i    ( '0                    ), // TODO
         .nmi_addr_i             ( '0                    ), // TODO

         // Instruction memory interface
         .instr_req_o            ( instr_req             ),
         .instr_gnt_i            ( instr_gnt             ),
         .instr_rvalid_i         ( instr_rvalid          ),
         .instr_addr_o           ( instr_addr            ),
         .instr_memtype_o        (                       ), // TODO: should the core tb check this?
         .instr_prot_o           (                       ), // TODO: should the core tb check this?
         .instr_dbg_o            (                       ), // TODO: should the core tb check this?
         .instr_rdata_i          ( instr_rdata           ),
         .instr_err_i            ( 1'b0                  ),

         // Data memory interface
         .data_req_o             ( data_req              ),
         .data_gnt_i             ( data_gnt              ),
         .data_rvalid_i          ( data_rvalid           ),
         .data_we_o              ( data_we               ),
         .data_be_o              ( data_be               ),
         .data_addr_o            ( data_addr             ),
         .data_memtype_o         (                       ), // TODO: should the core tb check this?
         .data_prot_o            (                       ), // TODO: should the core tb check this?
         .data_dbg_o             (                       ), // TODO
         .data_err_i             ( 1'b0                  ),
         .data_atop_o            (                       ),
         .data_exokay_i          ( 1'b1                  ),

         // Cycle Count
         .mcycle_o               (                       ), // TODO

         // eXtension interface
         .xif_compressed_if      ( ext_if                ),
         .xif_issue_if           ( ext_if                ),
         .xif_commit_if          ( ext_if                ),
         .xif_mem_if             ( ext_if                ),
         .xif_mem_result_if      ( ext_if                ),
         .xif_result_if          ( ext_if                ),

         // Interrupts
         .irq_i                  ( {32{1'b0}}            ),

         .clic_irq_i             (  1'b0                 ), // TODO
         .clic_irq_id_i          ( 12'h0                 ), // TODO
         .clic_irq_il_i          (  8'h0                 ), // TODO
         .clic_irq_priv_i        (  2'h0                 ), // TODO
         .clic_irq_hv_i          (  1'b0                 ), // TODO
         .clic_irq_id_o          (                       ), // TODO
         .clic_irq_mode_o        (                       ),
         .clic_irq_exit_o        (                       ),


         
         // Fencei flush handshake
         .fencei_flush_req_o     (                       ),
         .fencei_flush_ack_i     ( 1'b0                  ),

         .debug_req_i            ( debug_req             ),
         .debug_havereset_o      (                       ),
         .debug_running_o        (                       ),
         .debug_halted_o         (                       ),

         // CPU Control Signals
         .fetch_enable_i         ( fetch_enable_i        ),
         .core_sleep_o           ( core_sleep_o          )
       );


endmodule
