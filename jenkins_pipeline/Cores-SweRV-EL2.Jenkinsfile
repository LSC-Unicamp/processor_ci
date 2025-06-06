
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf Cores-SweRV-EL2'
                sh 'git clone --recursive --depth=1 https://github.com/chipsalliance/Cores-SweRV-EL2 Cores-SweRV-EL2'
            }
        }

        
        stage('Verilog Convert') {
            steps {
                dir("Cores-SweRV-EL2") {
                    sh 'RV_ROOT=$(pwd) configs/veer.config -set=fpga_optimize=1 -target=default -set=btb_size=128'
                }
            }
        }
        

        stage('Simulation') {
            steps {
                dir("Cores-SweRV-EL2") {
                    echo "simulation not supported"
                }
            }https://processorci.lsc.ic.unicamp.br/
        }

         stage('Utilities')  {
            steps {
                dir("Cores-SweRV-EL2") {
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
                                dir("Cores-SweRV-EL2") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Cores-SweRV-EL2 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("Cores-SweRV-EL2") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Cores-SweRV-EL2 -b digilent_arty_a7_100t -l'
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
