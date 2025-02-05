
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf SparrowRV'
                sh 'git clone --recursive --depth=1 https://github.com/xiaowuzxc/SparrowRV SparrowRV'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("SparrowRV") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   rtl/W25Q128JVxIM.v rtl/config.v rtl/defines.v rtl/core/core.v rtl/core/csr.v rtl/core/div.v rtl/core/dpram.v rtl/core/idex.v rtl/core/iram.v rtl/core/regs.v rtl/core/rstc.v rtl/core/sctr.v rtl/core/trap.v rtl/jtag/full_handshake_rx.v rtl/jtag/full_handshake_tx.v rtl/jtag/jtag_dm.v rtl/jtag/jtag_driver.v rtl/jtag/jtag_top.v rtl/perips/axi4lite_2mt16s.v rtl/perips/sram.v rtl/perips/sm3/sm3_cmprss_ceil_comb.v rtl/perips/sm3/sm3_cmprss_core.v rtl/perips/sm3/sm3_core_top.v rtl/perips/sm3/sm3_expnd_core.v rtl/perips/sm3/sm3_pad_core.v rtl/perips/sysio/fpioa.v rtl/perips/sysio/gpio.v rtl/perips/sysio/spi.v rtl/perips/sysio/sysio.v rtl/perips/sysio/uart.v rtl/soc/sparrow_soc.v rtl/perips/sm3/tb/tb_sm3_core_top.sv tb/tb_core.sv"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("SparrowRV") {
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
                                dir("SparrowRV") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SparrowRV -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("SparrowRV") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SparrowRV -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("SparrowRV") {
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
                                dir("SparrowRV") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SparrowRV -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("SparrowRV") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SparrowRV -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("SparrowRV") {
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
