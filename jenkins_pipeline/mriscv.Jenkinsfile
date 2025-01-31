
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf mriscv'
                sh 'git clone --recursive --depth=1 https://github.com/onchipuis/mriscv mriscv'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("mriscv") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s mriscvcore  mriscvcore/mriscvcore.v mriscvcore/ALU/ALU.v mriscvcore/DECO_INSTR/DECO_INSTR.v mriscvcore/FSM/FSM.v mriscvcore/IRQ/IRQ.v mriscvcore/MEMORY_INTERFACE/MEMORY_INTERFACE.v mriscvcore/MULT/MULT.v mriscvcore/REG_FILE/REG_FILE.v mriscvcore/UTILITIES/UTILITY.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("mriscv") {
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
                                dir("mriscv") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p mriscv -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("mriscv") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p mriscv -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("mriscv") {
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
                                dir("mriscv") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p mriscv -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("mriscv") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p mriscv -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("mriscv") {
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
