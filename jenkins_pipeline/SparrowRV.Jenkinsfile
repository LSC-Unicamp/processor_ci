
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf SparrowRV'
                sh 'git clone --recursive --depth=1 https://github.com/xiaowuzxc/SparrowRV SparrowRV'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("SparrowRV") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s core -I rtl/ rtl/config.v rtl/defines.v rtl/core/core.v rtl/core/csr.v rtl/core/div.v rtl/core/dpram.v rtl/core/idex.v rtl/core/iram.v rtl/core/regs.v rtl/core/rstc.v rtl/core/sctr.v rtl/core/trap.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("SparrowRV") {
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
                                dir("SparrowRV") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p SparrowRV -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("SparrowRV") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p SparrowRV -b digilent_arty_a7_100t -l'
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
