read_verilog -sv /eda/processor-ci-controller/modules/uart.sv
read_verilog /eda/processor-ci-controller/modules/UART/rtl/uart_rx.v
read_verilog /eda/processor-ci-controller/modules/UART/rtl/uart_tx.v

#read_verilog -sv /eda/processor-ci-controller/modules/spi.sv;
#read_verilog -sv /eda/processor-ci-controller/modules/SPI-Slave/rtl/spi_slave.sv;

read_verilog -sv /eda/processor-ci-controller/rtl/fifo.sv
read_verilog -sv /eda/processor-ci-controller/rtl/reset.sv
read_verilog -sv /eda/processor-ci-controller/rtl/clk_divider.sv
read_verilog -sv /eda/processor-ci-controller/rtl/memory.sv
read_verilog -sv /eda/processor-ci-controller/rtl/interpreter.sv
read_verilog -sv /eda/processor-ci-controller/rtl/controller.sv

set_param general.maxThreads 16

read_xdc "/eda/processor_ci/constraints/xilinx_vc709.xdc"
set_property PROCESSING_ORDER EARLY [get_files /eda/processor_ci/constraints/xilinx_vc709.xdc]

# synth
synth_design -top "processorci_top" -part "xc7a100tcsg324-1"

# place and route
opt_design
place_design

report_utilization -hierarchical -file xilinx_vc709_utilization_hierarchical_place.rpt
report_utilization               -file xilinx_vc709_utilization_place.rpt
report_io                        -file xilinx_vc709_io.rpt
report_control_sets -verbose     -file xilinx_vc709_control_sets.rpt
report_clock_utilization         -file xilinx_vc709_clock_utilization.rpt


route_design

report_timing_summary -no_header -no_detailed_paths
report_route_status                            -file xilinx_vc709_route_status.rpt
report_drc                                     -file xilinx_vc709_drc.rpt
report_timing_summary -datasheet -max_paths 10 -file xilinx_vc709_timing.rpt
report_power                                   -file xilinx_vc709_power.rpt


# write bitstream
write_bitstream -force "xilinx_vc709.bit"

exit