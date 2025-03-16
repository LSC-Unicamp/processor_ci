
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf leaf'
                sh 'git clone --recursive --depth=1 https://github.com/daniel-santos-7/leaf leaf'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("leaf") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=08               cpu/rtl/alu.vhdl cpu/rtl/alu_ctrl.vhdl cpu/rtl/br_detector.vhdl cpu/rtl/core.vhdl cpu/rtl/core_pkg.vhdl cpu/rtl/csrs.vhdl cpu/rtl/ex_block.vhdl cpu/rtl/id_block.vhdl cpu/rtl/id_ex_stage.vhdl cpu/rtl/if_stage.vhdl cpu/rtl/imm_gen.vhdl cpu/rtl/int_strg.vhdl cpu/rtl/leaf.vhdl cpu/rtl/lsu.vhdl cpu/rtl/main_ctrl.vhdl cpu/rtl/reg_file.vhdl cpu/rtl/wb_ctrl.vhdl soc/rtl/debug_reg.vhdl soc/rtl/leaf_soc.vhdl soc/rtl/leaf_soc_pkg.vhdl soc/rtl/ram.vhdl soc/rtl/rom.vhdl soc/rtl/soc_syscon.vhdl uart/rtl/down_counter.vhdl uart/rtl/fifo.vhdl uart/rtl/piso.vhdl uart/rtl/sipo.vhdl uart/rtl/uart.vhdl uart/rtl/uart_pkg.vhdl uart/rtl/uart_rx.vhdl uart/rtl/uart_tx.vhdl uart/rtl/uart_wbsl.vhdl cpu/tbs/alu_ctrl_tb.vhdl cpu/tbs/alu_tb.vhdl cpu/tbs/br_detector_tb.vhdl cpu/tbs/core_tb.vhdl cpu/tbs/csrs_tb.vhdl cpu/tbs/ex_block_tb.vhdl cpu/tbs/id_block_tb.vhdl cpu/tbs/id_ex_stage_tb.vhdl cpu/tbs/if_stage_tb.vhdl cpu/tbs/imm_gen_tb.vhdl cpu/tbs/int_strg_tb.vhdl cpu/tbs/lsu_tb.vhdl cpu/tbs/main_ctrl_tb.vhdl cpu/tbs/reg_file_tb.vhdl cpu/tbs/tbs_pkg.vhdl sim/rtl/leaf_sim.vhdl sim/rtl/leaf_sim_pkg.vhdl sim/rtl/sim_halt.vhdl sim/rtl/sim_io.vhdl sim/rtl/sim_mem.vhdl sim/rtl/sim_syscon.vhdl sim/tbs/sim_mem_tb.vhdl soc/tbs/leaf_soc_tb.vhdl soc/tbs/ram_tb.vhdl soc/tbs/soc_syscon_tb.vhdl uart/tbs/uart_tb.vhdl"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("leaf") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o /jenkins/processor_ci_utils/labels"
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
                                dir("leaf") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p leaf -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("leaf") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p leaf -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("leaf") {
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
                                dir("leaf") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p leaf -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("leaf") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p leaf -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("leaf") {
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
