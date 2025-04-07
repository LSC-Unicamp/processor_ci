
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf rv3n'
                sh 'git clone --recursive --depth=1 https://github.com/risclite/rv3n rv3n'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("rv3n") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s rv3n_top -I rtl rtl/define.v rtl/define_para.v rtl/include_func.v rtl/rv3n_chain_manager.v rtl/rv3n_csr.v rtl/rv3n_func_jcond.v rtl/rv3n_func_lsu.v rtl/rv3n_func_muldiv.v rtl/rv3n_func_op.v rtl/rv3n_gsr.v rtl/rv3n_predictor.v rtl/rv3n_stage_ch.v rtl/rv3n_stage_dc.v rtl/rv3n_stage_id.v rtl/rv3n_stage_if.v rtl/rv3n_top.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("rv3n") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config -o /jenkins/processor_ci_utils/labels"
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
                                dir("rv3n") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p rv3n -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("rv3n") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p rv3n -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("rv3n") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                    sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                    /eda/processor_ci_tests/config.json --p /dev/ttyACM0 -m rv32i -k 0x434F4C4F'
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
                                dir("rv3n") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p rv3n -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("rv3n") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p rv3n -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("rv3n") {
                                    sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                    sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                    /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459'
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
            junit '**/*.xml'
        }
    }
}
