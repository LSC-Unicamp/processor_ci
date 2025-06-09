
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf riscv-atom'
                sh 'git clone --recursive --depth=1 https://github.com/saursin/riscv-atom riscv-atom'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("riscv-atom") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s AtomRV_wb -I rtl/core/ -I rtl/common/ rtl/core/Alu.v rtl/core/AtomRV.v rtl/core/AtomRV_wb.v rtl/core/CSR_Unit.v rtl/core/Decode.v rtl/core/RVC_Aligner.v rtl/core/RVC_Decoder.v rtl/core/RegisterFile.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("riscv-atom") {
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
                                dir("riscv-atom") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p riscv-atom -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("riscv-atom") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p riscv-atom -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459 -ctm'
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
