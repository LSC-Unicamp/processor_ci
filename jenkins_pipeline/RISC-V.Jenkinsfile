
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf RISC-V'
                sh 'git clone --recursive --depth=1 https://github.com/yavuz650/RISC-V RISC-V'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("RISC-V") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s core  core/ALU.v core/control_unit.v core/core.v core/core_wb.v core/csr_unit.v core/forwarding_unit.v core/hazard_detection_unit.v core/imm_decoder.v core/load_store_unit.v core/muldiv/MULDIV_ctrl.v core/muldiv/MULDIV_in.v core/muldiv/MULDIV_top.v core/muldiv/MUL_DIV_out.v core/muldiv/divider_32.v core/muldiv/multiplier_32.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("RISC-V") {
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
                                dir("RISC-V") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RISC-V -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("RISC-V") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RISC-V -b digilent_arty_a7_100t -l'
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
