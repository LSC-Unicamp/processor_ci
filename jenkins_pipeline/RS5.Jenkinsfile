
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf RS5'
                sh 'git clone --recursive --depth=1 https://github.com/gaph-pucrs/RS5 RS5'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("RS5") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s RS5 -I rtl/ rtl/CSRBank.sv rtl/RS5.sv rtl/aes_unit.sv rtl/align.sv rtl/decode.sv rtl/decompresser.sv rtl/div.sv rtl/execute.sv rtl/fetch.sv rtl/mmu.sv rtl/mul.sv rtl/mulNbits.sv rtl/regbank.sv rtl/retire.sv rtl/vectorALU.sv rtl/vectorCSRs.sv rtl/vectorLSU.sv rtl/vectorRegbank.sv rtl/vectorUnit.sv rtl/aes/riscv_crypto_aes_fwd_sbox.sv rtl/aes/riscv_crypto_aes_sbox.sv rtl/aes/riscv_crypto_sbox_aes_out.sv rtl/aes/riscv_crypto_sbox_aes_top.sv rtl/aes/riscv_crypto_sbox_inv_mid.sv "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("RS5") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o /eda/processor_ci_utils/labels.json"
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
                                dir("RS5") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p RS5 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("RS5") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p RS5 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("RS5") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
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
                                dir("RS5") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p RS5 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("RS5") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p RS5 -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("RS5") {
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
