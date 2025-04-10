
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf T13x'
                sh 'git clone --recursive --depth=1 https://github.com/klessydra/T13x T13x'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("T13x") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=08               klessydra-t1-3th/PKG_RiscV_Klessydra.vhd klessydra-t1-3th/RTL-Accumulator.vhd klessydra-t1-3th/RTL-Debug_Unit.vhd klessydra-t1-3th/RTL-CSR_Unit.vhd klessydra-t1-3th/RTL-DSP_Unit.vhd klessydra-t1-3th/RTL-ID_STAGE.vhd klessydra-t1-3th/RTL-IE_STAGE.vhd klessydra-t1-3th/RTL-IF_STAGE.vhd klessydra-t1-3th/RTL-Load_Store_Unit.vhd klessydra-t1-3th/RTL-Processing_Pipeline.vhd klessydra-t1-3th/RTL-Program_Counter_unit.vhd klessydra-t1-3th/RTL-Registerfile.vhd klessydra-t1-3th/STR-Klessydra_top.vhd klessydra-t1-3th/RTL-Scratchpad_Memory.vhd klessydra-t1-3th/RTL-Scratchpad_Memory_Interface.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("T13x") {
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
                                dir("T13x") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p T13x -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("T13x") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p T13x -b digilent_arty_a7_100t -l'
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
