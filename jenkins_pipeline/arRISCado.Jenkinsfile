
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf arRISCado'
                sh 'git clone --recursive --depth=1 https://github.com/arRISCado/arRISCado arRISCado'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("arRISCado") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   boards/nano9k/top.v boards/primer20k/top.v project/cpu.v project/flash.v project/mmu.v project/ram.v project/rom.v project/top.v project/uart.v project/cpu/alu.v project/cpu/decode.v project/cpu/divider.v project/cpu/execute.v project/cpu/fetch.v project/cpu/memory.v project/cpu/register_bank.v project/cpu/writeback.v project/peripheral/buttons.v project/peripheral/peripheral_manager.v project/peripheral/pwm_port.v testbenches/alu_tb.v testbenches/cpu_tb.v testbenches/divider_tb.v testbenches/fetch_decode_tb.v testbenches/fetch_tb.v testbenches/if_de_ex_tb.v testbenches/if_de_ex_wb_tb.v testbenches/instruction_tb.v testbenches/memory_tb.v testbenches/pwm_tb.v testbenches/ram_tb.v testbenches/rom_tb.v testbenches/writeback_tb.v testbenches/utils/imports.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("arRISCado") {
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
                                dir("arRISCado") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p arRISCado -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("arRISCado") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p arRISCado -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("arRISCado") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                }
                            }
                        }
                    }
                }
                
                stage('digilent_nexys4_ddr') {
                    options {
                        lock(resource: 'digilent_nexys4_ddr')
                    }
                    stages {
                        stage('Synthesis and PnR') {
                            steps {
                                dir("arRISCado") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p arRISCado -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("arRISCado") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p arRISCado -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("arRISCado") {
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
