module ahb_to_wishbone #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    input logic                   HCLK,
    input logic                   HRESETn,

    // AHB Interface
    input  logic [ADDR_WIDTH-1:0] HADDR,
    input  logic [1:0]            HTRANS,
    input  logic                  HWRITE,
    input  logic [2:0]            HSIZE,
    input  logic [2:0]            HBURST,
    input  logic [3:0]            HPROT,
    input  logic                  HLOCK,
    input  logic [DATA_WIDTH-1:0] HWDATA,
    input  logic                  HREADY,
    output logic [DATA_WIDTH-1:0] HRDATA,
    output logic                  HREADYOUT,
    output logic [1:0]            HRESP,

    // Wishbone Interface
    output logic                  wb_cyc,
    output logic                  wb_stb,
    output logic                  wb_we,
    output logic [3:0]            wb_wstrb,
    output logic [ADDR_WIDTH-1:0] wb_adr,
    output logic [DATA_WIDTH-1:0] wb_dat_w,
    input  logic [DATA_WIDTH-1:0] wb_dat_r,
    input  logic                  wb_ack
);

    // Internal state
    logic ahb_active;
    logic [2:0] burst_cnt;
    logic burst_en;
    logic [ADDR_WIDTH-1:0] base_addr;
    logic [2:0] beat_size;

    // AHB access condition
    logic ahb_access;
    assign ahb_access = (HTRANS[1] || HWRITE) && HREADY;
    logic ready;

    // Response and read data
    //assign HRDATA    = wb_dat_r;
    assign HRESP     = 2'b00; // OKAY
    assign HREADYOUT = ((!ahb_active) || ready) && HRESETn;
    assign wb_dat_w  = HWDATA;

    // Burst type check
    logic is_burst;
    assign is_burst = |HBURST; // Not SINGLE

    always_ff @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            wb_cyc      <= 0;
            wb_stb      <= 0;
            wb_we       <= 0;
            wb_adr      <= 0;
            //wb_dat_w    <= 0;
            ahb_active  <= 0;
            burst_cnt   <= 0;
            burst_en    <= 0;
            base_addr   <= 0;
            beat_size   <= 0;
            ready       <= 0;
        end else begin
            // Default deassertions
            ready  <= 0;
            wb_cyc <= 0;
            wb_stb <= 0;

            if (ahb_access && !ahb_active) begin
                // Start transaction
                wb_adr     <= HADDR  & ~32'd3; // Align address to 4 bytes
                wb_we      <= HWRITE;
                //wb_dat_w   <= HWDATA;
                wb_wstrb   <= wstrb;
                wb_cyc     <= 1;
                wb_stb     <= 1;
                ahb_active <= 1;

                // Save base and setup burst
                base_addr  <= HADDR;
                beat_size  <= HSIZE;
                burst_cnt  <= get_burst_len(HBURST); // Number of beats
                burst_en   <= is_burst;
            end else if (ahb_active && wb_ack) begin
                // On ACK: if burst, prepare next beat
                if (burst_en && burst_cnt > 1) begin
                    wb_cyc     <= 1;
                    wb_stb     <= 1;
                    wb_we      <= HWRITE;
                    wb_adr     <= next_burst_addr(wb_adr, beat_size);
                    //wb_dat_w   <= HWDATA;
                    burst_cnt  <= burst_cnt - 1;
                    ahb_active <= 1; // continue burst
                end else begin
                    ahb_active <= 0;
                    burst_en   <= 0;
                    ready      <= 1;
                    HRDATA     <= wb_dat_r;
                end
            end
        end
    end

    // Write Strobe Translation
    logic [3:0] wstrb;

    always_comb begin
        wstrb = 4'b0000;
        case (HSIZE)
            3'b000: begin // 1 byte
                case (HADDR[1:0])
                    2'b00: wstrb = 4'b0001;
                    2'b01: wstrb = 4'b0010;
                    2'b10: wstrb = 4'b0100;
                    2'b11: wstrb = 4'b1000;
                endcase
            end
            3'b001: begin // 2 bytes (halfword)
                case (HADDR[1:0])
                    2'b00: wstrb = 4'b0011;
                    2'b10: wstrb = 4'b1100;
                    default: wstrb = 4'b0000; // invalid address for halfword
                endcase
            end
            3'b010: begin // 4 bytes (word)
                wstrb = 4'b1111;
            end
            default: wstrb = 4'b0000; // other sizes not supported
        endcase
    end

    // Function to compute number of beats from HBURST
    function [4:0] get_burst_len(input [2:0] burst);
        case (burst)
            3'b000: get_burst_len = 5'd1;  // SINGLE
            3'b001: get_burst_len = 5'd4;  // INCR4
            3'b010: get_burst_len = 5'd8;  // INCR8
            3'b011: get_burst_len = 5'd16; // INCR16
            default: get_burst_len = 5'd1; // INCR (undefined length)
        endcase
    endfunction

    // Function to calculate next burst address (incremental only)
    function [ADDR_WIDTH-1:0] next_burst_addr(
        input [ADDR_WIDTH-1:0] addr,
        input [2:0] size
    );
        begin
            next_burst_addr = addr + (1 << size); // increment by beat size
        end
    endfunction

endmodule
