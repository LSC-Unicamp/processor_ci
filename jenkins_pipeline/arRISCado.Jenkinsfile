
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf arRISCado'
                sh 'git clone --recursive --depth=1 https://github.com/arRISCado/arRISCado arRISCado'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("arRISCado") {
                    sh "iverilog -o simulation.out -g2005                  -s cpu  project/cpu.v project/flash.v project/mmu.v project/ram.v project/rom.v project/top.v project/uart.v project/cpu/alu.v project/cpu/decode.v project/cpu/divider.v project/cpu/execute.v project/cpu/fetch.v project/cpu/memory.v project/cpu/register_bank.v project/cpu/writeback.v project/peripheral/buttons.v project/peripheral/peripheral_manager.v project/peripheral/pwm_port.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("arRISCado") {
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
                                dir("arRISCado") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p arRISCado -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("arRISCado") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p arRISCado -b digilent_arty_a7_100t -l'
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
