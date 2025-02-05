
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf riscv-atom'
                sh 'git clone --recursive --depth=1 https://github.com/saursin/riscv-atom riscv-atom'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("riscv-atom") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   rtl/core/Alu.v rtl/core/AtomRV.v rtl/core/AtomRV_wb.v rtl/core/CSR_Unit.v rtl/core/Decode.v rtl/core/RVC_Aligner.v rtl/core/RVC_Decoder.v rtl/core/RegisterFile.v rtl/soc/atombones/AtomBones.v rtl/soc/hydrogensoc/HydrogenSoC.v rtl/uncore/gpio/GPIO.v rtl/uncore/gpio/GPIO_old.v rtl/uncore/gpio/IOBuf.v rtl/uncore/mem/DualPortRAM_wb.v rtl/uncore/mem/SinglePortRAM_wb.v rtl/uncore/mem/SinglePortROM_wb.v rtl/uncore/spi/SPI_core.v rtl/uncore/spi/SPI_wb.v rtl/uncore/timer/Timer_wb.v rtl/uncore/uart/FIFO_sync.v rtl/uncore/uart/UART.v rtl/uncore/uart/UART_core.v rtl/uncore/uart/simpleuart.v rtl/uncore/uart/simpleuart_wb.v rtl/uncore/wishbone/Arbiter.v rtl/uncore/wishbone/Arbiter2_wb.v rtl/uncore/wishbone/Arbiter3_wb.v rtl/uncore/wishbone/Crossbar5_wb.v rtl/uncore/wishbone/Crossbar6_wb.v rtl/uncore/wishbone/Crossbar_wb.v rtl/uncore/wishbone/Priority_encoder.v rtl/tb/HydrogenSoC_tb.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("riscv-atom") {
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
                                dir("riscv-atom") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p riscv-atom -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("riscv-atom") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p riscv-atom -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("riscv-atom") {
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
                                dir("riscv-atom") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p riscv-atom -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("riscv-atom") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p riscv-atom -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("riscv-atom") {
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
