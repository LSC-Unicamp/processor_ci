
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf tinyriscv'
                sh 'git clone --recursive https://github.com/liangkangnan/tinyriscv.git tinyriscv'
            }
        }

        stage('Simulation') {
            steps {
                dir("tinyriscv") {
                    sh "iverilog -o simulation.out -g2005  -s tinyriscv_soc_tb -I rtl/core rtl/core/clint.v rtl/core/csr_reg.v rtl/core/ctrl.v rtl/core/defines.v rtl/core/div.v rtl/core/ex.v rtl/core/id_ex.v rtl/core/id.v rtl/core/if_id.v rtl/core/pc_reg.v rtl/core/regs.v rtl/core/rib.v rtl/core/tinyriscv.v tb/tinyriscv_soc_tb.v rtl/debug/jtag_dm.v rtl/debug/jtag_driver.v rtl/debug/jtag_top.v rtl/debug/uart_debug.v rtl/perips/gpio.v rtl/perips/ram.v rtl/perips/rom.v rtl/perips/spi.v rtl/perips/timer.v rtl/perips/uart.v rtl/soc/tinyriscv_soc_top.v rtl/utils/full_handshake_rx.v rtl/utils/full_handshake_tx.v rtl/utils/gen_buf.v rtl/utils/gen_dff.v && vvp simulation.out"
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
                        stage('Síntese e PnR') {
                            steps {
                                dir("tinyriscv") {
                                    echo 'Iniciando síntese para FPGA colorlight_i9.'
                                    sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json -p tinyriscv -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("tinyriscv") {
                                    echo 'FPGA colorlight_i9 bloqueada para flash.'
                                    sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json -p tinyriscv -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Teste colorlight_i9') {
                            steps {
                                echo 'Testando FPGA colorlight_i9.'
                                dir("tinyriscv") {
                                    // Insira aqui os comandos de teste necessários
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
                        stage('Síntese e PnR') {
                            steps {
                                dir("tinyriscv") {
                                    echo 'Iniciando síntese para FPGA digilent_nexys4_ddr.'
                                    sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json -p tinyriscv -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("tinyriscv") {
                                    echo 'FPGA digilent_nexys4_ddr bloqueada para flash.'
                                    sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json -p tinyriscv -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Teste digilent_nexys4_ddr') {
                            steps {
                                echo 'Testando FPGA digilent_nexys4_ddr.'
                                dir("tinyriscv") {
                                    // Insira aqui os comandos de teste necessários
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
            dir("tinyriscv") {
                sh 'rm -rf *'
            }
        }
    }
}
