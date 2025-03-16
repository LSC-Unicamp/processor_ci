
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf Hazard3'
                sh 'git clone --recursive --depth=1 https://github.com/Wren6991/Hazard3 Hazard3'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Hazard3") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s hazard3_core -I hdl/ hdl/hazard3_core.v hdl/hazard3_cpu_1port.v hdl/hazard3_cpu_2port.v hdl/hazard3_csr.v hdl/hazard3_decode.v hdl/hazard3_frontend.v hdl/hazard3_instr_decompress.v hdl/hazard3_irq_ctrl.v hdl/hazard3_pmp.v hdl/hazard3_power_ctrl.v hdl/hazard3_regfile_1w2r.v hdl/hazard3_triggers.v hdl/arith/hazard3_alu.v hdl/arith/hazard3_branchcmp.v hdl/arith/hazard3_mul_fast.v hdl/arith/hazard3_muldiv_seq.v hdl/arith/hazard3_onehot_encode.v hdl/arith/hazard3_onehot_priority.v hdl/arith/hazard3_onehot_priority_dynamic.v hdl/arith/hazard3_priority_encode.v hdl/arith/hazard3_shift_barrel.v hdl/debug/cdc/hazard3_apb_async_bridge.v hdl/debug/cdc/hazard3_reset_sync.v hdl/debug/cdc/hazard3_sync_1bit.v hdl/debug/dm/hazard3_dm.v hdl/debug/dm/hazard3_sbus_to_ahb.v hdl/debug/dtm/hazard3_ecp5_jtag_dtm.v hdl/debug/dtm/hazard3_jtag_dtm.v hdl/debug/dtm/hazard3_jtag_dtm_core.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Hazard3") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o  /jenkins/processor_ci_utils/labels"
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
                                dir("Hazard3") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Hazard3 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("Hazard3") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Hazard3 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("Hazard3") {
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
                                dir("Hazard3") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Hazard3 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("Hazard3") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Hazard3 -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("Hazard3") {
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
