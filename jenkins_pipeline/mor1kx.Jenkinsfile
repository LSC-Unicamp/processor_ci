
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf mor1kx'
                sh 'git clone --recursive --depth=1 https://github.com/openrisc/mor1kx mor1kx'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("mor1kx") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s mor1kx -I rtl/verilog rtl/verilog/mor1kx-defines.v rtl/verilog/mor1kx-sprs.v rtl/verilog/mor1kx.v rtl/verilog/mor1kx_branch_prediction.v rtl/verilog/mor1kx_branch_predictor_gshare.v rtl/verilog/mor1kx_branch_predictor_saturation_counter.v rtl/verilog/mor1kx_branch_predictor_simple.v rtl/verilog/mor1kx_bus_if_wb32.v rtl/verilog/mor1kx_cache_lru.v rtl/verilog/mor1kx_cfgrs.v rtl/verilog/mor1kx_cpu.v rtl/verilog/mor1kx_cpu_cappuccino.v rtl/verilog/mor1kx_cpu_espresso.v rtl/verilog/mor1kx_cpu_prontoespresso.v rtl/verilog/mor1kx_ctrl_cappuccino.v rtl/verilog/mor1kx_ctrl_espresso.v rtl/verilog/mor1kx_ctrl_prontoespresso.v rtl/verilog/mor1kx_dcache.v rtl/verilog/mor1kx_decode.v rtl/verilog/mor1kx_decode_execute_cappuccino.v rtl/verilog/mor1kx_dmmu.v rtl/verilog/mor1kx_execute_alu.v rtl/verilog/mor1kx_execute_ctrl_cappuccino.v rtl/verilog/mor1kx_fetch_cappuccino.v rtl/verilog/mor1kx_fetch_espresso.v rtl/verilog/mor1kx_fetch_prontoespresso.v rtl/verilog/mor1kx_fetch_tcm_prontoespresso.v rtl/verilog/mor1kx_icache.v rtl/verilog/mor1kx_immu.v rtl/verilog/mor1kx_lsu_cappuccino.v rtl/verilog/mor1kx_lsu_espresso.v rtl/verilog/mor1kx_pcu.v rtl/verilog/mor1kx_pic.v rtl/verilog/mor1kx_rf_cappuccino.v rtl/verilog/mor1kx_rf_espresso.v rtl/verilog/mor1kx_simple_dpram_sclk.v rtl/verilog/mor1kx_store_buffer.v rtl/verilog/mor1kx_ticktimer.v rtl/verilog/mor1kx_true_dpram_sclk.v rtl/verilog/mor1kx_wb_mux_cappuccino.v rtl/verilog/mor1kx_wb_mux_espresso.v rtl/verilog/pfpu32/pfpu32_addsub.v rtl/verilog/pfpu32/pfpu32_cmp.v rtl/verilog/pfpu32/pfpu32_f2i.v rtl/verilog/pfpu32/pfpu32_i2f.v rtl/verilog/pfpu32/pfpu32_muldiv.v rtl/verilog/pfpu32/pfpu32_rnd.v rtl/verilog/pfpu32/pfpu32_top.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("mor1kx") {
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
                                dir("mor1kx") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p mor1kx -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("mor1kx") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p mor1kx -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("mor1kx") {
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
                                dir("mor1kx") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p mor1kx -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("mor1kx") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p mor1kx -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("mor1kx") {
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
