
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
                    sh "ghdl -a --std=08               Project/Components/ALU.vhd Project/Components/EX_MEM_DIV.vhd Project/Components/ID_EX_DIV.vhd Project/Components/IF_ID_DIV.vhd Project/Components/MEM_WB_DIV.vhd Project/Components/adder.vhd Project/Components/controller.vhd Project/Components/datapath.vhd Project/Components/flushing_unit.vhd Project/Components/forwarding_unit.vhd Project/Components/jump_target_unit.vhd Project/Components/mux_2_1.vhd Project/Components/mux_32_1.vhd Project/Components/mux_3_1.vhd Project/Components/mux_5_1.vhd Project/Components/progmem_interface.vhd Project/Components/program_counter.vhd Project/Components/reg1b.vhd Project/Components/reg2b.vhd Project/Components/reg32b.vhd Project/Components/reg32b_falling_edge.vhd Project/Components/reg3b.vhd Project/Components/reg4b.vhd Project/Components/reg5b.vhd Project/Components/register_file.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("maestro") {
                    sh "python3 /eda/processor-ci/core/labeler_prototype.py -d \$(pwd)         -c /eda/processor-ci/config.json -o /jenkins/processor_ci_utils/labels.json"
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
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p maestro -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("maestro") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p maestro -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("maestro") {
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
                                dir("maestro") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p maestro -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("maestro") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p maestro -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("maestro") {
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
