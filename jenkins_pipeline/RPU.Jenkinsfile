
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf RPU'
                sh 'git clone --recursive --depth=1 https://github.com/Domipheus/RPU RPU'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("RPU") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=08               vhdl/constants.vhd vhdl/alu_int32_div.vhd vhdl/control_unit.vhd vhdl/core.vhd vhdl/csr_unit.vhd vhdl/lint_unit.vhd vhdl/mem_controller.vhd vhdl/pc_unit.vhd vhdl/register_set.vhd vhdl/unit_alu_RV32_I.vhd vhdl/unit_decoder_RV32I.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("RPU") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config -o /jenkins/processor_ci_utils/labels"
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
                                dir("RPU") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RPU -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("RPU") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RPU -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyACM0 -m rv32i -k 0x434F4C4F'
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
                                dir("RPU") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RPU -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("RPU") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RPU -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459'
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
