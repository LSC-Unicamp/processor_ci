
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf Risco-5'
                sh 'git clone --recursive --depth=1 https://github.com/JN513/Risco-5.git Risco-5'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Risco-5") {
                    sh "iverilog -o simulation.out -g2005                  -s soc_tb -I src/core/ src/core/alu.v src/core/alu_control.v src/core/control_unit.v src/core/core.v src/core/csr_unit.v src/core/immediate_generator.v src/core/mdu.v src/core/mux.v src/core/pc.v src/core/registers.v tests/soc_test.v src/peripheral/bus.v src/peripheral/fifo.v src/peripheral/gpios.v src/peripheral/gpio.v src/peripheral/leds.v src/peripheral/memory.v src/peripheral/pwm.v src/peripheral/soc.v src/peripheral/uart_rx.v src/peripheral/uart_tx.v src/peripheral/uart.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Risco-5") {
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
                                dir("Risco-5") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Risco-5 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("Risco-5") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Risco-5 -b digilent_arty_a7_100t -l'
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
