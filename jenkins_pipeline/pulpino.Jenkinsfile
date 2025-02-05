
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf pulpino'
                sh 'git clone --recursive --depth=1 https://github.com/pulp-platform/pulpino pulpino'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("pulpino") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   fpga/rtl/clk_rst_gen.v fpga/rtl/pulpemu_top.v fpga/rtl/pulpino_wrap.v rtl/apb_mock_uart.sv rtl/axi2apb_wrap.sv rtl/axi_mem_if_SP_wrap.sv rtl/axi_node_intf_wrap.sv rtl/axi_slice_wrap.sv rtl/axi_spi_slave_wrap.sv rtl/boot_code.sv rtl/boot_rom_wrap.sv rtl/clk_rst_gen.sv rtl/core2axi_wrap.sv rtl/core_region.sv rtl/dp_ram_wrap.sv rtl/instr_ram_wrap.sv rtl/periph_bus_wrap.sv rtl/peripherals.sv rtl/pulpino_top.sv rtl/ram_mux.sv rtl/random_stalls.sv rtl/sp_ram_wrap.sv rtl/components/cluster_clock_gating.sv rtl/components/cluster_clock_inverter.sv rtl/components/cluster_clock_mux2.sv rtl/components/dp_ram.sv rtl/components/generic_fifo.sv rtl/components/pulp_clock_gating.sv rtl/components/pulp_clock_inverter.sv rtl/components/pulp_clock_mux2.sv rtl/components/rstgen.sv rtl/components/sp_ram.sv rtl/includes/apb_bus.sv rtl/includes/apu_defines.sv rtl/includes/axi_bus.sv rtl/includes/config.sv rtl/includes/debug_bus.sv tb/i2c_eeprom_model.sv tb/if_spi_master.sv tb/if_spi_slave.sv tb/jtag_dpi.sv tb/pkg_spi.sv tb/tb.sv tb/tb_jtag_pkg.sv tb/tb_mem_pkg.sv tb/tb_spi_pkg.sv tb/uart.sv"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("pulpino") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o /jenkins/processor_ci_utils/labels.json"
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
                                dir("pulpino") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p pulpino -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("pulpino") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p pulpino -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("pulpino") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                }
                            }
                        }
                    }
                }
                
                stage('digilent_nexys4_ddr') {
                    options {
                        lock(resource: 'digilent_nexys4_ddr')
                    }
                    stages {
                        stage('Synthesis and PnR') {
                            steps {
                                dir("pulpino") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p pulpino -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("pulpino") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p pulpino -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("pulpino") {
                                    sh 'echo "Test for FPGA in /dev/ttyUSB1"'
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
