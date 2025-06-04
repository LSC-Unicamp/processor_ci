set_device -name GW2AR-18C GW2AR-LV18QN88C8/I7

add_file /eda/processor_ci/constraints/gowin_tangnano_20k.cst
add_file /eda/processor_ci/constraints/gowin_tangnano_20k.sdc

add_file /eda/processor-ci-controller/modules/uart.sv
add_file /eda/processor-ci-controller/modules/UART/rtl/uart_rx.v
add_file /eda/processor-ci-controller/modules/UART/rtl/uart_tx.v
add_file /eda/processor-ci-controller/rtl/fifo.sv
add_file /eda/processor-ci-controller/rtl/reset.sv
add_file /eda/processor-ci-controller/rtl/clk_divider.sv
add_file /eda/processor-ci-controller/rtl/memory.sv
add_file /eda/processor-ci-controller/rtl/interpreter.sv
add_file /eda/processor-ci-controller/rtl/controller.sv
add_file /eda/processor-ci-controller/rtl/timer.sv
add_file /eda/processor_ci/internal/fpga_top.sv
add_file /eda/processor_ci/internal/ahblite_to_wishbone.sv
add_file /eda/processor_ci/internal/axi4_to_wishbone.sv
add_file /eda/processor_ci/internal/axi4lite_to_wishbone.sv

set_option -top_module fpga_top 

set_option -use_mspi_as_gpio 1
set_option -use_sspi_as_gpio 1
set_option -use_ready_as_gpio 1
set_option -use_done_as_gpio 1
set_option -rw_check_on_ram 1
run all