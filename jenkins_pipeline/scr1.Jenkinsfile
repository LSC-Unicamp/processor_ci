
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf scr1'
                sh 'git clone --recursive --depth=1 https://github.com/syntacore/scr1 scr1'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("scr1") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s scr1_core_top -I src/includes src/core/scr1_clk_ctrl.sv src/core/scr1_core_top.sv src/core/scr1_dm.sv src/core/scr1_dmi.sv src/core/scr1_scu.sv src/core/scr1_tapc.sv src/core/scr1_tapc_shift_reg.sv src/core/scr1_tapc_synchronizer.sv src/core/pipeline/scr1_ipic.sv src/core/pipeline/scr1_pipe_csr.sv src/core/pipeline/scr1_pipe_exu.sv src/core/pipeline/scr1_pipe_hdu.sv src/core/pipeline/scr1_pipe_ialu.sv src/core/pipeline/scr1_pipe_idu.sv src/core/pipeline/scr1_pipe_ifu.sv src/core/pipeline/scr1_pipe_lsu.sv src/core/pipeline/scr1_pipe_mprf.sv src/core/pipeline/scr1_pipe_tdu.sv src/core/pipeline/scr1_pipe_top.sv src/core/pipeline/scr1_tracelog.sv src/core/primitives/scr1_cg.sv src/core/primitives/scr1_reset_cells.sv "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("scr1") {
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
                                dir("scr1") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p scr1 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("scr1") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p scr1 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("scr1") {
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
                                dir("scr1") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p scr1 -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("scr1") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p scr1 -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("scr1") {
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
