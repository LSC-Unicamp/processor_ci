
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf airisc_core_complex'
                sh 'git clone --recursive --depth=1 https://github.com/Fraunhofer-IMS/airisc_core_complex airisc_core_complex'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("airisc_core_complex") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s airi5c_core -I src/ src/airi5c_EX_pregs.v src/airi5c_PC_mux.v src/airi5c_WB_pregs.v src/airi5c_alu.v src/airi5c_branch_prediction.v src/airi5c_core.v src/airi5c_csr_file.v src/airi5c_ctrl.v src/airi5c_debug_module.v src/airi5c_debug_rom.v src/airi5c_decode.v src/airi5c_decompression.v src/airi5c_dmem_latch.v src/airi5c_dpsram_4x8to32bit_wrapper.v src/airi5c_fetch.v src/airi5c_imm_gen.v src/airi5c_mem_arbiter.v src/airi5c_periph_mux.v src/airi5c_pipeline.v src/airi5c_prebuf_fifo.v src/airi5c_regfile.v src/airi5c_src_a_mux.v src/airi5c_src_b_mux.v src/airi5c_sync_to_hasti_bridge.v src/airi5c_wb_src_mux.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("airisc_core_complex") {
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
                                dir("airisc_core_complex") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p airisc_core_complex -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("airisc_core_complex") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p airisc_core_complex -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("airisc_core_complex") {
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
                                dir("airisc_core_complex") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p airisc_core_complex -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("airisc_core_complex") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p airisc_core_complex -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("airisc_core_complex") {
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
