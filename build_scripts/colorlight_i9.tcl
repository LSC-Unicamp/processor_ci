yosys read_systemverilog -defer /eda/processor-ci-controller/modules/uart.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/modules/UART/rtl/uart_rx.v
yosys read_systemverilog -defer /eda/processor-ci-controller/modules/UART/rtl/uart_tx.v
yosys read_systemverilog -defer /eda/processor_ci/internal/ahblite_to_wishbone.svls
yosys read_systemverilog -defer /eda/processor_ci/internal/axi4_to_wishbone.sv
yosys read_systemverilog -defer /eda/processor_ci/internal/axi4lite_to_wishbone.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/fifo.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/reset.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/clk_divider.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/memory.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/interpreter.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/controller.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/timer.sv
yosys read_systemverilog -defer /eda/processor_ci/internal/fpga_top.sv
yosys read_systemverilog -link

yosys synth_ecp5 -json colorlight_i9.json -top fpga_top -abc9