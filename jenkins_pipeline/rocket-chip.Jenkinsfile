
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf rocket-chip'
                sh 'git clone --recursive --depth=1 https://github.com/chipsalliance/rocket-chip rocket-chip'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("rocket-chip") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   src/main/resources/vsrc/AsyncResetReg.v src/main/resources/vsrc/ClockDivider2.v src/main/resources/vsrc/ClockDivider3.v src/main/resources/vsrc/EICG_wrapper.v src/main/resources/vsrc/RoccBlackBox.v src/main/resources/vsrc/SimDTM.v src/main/resources/vsrc/SimJTAG.v src/main/resources/vsrc/debug_rob.v src/main/resources/vsrc/plusarg_reader.v dependencies/chisel/src/test/resources/chisel3/AnalogBlackBox.v dependencies/chisel/src/test/resources/chisel3/BlackBoxTest.v dependencies/chisel/src/test/resources/chisel3/VerilogVendingMachine.v dependencies/hardfloat/hardfloat/tests/resources/vsrc/emulator.v src/main/resources/vsrc/TestDriver.v dependencies/chisel/svsim/src/test/resources/GCD.sv"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("rocket-chip") {
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
                                dir("rocket-chip") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p rocket-chip -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("rocket-chip") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p rocket-chip -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("rocket-chip") {
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
                                dir("rocket-chip") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p rocket-chip -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("rocket-chip") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p rocket-chip -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("rocket-chip") {
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
