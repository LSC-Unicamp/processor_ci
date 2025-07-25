
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf F03x'
                sh 'git clone --recursive --depth=1 https://github.com/klessydra/F03x F03x'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("F03x") {
                    sh "ghdl -a --std=08               klessydra-f0-3th/PKG_RiscV_Klessydra_thread_parameters.vhd klessydra-f0-3th/PKG_RiscV_Klessydra.vhd klessydra-f0-3th/TMR_REG_PKG.vhd klessydra-f0-3th/CMP-TMR_REG.vhd klessydra-f0-3th/RTL-Processing_Pipeline_TMR.vhd klessydra-f0-3th/RTL-Program_Counter_unit_TMR.vhd klessydra-f0-3th/STR-Klessydra_top.vhd klessydra-f0-3th/RTL-CSR_Unit_TMR.vhd klessydra-f0-3th/RTL-Debug_Unit.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("F03x") {
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
                                dir("F03x") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p F03x -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("F03x") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p F03x -b digilent_arty_a7_100t -l'
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
