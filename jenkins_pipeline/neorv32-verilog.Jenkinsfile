
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf neorv32-verilog'
                sh 'git clone --recursive --depth=1 https://github.com/stnolting/neorv32-verilog neorv32-verilog'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("neorv32-verilog") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=2005               neorv32/rtl/core/neorv32_application_image.vhd neorv32/rtl/core/neorv32_boot_rom.vhd neorv32/rtl/core/neorv32_bootloader_image.vhd neorv32/rtl/core/neorv32_bus.vhd neorv32/rtl/core/neorv32_cache.vhd neorv32/rtl/core/neorv32_cfs.vhd neorv32/rtl/core/neorv32_clockgate.vhd neorv32/rtl/core/neorv32_cpu.vhd neorv32/rtl/core/neorv32_cpu_alu.vhd neorv32/rtl/core/neorv32_cpu_control.vhd neorv32/rtl/core/neorv32_cpu_cp_bitmanip.vhd neorv32/rtl/core/neorv32_cpu_cp_cfu.vhd neorv32/rtl/core/neorv32_cpu_cp_cond.vhd neorv32/rtl/core/neorv32_cpu_cp_crypto.vhd neorv32/rtl/core/neorv32_cpu_cp_fpu.vhd neorv32/rtl/core/neorv32_cpu_cp_muldiv.vhd neorv32/rtl/core/neorv32_cpu_cp_shifter.vhd neorv32/rtl/core/neorv32_cpu_decompressor.vhd neorv32/rtl/core/neorv32_cpu_lsu.vhd neorv32/rtl/core/neorv32_cpu_pmp.vhd neorv32/rtl/core/neorv32_cpu_regfile.vhd neorv32/rtl/core/neorv32_crc.vhd neorv32/rtl/core/neorv32_debug_auth.vhd neorv32/rtl/core/neorv32_debug_dm.vhd neorv32/rtl/core/neorv32_debug_dtm.vhd neorv32/rtl/core/neorv32_dma.vhd neorv32/rtl/core/neorv32_dmem.vhd neorv32/rtl/core/neorv32_fifo.vhd neorv32/rtl/core/neorv32_gpio.vhd neorv32/rtl/core/neorv32_gptmr.vhd neorv32/rtl/core/neorv32_imem.vhd neorv32/rtl/core/neorv32_mtime.vhd neorv32/rtl/core/neorv32_neoled.vhd neorv32/rtl/core/neorv32_onewire.vhd neorv32/rtl/core/neorv32_package.vhd neorv32/rtl/core/neorv32_pwm.vhd neorv32/rtl/core/neorv32_sdi.vhd neorv32/rtl/core/neorv32_slink.vhd neorv32/rtl/core/neorv32_spi.vhd neorv32/rtl/core/neorv32_sys.vhd neorv32/rtl/core/neorv32_sysinfo.vhd neorv32/rtl/core/neorv32_top.vhd neorv32/rtl/core/neorv32_trng.vhd neorv32/rtl/core/neorv32_twd.vhd neorv32/rtl/core/neorv32_twi.vhd neorv32/rtl/core/neorv32_uart.vhd neorv32/rtl/core/neorv32_wdt.vhd neorv32/rtl/core/neorv32_xbus.vhd neorv32/rtl/core/neorv32_xip.vhd neorv32/rtl/core/neorv32_xirq.vhd neorv32/rtl/processor_templates/neorv32_ProcessorTop_Minimal.vhd neorv32/rtl/processor_templates/neorv32_ProcessorTop_MinimalBoot.vhd neorv32/rtl/processor_templates/neorv32_ProcessorTop_UP5KDemo.vhd neorv32/rtl/system_integration/neorv32_litex_core_complex.vhd neorv32/rtl/system_integration/neorv32_vivado_ip.vhd neorv32/rtl/system_integration/xbus2ahblite_bridge.vhd neorv32/rtl/system_integration/xbus2axi4lite_bridge.vhd src/neorv32_verilog_wrapper.vhd sim/testbench.v sim/uart_sim_receiver.v neorv32/rtl/test_setups/neorv32_test_setup_approm.vhd neorv32/rtl/test_setups/neorv32_test_setup_bootloader.vhd neorv32/rtl/test_setups/neorv32_test_setup_on_chip_debugger.vhd neorv32/sim/neorv32_tb.vhd neorv32/sim/sim_uart_rx.vhd neorv32/sim/xbus_gateway.vhd neorv32/sim/xbus_memory.vhd"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("neorv32-verilog") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o /eda/processor_ci_utils/labels"
                }            
            }
        }

        stage('FPGA Build Pipeline') {
            parallel {
                
                stage('colorlight_i9') {
                    options {
                        lock(resource: 'colorlight_i9')
                    }
                    stages {
                        stage('Synthesis and PnR') {
                            steps {
                                dir("neorv32-verilog") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p neorv32-verilog -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("neorv32-verilog") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p neorv32-verilog -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("neorv32-verilog") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                    sh 'python3 /eda/processor_ci_tests/test_runner/run.py --config                                    /eda/processor_ci_tests/test_runner/config.json --port /dev/ttyACM0'
                                }
                            }
                        }
                    }
                }
                
                stage('digilent_arty_a7_100t') {
                    options {
                        lock(resource: 'digilent_arty_a7_100t')
                    }
                    stages {
                        stage('Synthesis and PnR') {
                            steps {
                                dir("neorv32-verilog") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p neorv32-verilog -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("neorv32-verilog") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p neorv32-verilog -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("neorv32-verilog") {
                                    sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                    sh 'python3 /eda/processor_ci_tests/test_runner/run.py --config                                    /eda/processor_ci_tests/test_runner/config.json --port /dev/ttyUSB1'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    post {
        always {
            junit '**/test-reports/*.xml'
        }
    }
}
