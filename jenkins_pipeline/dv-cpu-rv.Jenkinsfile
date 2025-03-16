
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf dv-cpu-rv'
                sh 'git clone --recursive --depth=1 https://github.com/devindang/dv-cpu-rv dv-cpu-rv'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("dv-cpu-rv") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s rv_core  core/rtl/rv_alu.v core/rtl/rv_alu_ctrl.v core/rtl/rv_branch_predict.v core/rtl/rv_core.v core/rtl/rv_ctrl.v core/rtl/rv_div.v core/rtl/rv_forward.v core/rtl/rv_hzd_detect.v core/rtl/rv_imm_gen.v core/rtl/rv_mem_map.v core/rtl/rv_mul.v core/rtl/rv_rf.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("dv-cpu-rv") {
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
                                dir("dv-cpu-rv") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p dv-cpu-rv -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("dv-cpu-rv") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p dv-cpu-rv -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("dv-cpu-rv") {
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
                                dir("dv-cpu-rv") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p dv-cpu-rv -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("dv-cpu-rv") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p dv-cpu-rv -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("dv-cpu-rv") {
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
