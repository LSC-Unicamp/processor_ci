
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf Baby-Risco-5'
                sh 'git clone --recursive --depth=1 https://github.com/JN513/Baby-Risco-5 Baby-Risco-5'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Baby-Risco-5") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s Core  src/core/alu.v src/core/alu_control.v src/core/control_unit.v src/core/core.v src/core/immediate_generator.v src/core/registers.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Baby-Risco-5") {
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
                                dir("Baby-Risco-5") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Baby-Risco-5 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("Baby-Risco-5") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Baby-Risco-5 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyACM0 -m rv32i -k 0x434F4C4F'
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
                                dir("Baby-Risco-5") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Baby-Risco-5 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("Baby-Risco-5") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Baby-Risco-5 -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459'
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
