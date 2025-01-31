
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf DV-CPU-RV'
                sh 'git clone --recursive --depth=1 https://github.com/devindang/dv-cpu-rv.git DV-CPU-RV'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("DV-CPU-RV") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s rv_core  core/rtl/rv_alu.v core/rtl/rv_alu_ctrl.v core/rtl/rv_branch_predict.v core/rtl/rv_branch_test.v core/rtl/rv_core.v core/rtl/rv_ctrl.v core/rtl/rv_data_mem.v core/rtl/rv_div.v core/rtl/rv_dpram.v core/rtl/rv_forward.v core/rtl/rv_hzd_detect.v core/rtl/rv_imm_gen.v core/rtl/rv_instr_mem.v core/rtl/rv_mem_map.v core/rtl/rv_mul.v core/rtl/rv_rf.v core/rtl/rv_instr_mem.v core/rtl/rv_data_mem.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("DV-CPU-RV") {
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
                                dir("DV-CPU-RV") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p DV-CPU-RV -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("DV-CPU-RV") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p DV-CPU-RV -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("DV-CPU-RV") {
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
                                dir("DV-CPU-RV") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p DV-CPU-RV -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("DV-CPU-RV") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p DV-CPU-RV -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("DV-CPU-RV") {
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
