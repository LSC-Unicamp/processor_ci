
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf SuperScalar-RISCV-CPU'
                sh 'git clone --recursive --depth=1 https://github.com/risclite/SuperScalar-RISCV-CPU SuperScalar-RISCV-CPU'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("SuperScalar-RISCV-CPU") {
                    echo 'FPGA > Simulation'
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("SuperScalar-RISCV-CPU") {
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
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p SuperScalar-RISCV-CPU -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p SuperScalar-RISCV-CPU -b digilent_arty_a7_100t -l'
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
