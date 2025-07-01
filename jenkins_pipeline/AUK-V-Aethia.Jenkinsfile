
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf AUK-V-Aethia'
                sh 'git clone --recursive --depth=1 https://github.com/veeYceeY/AUK-V-Aethia AUK-V-Aethia'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("AUK-V-Aethia") {
                    sh "iverilog -o simulation.out -g2005                  -s aukv -I rtl/wishbone/ rtl/core/aukv.v rtl/core/aukv_alu.v rtl/core/aukv_csr_regfile.v rtl/core/aukv_decode.v rtl/core/aukv_execute.v rtl/core/aukv_fetch.v rtl/core/aukv_gpr_regfilie.v rtl/core/aukv_mem.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("AUK-V-Aethia") {
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
                                dir("AUK-V-Aethia") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p AUK-V-Aethia -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("AUK-V-Aethia") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p AUK-V-Aethia -b digilent_arty_a7_100t -l'
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
