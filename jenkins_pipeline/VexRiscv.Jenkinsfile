
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf VexRiscv'
                sh 'git clone --recursive --depth=1 https://github.com/SpinalHDL/VexRiscv VexRiscv'
            }
        }

        
        stage('Verilog Convert') {
            steps {
                dir("VexRiscv") {
                    sh 'sbt "runMain vexriscv.demo.GenFull"'
                }
            }
        }
        

        stage('Simulation') {
            steps {
                dir("VexRiscv") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s VexRiscv  VexRiscv.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("VexRiscv") {
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
                                dir("VexRiscv") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p VexRiscv -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("VexRiscv") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p VexRiscv -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("VexRiscv") {
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
                                dir("VexRiscv") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p VexRiscv -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("VexRiscv") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p VexRiscv -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("VexRiscv") {
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
