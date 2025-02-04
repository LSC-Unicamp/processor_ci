
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf Baby-Risco-5'
                sh 'git clone --recursive --depth=1 https://github.com/JN513/Baby-Risco-5 Baby-Risco-5'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Baby-Risco-5") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   debug/clk_divider.v debug/debug.v debug/reset.v fpga/colorlight_i9/main.v fpga/cyclone10gx/main.v fpga/de1soc/main.v fpga/digilent_arty/main.v fpga/nexys4_ddr/main.v fpga/tangnano20k/main.v fpga/tangnano20k_yosys/main.v fpga/xilinx_vc709/main.v src/core/alu.v src/core/alu_control.v src/core/control_unit.v src/core/core.v src/core/immediate_generator.v src/core/registers.v src/peripheral/leds.v src/peripheral/memory.v src/peripheral/soc.v tests/alu_test.v tests/clk_divider.v tests/core_test.v tests/fifo_test.v tests/gpio_test.v tests/immediate_generator_test.v tests/mux_test.v tests/pc_test.v tests/registers_test.v tests/reset_test.v tests/soc_test.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Baby-Risco-5") {
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
                                dir("Baby-Risco-5") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Baby-Risco-5 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("Baby-Risco-5") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Baby-Risco-5 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("Baby-Risco-5") {
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
                                dir("Baby-Risco-5") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Baby-Risco-5 -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("Baby-Risco-5") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Baby-Risco-5 -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("Baby-Risco-5") {
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
