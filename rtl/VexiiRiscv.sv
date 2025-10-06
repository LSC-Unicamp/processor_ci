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

logic vexii_i_cyc, vexii_i_stb, vexii_i_ack, vexii_i_we;
logic vexii_d_cyc, vexii_d_stb, vexii_d_ack, vexii_d_we;

logic [7:0] vexii_i_sel, vexii_d_sel;
logic [63:0] vexii_i_mosi, vexii_d_mosi, vexii_i_miso, vexii_d_miso;
logic [28:0] vexii_i_addr, vexii_d_addr;
logic [2:0] vexii_i_cti, vexii_d_cti;
logic [1:0] vexii_i_bte, vexii_d_bte;

VexiiRiscv u_VexiiRiscv (
    .PrivilegedPlugin_logic_rdtime                         (0), // 64 bits
    .PrivilegedPlugin_logic_harts_0_int_m_timer            (0), // 1 bit
    .PrivilegedPlugin_logic_harts_0_int_m_software         (0), // 1 bit
    .PrivilegedPlugin_logic_harts_0_int_m_external         (0), // 1 bit
    .LsuL1WishbonePlugin_logic_bus_CYC                     (vexii_d_cyc), // 1 bit
    .LsuL1WishbonePlugin_logic_bus_STB                     (vexii_d_stb), // 1 bit
    .LsuL1WishbonePlugin_logic_bus_ACK                     (vexii_d_ack), // 1 bit
    .LsuL1WishbonePlugin_logic_bus_WE                      (vexii_d_we), // 1 bit
    .LsuL1WishbonePlugin_logic_bus_ADR                     (vexii_d_addr), // 29 bits
    .LsuL1WishbonePlugin_logic_bus_DAT_MISO                (vexii_d_miso), // 64 bits
    .LsuL1WishbonePlugin_logic_bus_DAT_MOSI                (vexii_d_mosi), // 64 bits
    .LsuL1WishbonePlugin_logic_bus_SEL                     (vexii_d_sel), // 8 bits
    .LsuL1WishbonePlugin_logic_bus_ERR                     (0), // 1 bit
    .LsuL1WishbonePlugin_logic_bus_CTI                     (vexii_d_cti), // 3 bits
    .LsuL1WishbonePlugin_logic_bus_BTE                     (vexii_d_bte), // 2 bits
    .FetchL1WishbonePlugin_logic_bus_CYC                   (vexii_i_cyc), // 1 bit
    .FetchL1WishbonePlugin_logic_bus_STB                   (vexii_i_stb), // 1 bit
    .FetchL1WishbonePlugin_logic_bus_ACK                   (vexii_i_ack), // 1 bit
    .FetchL1WishbonePlugin_logic_bus_WE                    (vexii_i_we), // 1 bit
    .FetchL1WishbonePlugin_logic_bus_ADR                   (vexii_i_addr), // 29 bits
    .FetchL1WishbonePlugin_logic_bus_DAT_MISO              (vexii_i_miso), // 64 bits
    .FetchL1WishbonePlugin_logic_bus_DAT_MOSI              (vexii_i_mosi), // 64 bits
    .FetchL1WishbonePlugin_logic_bus_SEL                   (vexii_i_sel), // 8 bits
    .FetchL1WishbonePlugin_logic_bus_ERR                   (0), // 1 bit
    .FetchL1WishbonePlugin_logic_bus_CTI                   (vexii_i_cti), // 3 bits
    .FetchL1WishbonePlugin_logic_bus_BTE                   (vexii_i_bte), // 2 bits
    .LsuCachelessWishbonePlugin_logic_bridge_down_CYC      (), // 1 bit
    .LsuCachelessWishbonePlugin_logic_bridge_down_STB      (), // 1 bit
    .LsuCachelessWishbonePlugin_logic_bridge_down_ACK      (0), // 1 bit
    .LsuCachelessWishbonePlugin_logic_bridge_down_WE       (), // 1 bit
    .LsuCachelessWishbonePlugin_logic_bridge_down_ADR      (), // 29 bits
    .LsuCachelessWishbonePlugin_logic_bridge_down_DAT_MISO (0), // 64 bits
    .LsuCachelessWishbonePlugin_logic_bridge_down_DAT_MOSI (), // 64 bits
    .LsuCachelessWishbonePlugin_logic_bridge_down_SEL      (), // 8 bits
    .LsuCachelessWishbonePlugin_logic_bridge_down_ERR      (0), // 1 bit
    .LsuCachelessWishbonePlugin_logic_bridge_down_CTI      (), // 3 bits
    .LsuCachelessWishbonePlugin_logic_bridge_down_BTE      (), // 2 bits
    .clk                                                   (clk_core),  // 1 bit
    .reset                                                 (rst_core)  // 1 bit
);


