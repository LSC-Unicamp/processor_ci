read_verilog -sv /eda/processor-ci-controller/modules/uart.sv
read_verilog /eda/processor-ci-controller/modules/UART/rtl/uart_rx.v
read_verilog /eda/processor-ci-controller/modules/UART/rtl/uart_tx.v

#read_verilog -sv /eda/processor-ci-controller/modules/spi.sv;
#read_verilog -sv /eda/processor-ci-controller/modules/SPI-Slave/rtl/spi_slave.sv;

read_verilog -sv /eda/processor-ci-controller/rtl/ahblite_to_wishbone.sv
read_verilog -sv /eda/processor-ci-controller/rtl/axi4_to_wishbone.sv
read_verilog -sv /eda/processor-ci-controller/rtl/axi4lite_to_wishbone.sv
read_verilog -sv /eda/processor-ci-controller/rtl/fifo.sv
read_verilog -sv /eda/processor-ci-controller/rtl/reset.sv
read_verilog -sv /eda/processor-ci-controller/rtl/clk_divider.sv
read_verilog -sv /eda/processor-ci-controller/rtl/memory.sv
read_verilog -sv /eda/processor-ci-controller/rtl/interpreter.sv
read_verilog -sv /eda/processor-ci-controller/rtl/controller.sv
read_verilog -sv /eda/processor-ci-controller/rtl/timer.sv

set_param general.maxThreads 16

read_xdc "/eda/processor_ci/constraints/digilent_nexys4_ddr.xdc"
set_property PROCESSING_ORDER EARLY [get_files /eda/processor_ci/constraints/digilent_nexys4_ddr.xdc]

# synth
synth_design -top "processorci_top" -part "xc7a100tcsg324-1"

# place and route
opt_design
place_design

report_utilization -hierarchical -file digilent_nexys4ddr_utilization_hierarchical_place.rpt
report_utilization               -file digilent_nexys4ddr_utilization_place.rpt
report_io                        -file digilent_nexys4ddr_io.rpt
report_control_sets -verbose     -file digilent_nexys4ddr_control_sets.rpt
report_clock_utilization         -file digilent_nexys4ddr_clock_utilization.rpt


route_design

report_timing_summary -no_header -no_detailed_paths
report_route_status                            -file digilent_nexys4ddr_route_status.rpt
report_drc                                     -file digilent_nexys4ddr_drc.rpt
report_timing_summary -datasheet -max_paths 10 -file digilent_nexys4ddr_timing.rpt
report_power                                   -file digilent_nexys4ddr_power.rpt


# write bitstream
write_bitstream -force "digilent_nexys4_ddr.bit"

exit