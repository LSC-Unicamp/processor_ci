read_verilog -sv /eda/processor-ci-controller/modules/uart.sv
read_verilog /eda/processor-ci-controller/modules/UART/rtl/uart_rx.v
read_verilog /eda/processor-ci-controller/modules/UART/rtl/uart_tx.v

#read_verilog -sv /eda/processor-ci-controller/modules/spi.sv;
#read_verilog -sv /eda/processor-ci-controller/modules/SPI-Slave/rtl/spi_slave.sv;

read_verilog -sv /eda/processor_ci/internal/ahblite_to_wishbone.sv
read_verilog -sv /eda/processor_ci/internal/axi4_to_wishbone.sv
read_verilog -sv /eda/processor_ci/internal/axi4lite_to_wishbone.sv
read_verilog -sv /eda/processor-ci-controller/rtl/fifo.sv
read_verilog -sv /eda/processor-ci-controller/rtl/reset.sv
read_verilog -sv /eda/processor-ci-controller/rtl/clk_divider.sv
read_verilog -sv /eda/processor-ci-controller/rtl/memory.sv
read_verilog -sv /eda/processor-ci-controller/rtl/interpreter.sv
read_verilog -sv /eda/processor-ci-controller/rtl/controller.sv
read_verilog -sv /eda/processor-ci-controller/rtl/timer.sv
read_verilog -sv /eda/processor_ci/internal/fpga_top.sv

set_param general.maxThreads 16

read_xdc "/eda/processor_ci/constraints/zedboard.xdc"
set_property PROCESSING_ORDER EARLY [get_files /eda/processor_ci/constraints/zedboard.xdc]

# synth
synth_design -top "fpga_top" -part "xc7z020clg484-1"

# place and route
opt_design
place_design

report_utilization -hierarchical -file zedboard_utilization_hierarchical_place.rpt
report_utilization               -file zedboard_utilization_place.rpt
report_io                        -file zedboard_io.rpt
report_control_sets -verbose     -file zedboard_control_sets.rpt
report_clock_utilization         -file zedboard_clock_utilization.rpt


route_design

report_timing_summary -no_header -no_detailed_paths
report_route_status                            -file zedboard_route_status.rpt
report_drc                                     -file zedboard_drc.rpt
report_timing_summary -datasheet -max_paths 10 -file zedboard_timing.rpt
report_power                                   -file zedboard_power.rpt


# write bitstream
write_bitstream -force "zedboard.bit"

exit
