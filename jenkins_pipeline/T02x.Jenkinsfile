
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf T02x'
                sh 'git clone --recursive --depth=1 https://github.com/klessydra/T02x T02x'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("T02x") {
                    sh "ghdl -a --std=08               klessydra-t0-2th/PKG_RiscV_Klessydra_thread_parameters.vhd klessydra-t0-2th/PKG_RiscV_Klessydra.vhd klessydra-t0-2th/RTL-CSR_Unit.vhd klessydra-t0-2th/RTL-Debug_Unit.vhd klessydra-t0-2th/RTL-Processing_Pipeline.vhd klessydra-t0-2th/RTL-Program_Counter_unit.vhd klessydra-t0-2th/STR-Klessydra_top.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("T02x") {
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
                                dir("T02x") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p T02x -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("T02x") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p T02x -b digilent_arty_a7_100t -l'
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
