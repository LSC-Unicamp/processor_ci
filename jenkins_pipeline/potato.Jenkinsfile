
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf potato'
                sh 'git clone --recursive --depth=1 https://github.com/skordal/potato potato'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("potato") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=08               example/aee_rom_wrapper.vhd example/toplevel.vhd soc/pp_fifo.vhd soc/pp_soc_gpio.vhd soc/pp_soc_intercon.vhd soc/pp_soc_memory.vhd soc/pp_soc_reset.vhd soc/pp_soc_timer.vhd soc/pp_soc_uart.vhd src/pp_alu.vhd src/pp_alu_control_unit.vhd src/pp_alu_mux.vhd src/pp_comparator.vhd src/pp_constants.vhd src/pp_control_unit.vhd src/pp_core.vhd src/pp_counter.vhd src/pp_csr.vhd src/pp_csr_alu.vhd src/pp_csr_unit.vhd src/pp_decode.vhd src/pp_execute.vhd src/pp_fetch.vhd src/pp_icache.vhd src/pp_imm_decoder.vhd src/pp_memory.vhd src/pp_potato.vhd src/pp_register_file.vhd src/pp_types.vhd src/pp_utilities.vhd src/pp_wb_adapter.vhd src/pp_wb_arbiter.vhd src/pp_writeback.vhd example/tb_toplevel.vhd testbenches/tb_processor.vhd testbenches/tb_soc.vhd testbenches/tb_soc_gpio.vhd testbenches/tb_soc_intercon.vhd testbenches/tb_soc_memory.vhd testbenches/tb_soc_timer.vhd testbenches/tb_soc_uart.vhd"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("potato") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config -o /jenkins/processor_ci_utils/labels"
                }            
            }
        }

        stage('FPGA Build Pipeline') {
            parallel {
                
                stage('digilent_arty_a7_100t') {
                    options {
                        lock(resource: 'digilent_arty_a7_100t')
                    }
                    stages {
                        stage('Synthesis and PnR') {
                            steps {
                                dir("potato") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p potato -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("potato") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p potato -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459 '
                            }
                        }
                    }
                }
            }
        }
    }
    post {
        always {
            junit '**/*.xml'
        }
    }
}
