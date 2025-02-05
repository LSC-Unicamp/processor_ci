
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf NutShell'
                sh 'git clone --recursive --depth=1 https://github.com/OSCPU/NutShell NutShell'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("NutShell") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   fpga/board/PXIe/rtl/addr_mapper.v fpga/board/PXIe/rtl/system_top.v fpga/board/axu3cg/rtl/addr_mapper.v fpga/board/axu3cg/rtl/system_top.v fpga/board/axu3cg/rtl/hdmi/i2c_config.v fpga/board/axu3cg/rtl/hdmi/i2c_master_bit_ctrl.v fpga/board/axu3cg/rtl/hdmi/i2c_master_byte_ctrl.v fpga/board/axu3cg/rtl/hdmi/i2c_master_defines.v fpga/board/axu3cg/rtl/hdmi/i2c_master_top.v fpga/board/axu3cg/rtl/hdmi/timescale.v difftest/src/test/vsrc/common/SimJTAG.v difftest/src/test/vsrc/common/assert.v difftest/src/test/vsrc/common/ref.v difftest/src/test/vsrc/vcs/DeferredControl.v difftest/src/test/vsrc/vcs/DifftestEndpoint.v difftest/src/test/vsrc/vcs/top.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("NutShell") {
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
                                dir("NutShell") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p NutShell -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("NutShell") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p NutShell -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("NutShell") {
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
                                dir("NutShell") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p NutShell -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("NutShell") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p NutShell -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("NutShell") {
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
