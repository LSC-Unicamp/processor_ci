yosys read_systemverilog -defer /eda/processor-ci-controller/modules/uart.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/modules/UART/rtl/uart_rx.v
yosys read_systemverilog -defer /eda/processor-ci-controller/modules/UART/rtl/uart_tx.v
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/fifo.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/reset.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/clk_divider.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/memory.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/interpreter.sv
yosys read_systemverilog -defer /eda/processor-ci-controller/rtl/controller.sv

yosys read_systemverilog -link

yosys synth_ecp5 -json colorlight_i9.json -top processorci_top -abc9