// Ponte 64 -> 32 bits para conectar CPU ao core
wb64_to_wb32_bridge u_wb64_to_wb32_i (
    .clk        (clk_core),
    .rst        (rst_core),

    // Lado CPU 64 bits (VexiiRiscv)
    .cyc_i      (vexii_i_cyc),
    .stb_i      (vexii_i_stb),
    .we_i       (vexii_i_we),
    .adr_i      (vexii_i_addr),      // 29 bits
    .dat_i      (vexii_i_mosi), // 64 bits
    .dat_o      (vexii_i_miso), // 64 bits
    .sel_i      (vexii_i_sel),      // 8 bits
    .ack_o      (vexii_i_ack),
    .cti_i      (vexii_i_cti),
    .bte_i      (vexii_i_bte),

    // Lado Core 32 bits
    .core_cyc_o     (core_cyc),
    .core_stb_o     (core_stb),
    .core_we_o      (core_we),
    .core_addr_o    (core_addr),
    .core_dat_o     (core_data_out),
    .core_dat_i     (core_data_in),
    .core_sel_o     (core_wstrb),
    .core_ack_i     (core_ack)
);

// Ponte 64 -> 32 bits para conectar CPU ao core
wb64_to_wb32_bridge u_wb64_to_wb32_d (
    .clk        (clk_core),
    .rst        (rst_core),

    // Lado CPU 64 bits (VexiiRiscv)
    .cyc_i      (vexii_d_cyc),
    .stb_i      (vexii_d_stb),
    .we_i       (vexii_d_we),
    .adr_i      (vexii_d_addr),      // 29 bits
    .dat_i      (vexii_d_mosi), // 64 bits
    .dat_o      (vexii_d_miso), // 64 bits
    .sel_i      (vexii_d_sel),      // 8 bits
    .ack_o      (vexii_d_ack),
    .cti_i      (vexii_d_cti),
    .bte_i      (vexii_d_bte),

    // Lado Core 32 bits
    .core_cyc_o     (data_mem_cyc),
    .core_stb_o     (data_mem_stb),
    .core_we_o      (data_mem_we),
    .core_addr_o    (data_mem_addr),
    .core_dat_o     (data_mem_data_out),
    .core_dat_i     (data_mem_data_in),
    .core_sel_o     (data_mem_wstrb),
    .core_ack_i     (data_mem_ack)
);


endmodule

