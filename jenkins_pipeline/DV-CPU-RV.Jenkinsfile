
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf DV-CPU-RV'
                sh 'git clone --recursive --depth=1 https://github.com/devindang/dv-cpu-rv.git DV-CPU-RV'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("DV-CPU-RV") {
                    sh "iverilog -o simulation.out -g2005                  -s rv_core  core/rtl/rv_alu.v core/rtl/rv_alu_ctrl.v core/rtl/rv_branch_predict.v core/rtl/rv_branch_test.v core/rtl/rv_core.v core/rtl/rv_ctrl.v core/rtl/rv_data_mem.v core/rtl/rv_div.v core/rtl/rv_dpram.v core/rtl/rv_forward.v core/rtl/rv_hzd_detect.v core/rtl/rv_imm_gen.v core/rtl/rv_instr_mem.v core/rtl/rv_mem_map.v core/rtl/rv_mul.v core/rtl/rv_rf.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("DV-CPU-RV") {
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
                                dir("DV-CPU-RV") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p DV-CPU-RV -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("DV-CPU-RV") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p DV-CPU-RV -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459 '
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
