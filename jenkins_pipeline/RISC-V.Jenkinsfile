
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf RISC-V'
                sh 'git clone --recursive --depth=1 https://github.com/yavuz650/RISC-V RISC-V'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("RISC-V") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   core/ALU.v core/control_unit.v core/core.v core/core_wb.v core/csr_unit.v core/forwarding_unit.v core/hazard_detection_unit.v core/imm_decoder.v core/load_store_unit.v core/muldiv/MULDIV_ctrl.v core/muldiv/MULDIV_in.v core/muldiv/MULDIV_top.v core/muldiv/MUL_DIV_out.v core/muldiv/divider_32.v core/muldiv/multiplier_32.v peripherals/debug_interface_wb.v peripherals/loader_wb.v peripherals/memory_2rw_wb.v peripherals/mtime_registers_wb.v peripherals/uart_wb.v processor/barebones/barebones_wb_top.v processor/fpga_uart/fpga_top.v processor/barebones/barebones_top_tb.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("RISC-V") {
                    sh "python3 /eda/processor-ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor-ci/config.json -o /jenkins/processor_ci_utils/labels.json"
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
                                dir("RISC-V") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p RISC-V -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("RISC-V") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p RISC-V -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("RISC-V") {
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
                                dir("RISC-V") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p RISC-V -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("RISC-V") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p RISC-V -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("RISC-V") {
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
