
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf SuperScalar-RISCV-CPU'
                sh 'git clone --recursive --depth=1 https://github.com/risclite/SuperScalar-RISCV-CPU SuperScalar-RISCV-CPU'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("SuperScalar-RISCV-CPU") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s ssrv_top -I rtl/ rtl/alu.v rtl/define.v rtl/define_para.v rtl/include_func.v rtl/instrbits.v rtl/instrman.v rtl/lsu.v rtl/membuf.v rtl/mprf.v rtl/mul.v rtl/predictor.v rtl/schedule.v rtl/ssrv_top.v rtl/sys_csr.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("SuperScalar-RISCV-CPU") {
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
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SuperScalar-RISCV-CPU -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SuperScalar-RISCV-CPU -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("SuperScalar-RISCV-CPU") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
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
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SuperScalar-RISCV-CPU -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SuperScalar-RISCV-CPU -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("SuperScalar-RISCV-CPU") {
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
