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
assign core_stb = core_cyc;
assign core_we  = 1'b0; // Read only
assign core_data_out = 32'b0; // No data to write

assign data_mem_stb = data_mem_cyc;

logic instr_resp, instr_req, dmem_resp, rst;
logic [31:0] dmem_data;

logic [31:0] instr_addr;
logic [127:0] instr_data;

always_ff @(posedge clk_core) begin
    rst <= rst_core;
    dmem_resp <= data_mem_ack;
    dmem_data <= data_mem_data_in;
end


ssrv_top u_ssrv_top (
    .clk            (clk_core),
    .rst            (rst),

    .imem_req       (instr_req),
    .imem_addr      (instr_addr),
    .imem_rdata     (instr_data),
    .imem_resp      (instr_resp),
    .imem_err       (1'b0),

    .dmem_req       (data_mem_cyc),
    .dmem_cmd       (data_mem_we),
    .dmem_width     (), // strobe 2'b10 word, 2'b01 halfword, 2'b00 byte
    .dmem_addr      (data_mem_addr),
    .dmem_wdata     (data_mem_data_out),
    .dmem_rdata     (dmem_data),
    .dmem_resp      (dmem_resp),
    .dmem_err       (1'b0)
);

typedef enum logic [3:0] {
    IDLE              = 4'd0,
    READ_WB_1         = 4'd1,
    READ_NEXT_INSTR   = 4'd2,
    READ_WB_2         = 4'd3,
    READ_NEXT_INSTR_2 = 4'd4,
    READ_WB_3         = 4'd5,
    READ_NEXT_INSTR_3 = 4'd6,
    READ_WB_4         = 4'd7,
    WB                = 4'd8
} fsm_state_t;

fsm_state_t state;

always_ff @(posedge clk_core) begin
    if(rst_core) begin
        instr_resp <=0;
        instr_data <= 0;
    end else begin
        case (state)
            IDLE: begin
                instr_resp <= 0;
                if(instr_req) begin
                    core_addr <= instr_addr;
                    core_cyc  <= 1;
                    state     <= READ_WB_1;
                end
            end

            READ_WB_1: begin
                if(core_ack) begin
                    core_cyc         <= 0;
                    instr_data[31:0] <= core_data_in;
                    core_addr        <= core_addr + 4;
                    state            <= READ_NEXT_INSTR; 
                end
            end

            READ_NEXT_INSTR: begin
                core_cyc <= 1;
                state    <= READ_WB_2;
            end

            READ_WB_2: begin
                if(core_ack) begin
                    core_cyc          <= 0;
                    instr_data[63:32] <= core_data_in;
                    core_addr         <= core_addr + 4;
                    state             <= READ_NEXT_INSTR_2; 
                end
            end

            READ_NEXT_INSTR_2: begin
                core_cyc <= 1;
                state    <= READ_WB_3;
            end

            READ_WB_3: begin
                if(core_ack) begin
                    core_cyc          <= 0;
                    instr_data[95:64] <= core_data_in;
                    core_addr         <= core_addr + 4;
                    state             <= READ_NEXT_INSTR_3; 
                end
            end

            READ_NEXT_INSTR_3: begin
                core_cyc <= 1;
                state    <= READ_WB_4;
            end

            READ_WB_4: begin
                if(core_ack) begin
                    core_cyc           <= 0;
                    instr_data[127:96] <= core_data_in;
                    state              <= WB; 
                end
            end

            WB: begin
                instr_resp <= 1;
                state      <= IDLE;
            end

            default: state <= IDLE;
        endcase
    end
end


endmodule
