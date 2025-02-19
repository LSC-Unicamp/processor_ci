read_verilog /eda/processor-ci-controller/modules/uart.v
read_verilog /eda/processor-ci-controller/modules/UART/rtl/uart_rx.v
read_verilog /eda/processor-ci-controller/modules/UART/rtl/uart_tx.v

#read_verilog /eda/processor-ci-controller/modules/spi.v;
#read_verilog /eda/processor-ci-controller/modules/SPI-Slave/rtl/spi_slave.v;

read_verilog /eda/processor-ci-controller/src/fifo.v
read_verilog /eda/processor-ci-controller/src/reset.v
read_verilog /eda/processor-ci-controller/src/clk_divider.v
read_verilog /eda/processor-ci-controller/src/memory.v
read_verilog /eda/processor-ci-controller/src/interpreter.v
read_verilog /eda/processor-ci-controller/src/controller.v

set ID [lindex $argv 0]
set CLOCK_FREQ [lindex $argv 1]
set MEMORY_SIZE [lindex $argv 2]
set HIGH_CLK 1

set DIFERENCIAL_CLK 1

read_xdc "/eda/processor_ci/constraints/xilinx_vc709.xdc"
set_property PROCESSING_ORDER EARLY [get_files /eda/processor_ci/constraints/xilinx_vc709.xdc]

# synth
synth_design -top "processorci_top" -part "xc7vx690tffg1761-2" -verilog_define $ID -verilog_define $CLOCK_FREQ -verilog_define $MEMORY_SIZE \
    -verilog_define $HIGH_CLK -verilog_define $DIFERENCIAL_CLK

# place and route
opt_design
place_design

report_utilization -hierarchical -file virtex_utilization_hierarchical_place.rpt
report_utilization -file virtex_utilization_place.rpt
report_io -file virtex_io.rpt
report_control_sets -verbose -file virtex_control_sets.rpt
report_clock_utilization -file virtex_clock_utilization.rpt

route_design

report_timing_summary -no_header -no_detailed_paths
report_route_status -file virtex_route_status.rpt
report_drc -file virtex_drc.rpt
report_timing_summary -datasheet -max_paths 10 -file virtex_timing.rpt
report_power -file virtex_power.rpt

# write bitstream
write_bitstream -force "xilinx_vc709.bit"

exit