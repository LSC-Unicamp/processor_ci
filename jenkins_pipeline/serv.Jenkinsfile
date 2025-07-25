
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf serv'
                sh 'git clone --recursive --depth=1 https://github.com/olofk/serv serv'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("serv") {
                    sh "iverilog -o simulation.out -g2005                  -s serv_rf_top  rtl/serv_aligner.v rtl/serv_alu.v rtl/serv_bufreg.v rtl/serv_bufreg2.v rtl/serv_compdec.v rtl/serv_csr.v rtl/serv_ctrl.v rtl/serv_decode.v rtl/serv_immdec.v rtl/serv_mem_if.v rtl/serv_rf_if.v rtl/serv_rf_ram.v rtl/serv_rf_ram_if.v rtl/serv_rf_top.v rtl/serv_state.v rtl/serv_synth_wrapper.v rtl/serv_top.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("serv") {
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
                                dir("serv") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p serv -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("serv") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p serv -b digilent_arty_a7_100t -l'
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