module wb64_to_wb32_bridge (
    input  logic        clk,
    input  logic        rst,

    // Wishbone 64-bit lado CPU (master)
    input  logic        cyc_i,
    input  logic        stb_i,
    input  logic        we_i,
    input  logic [28:0] adr_i,      // endereço word-alinhado 64b
    input  logic [63:0] dat_i,
    output logic [63:0] dat_o,
    input  logic [7:0]  sel_i,
    output logic        ack_o,
    input  logic [2:0]  cti_i,
    input  logic [1:0]  bte_i,

    // Wishbone 32-bit lado Core (slave)
    output logic        core_cyc_o,
    output logic        core_stb_o,
    output logic        core_we_o,
    output logic [31:0] core_addr_o,
    output logic [31:0] core_dat_o,
    input  logic [31:0] core_dat_i,
    output logic [3:0]  core_sel_o,
    input  logic        core_ack_i
);

    typedef enum logic [1:0] {
        IDLE,
        ACCESS_LOW,
        ACCESS_HIGH
    } state_t;

    state_t state, next_state;

    // registradores
    logic [63:0] data_buffer_reg, data_buffer_next;
    logic [28:0] addr_reg, addr_next;
    logic        we_reg,   we_next;
    logic [7:0]  sel_reg,  sel_next;
    logic [63:0] dat_i_reg, dat_i_next;
    logic [2:0]  cti_reg,  cti_next;
    logic [1:0]  bte_reg,  bte_next;

    // função: calcula próximo endereço conforme BTE (em unidades de 64-bit word)
    function automatic [28:0] next_addr(input [28:0] a, input [1:0] bte);
        case (bte)
            2'b00: next_addr = a + 1; // linear
            2'b01: next_addr = {a[28:2], (a[1:0]+1) & 2'b11};   // wrap-4
            2'b10: next_addr = {a[28:3], (a[2:0]+1) & 3'b111};  // wrap-8
            2'b11: next_addr = {a[28:4], (a[3:0]+1) & 4'b1111}; // wrap-16
        endcase
    endfunction

    // estado + registradores
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            state           <= IDLE;
            addr_reg        <= '0;
            we_reg          <= '0;
            sel_reg         <= '0;
            dat_i_reg       <= '0;
            cti_reg         <= '0;
            bte_reg         <= '0;
            data_buffer_reg <= '0;
        end else begin
            state           <= next_state;
            addr_reg        <= addr_next;
            we_reg          <= we_next;
            sel_reg         <= sel_next;
            dat_i_reg       <= dat_i_next;
            cti_reg         <= cti_next;
            bte_reg         <= bte_next;
            data_buffer_reg <= data_buffer_next;
        end
    end

    // FSM combinacional
    always_comb begin
        // defaults
        next_state        = state;
        addr_next         = addr_reg;
        we_next           = we_reg;
        sel_next          = sel_reg;
        dat_i_next        = dat_i_reg;
        cti_next          = cti_reg;
        bte_next          = bte_reg;
        data_buffer_next  = data_buffer_reg;

        core_cyc_o   = (state != IDLE);
        core_stb_o   = 1'b0;
        core_we_o    = we_reg;
        core_addr_o  = 32'h0;
        core_dat_o   = 32'h0;
        core_sel_o   = 4'h0;
        ack_o        = 1'b0;
        dat_o        = data_buffer_reg;

        case (state)
            IDLE: begin
                if (cyc_i && stb_i) begin
                    next_state = ACCESS_LOW;
                    addr_next  = adr_i;
                    we_next    = we_i;
                    sel_next   = sel_i;
                    dat_i_next = dat_i;
                    cti_next   = cti_i;
                    bte_next   = bte_i;
                end
            end

            ACCESS_LOW: begin
                core_stb_o  = 1'b1;
                core_addr_o = {addr_reg, 3'b000};
                core_sel_o  = sel_reg[3:0];
                core_dat_o  = dat_i_reg[31:0];
                if (core_ack_i) begin
                    if (!we_reg)
                        data_buffer_next[31:0] = core_dat_i;
                    next_state = ACCESS_HIGH;
                end
            end

            ACCESS_HIGH: begin
                core_stb_o  = 1'b1;
                core_addr_o = {addr_reg, 3'b100};
                core_sel_o  = sel_reg[7:4];
                core_dat_o  = dat_i_reg[63:32];
                if (core_ack_i) begin
                    if (!we_reg)
                        data_buffer_next[63:32] = core_dat_i;

                    // gera ack para o master 64b
                    ack_o  = 1'b1;

                    if (cti_reg == 3'b111) begin
                        // fim do burst
                        next_state = IDLE;
                    end else begin
                        // continua burst
                        addr_next  = next_addr(addr_reg, bte_reg);
                        next_state = ACCESS_LOW;

                        // capturar próximo beat (se master já forneceu)
                        if (cyc_i && stb_i) begin
                            dat_i_next = dat_i;
                            sel_next   = sel_i;
                            cti_next   = cti_i;
                            bte_next   = bte_i;
                        end
                    end
                end
            end
        endcase
    end

endmodule
