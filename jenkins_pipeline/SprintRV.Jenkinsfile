
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf SprintRV'
                sh 'git clone --recursive --depth=1 https://github.com/CastoHu/SprintRV SprintRV'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("SprintRV") {
                    sh "iverilog -o simulation.out -g2005                  -s core_top -I rtl/core/include/ rtl/core/core_top.v rtl/core/ctrl/ctrl.v rtl/core/dec/id.v rtl/core/dec/id_ex.v rtl/core/exu/div.v rtl/core/exu/ex.v rtl/core/exu/ex_mem.v rtl/core/ifu/bp.v rtl/core/ifu/if_id.v rtl/core/ifu/ifu.v rtl/core/include/defines.v rtl/core/lsu/mem.v rtl/core/lsu/mem_wb.v rtl/core/wb/csr.v rtl/core/wb/gpr.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("SprintRV") {
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
                                dir("SprintRV") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p SprintRV -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("SprintRV") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p SprintRV -b digilent_arty_a7_100t -l'
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
