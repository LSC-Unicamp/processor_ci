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

logic [31:0] awaddr;
logic [2:0]  awprot;
logic        awvalid;
logic        awready;

logic [31:0] wdata;
logic [3:0]  wstrb;
logic        wvalid;
logic        wready;

logic [1:0]  bresp;
logic        bvalid;
logic        bready;

logic [31:0] araddr;
logic [2:0]  arprot;
logic        arvalid;
logic        arready;

logic [31:0] rdata;
logic [1:0]  rresp;
logic        rvalid;
logic        rready;

AXI4Lite_to_Wishbone #(
    .ADDR_WIDTH(32),
    .DATA_WIDTH(32)
) bridge_inst (
    .ACLK      (clk_core),
    .ARESETN   (~rst_core),

    .AWADDR    (awaddr),
    .AWPROT    (awprot),
    .AWVALID   (awvalid),
    .AWREADY   (awready),
    .WDATA     (wdata),
    .WSTRB     (wstrb),
    .WVALID    (wvalid),
    .WREADY    (wready),
    .BRESP     (bresp),
    .BVALID    (bvalid),
    .BREADY    (bready),
    .ARADDR    (araddr),
    .ARPROT    (arprot),
    .ARVALID   (arvalid),
    .ARREADY   (arready),
    .RDATA     (rdata),
    .RRESP     (rresp),
    .RVALID    (rvalid),
    .RREADY    (rready),

    .wb_adr_o  (core_addr),
    .wb_dat_o  (core_data_out),
    .wb_we_o   (core_we),
    .wb_stb_o  (core_stb),
    .wb_cyc_o  (core_cyc),
    .wb_sel_o  (core_wstrb),
    .wb_dat_i  (core_data_in),
    .wb_ack_i  (core_ack),
    .wb_err_i  (1'b0)
);

mriscvcore mriscvcore_inst (
    .clk     (clk_core),
    .rstn    (~rst_core),
    .trap    (),

    .AWvalid (awvalid),
    .AWready (awready),
    .AWdata  (awaddr),
    .AWprot  (awprot),

    .Wvalid  (wvalid),
    .Wready  (wready),
    .Wdata   (wdata),
    .Wstrb   (wstrb),

    .Bvalid  (bvalid),
    .Bready  (bready),

    .ARvalid (arvalid),
    .ARready (arready),
    .ARdata  (araddr),
    .ARprot  (arprot),

    .Rvalid  (rvalid),
    .RReady  (rready),
    .Rdata   (rdata),

    .inirr   (0)
);

endmodule
