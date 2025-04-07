
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf maestro'
                sh 'git clone --recursive --depth=1 https://github.com/Artoriuz/maestro maestro'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("maestro") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=08               Project/Components/ALU.vhd Project/Components/EX_MEM_DIV.vhd Project/Components/ID_EX_DIV.vhd Project/Components/IF_ID_DIV.vhd Project/Components/MEM_WB_DIV.vhd Project/Components/adder.vhd Project/Components/controller.vhd Project/Components/datapath.vhd Project/Components/flushing_unit.vhd Project/Components/forwarding_unit.vhd Project/Components/jump_target_unit.vhd Project/Components/mux_2_1.vhd Project/Components/mux_32_1.vhd Project/Components/mux_3_1.vhd Project/Components/mux_5_1.vhd Project/Components/progmem_interface.vhd Project/Components/program_counter.vhd Project/Components/reg1b.vhd Project/Components/reg2b.vhd Project/Components/reg32b.vhd Project/Components/reg32b_falling_edge.vhd Project/Components/reg3b.vhd Project/Components/reg4b.vhd Project/Components/reg5b.vhd Project/Components/register_file.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("maestro") {
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
                                dir("maestro") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p maestro -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("maestro") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p maestro -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("maestro") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                    sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                    /eda/processor_ci_tests/config.json --p /dev/ttyACM0 -m rv32i -k 0x434F4C4F'
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
                                dir("maestro") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p maestro -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("maestro") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p maestro -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("maestro") {
                                    sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                    sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                    /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459'
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
            junit '**/*.xml'
        }
    }
}
