module processorci_top (
    `ifdef DIFERENCIAL_CLK
    input  logic clk_ref_p,
    input  logic clk_ref_n,
    `else
    input  logic clk,
    `endif

    input  logic reset,

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
logic core_cyc;
logic core_stb;
logic core_we;
logic [31:0] core_addr;
logic [31:0] core_data_out;
logic [31:0] core_data_in;
logic        core_ack;

`ifndef CLOCK_FREQ
`define CLOCK_FREQ 25000000 // 100MHz
`endif
`ifndef MEMORY_SIZE
`define MEMORY_SIZE 1024 // 1KB
`endif

Controller #(
    .CLK_FREQ           (`CLOCK_FREQ),
    .BIT_RATE           (115200),
    .PAYLOAD_BITS       (8),
    .BUFFER_SIZE        (8),
    .PULSE_CONTROL_BITS (32),
    .BUS_WIDTH          (32),
    .WORD_SIZE_BY       (4),
    .ID                 (32'h7700006A),
    .RESET_CLK_CYCLES   (20),
    .MEMORY_FILE        (""),
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
    
    // Barramento padrão (não AXI4-Lite)
    .core_cyc_i         (core_cyc),
    .core_stb_i         (core_stb),
    .core_we_i          (core_we),
    .core_addr_i        (core_addr),
    .core_data_i        (core_data_out),
    .core_data_o        (core_data_in),
    .core_ack_o         (core_ack)
);

// Core space

Grande_Risco5 #(
    .BOOT_ADDRESS           (32'h00000000),
    .I_CACHE_SIZE           (256),
    .D_CACHE_SIZE           (256),
    .DATA_WIDTH             (32),
    .ADDR_WIDTH             (32),
    .BRANCH_PREDICTION_SIZE (128)
) Processor (
    .clk    (clk_core),
    .rst_n  (~rst_core),
    .halt   (1'b0),

    .cyc_o  (core_cyc),
    .stb_o  (core_stb),
    .we_o   (core_we),

    .addr_o (core_addr),
    .data_o (core_data_out),

    .ack_i  (core_ack),
    .data_i (core_data_in),

    .interruption (1'b0)
);

// Clock inflaestructure

`ifdef HIGH_CLK

initial begin
    clk_o = 1'b0; // 50mhz or 100mhz
end

`ifdef DIFERENCIAL_CLK
logic clk_ref; // Sinal de clock single-ended

// Instância do buffer diferencial
IBUFDS #(
    .DIFF_TERM("FALSE"),     // Habilita ou desabilita o terminador diferencial
    .IBUF_LOW_PWR("TRUE"),   // Ativa o modo de baixa potência
    .IOSTANDARD("DIFF_SSTL15")
) ibufds_inst (
    .O(clk_ref),    // Clock single-ended de saída
    .I(clk_ref_p),  // Entrada diferencial positiva
    .IB(clk_ref_n)  // Entrada diferencial negativa
);


always @(posedge clk_ref) begin
    clk_o = ~clk_o;
end
`else
always @(posedge clk) begin
    clk_o = ~clk_o;
end
`endif

`endif

// Reset Inflaestructure


ResetBootSystem #(
    .CYCLES(20)
) ResetBootSystem(
    `ifdef HIGH_CLK
    .clk    (clk_o),
    `else
    .clk    (clk),
    `endif
    
    .rst_n_o(rst_n)
);
    
endmodule
