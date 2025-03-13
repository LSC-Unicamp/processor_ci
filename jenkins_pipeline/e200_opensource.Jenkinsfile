
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf e200_opensource'
                sh 'git clone --recursive --depth=1 https://github.com/SI-RISCV/e200_opensource e200_opensource'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("e200_opensource") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s e203_cpu_top -I rtl/e203/core/ rtl/e203/core/config.v rtl/e203/core/e203_biu.v rtl/e203/core/e203_clk_ctrl.v rtl/e203/core/e203_clkgate.v rtl/e203/core/e203_core.v rtl/e203/core/e203_cpu.v rtl/e203/core/e203_cpu_top.v rtl/e203/core/e203_defines.v rtl/e203/core/e203_dtcm_ctrl.v rtl/e203/core/e203_dtcm_ram.v rtl/e203/core/e203_extend_csr.v rtl/e203/core/e203_exu.v rtl/e203/core/e203_exu_alu.v rtl/e203/core/e203_exu_alu_bjp.v rtl/e203/core/e203_exu_alu_csrctrl.v rtl/e203/core/e203_exu_alu_dpath.v rtl/e203/core/e203_exu_alu_lsuagu.v rtl/e203/core/e203_exu_alu_muldiv.v rtl/e203/core/e203_exu_alu_rglr.v rtl/e203/core/e203_exu_branchslv.v rtl/e203/core/e203_exu_commit.v rtl/e203/core/e203_exu_csr.v rtl/e203/core/e203_exu_decode.v rtl/e203/core/e203_exu_disp.v rtl/e203/core/e203_exu_excp.v rtl/e203/core/e203_exu_longpwbck.v rtl/e203/core/e203_exu_oitf.v rtl/e203/core/e203_exu_regfile.v rtl/e203/core/e203_exu_wbck.v rtl/e203/core/e203_ifu.v rtl/e203/core/e203_ifu_ifetch.v rtl/e203/core/e203_ifu_ift2icb.v rtl/e203/core/e203_ifu_litebpu.v rtl/e203/core/e203_ifu_minidec.v rtl/e203/core/e203_irq_sync.v rtl/e203/core/e203_itcm_ctrl.v rtl/e203/core/e203_itcm_ram.v rtl/e203/core/e203_lsu.v rtl/e203/core/e203_lsu_ctrl.v rtl/e203/core/e203_reset_ctrl.v rtl/e203/core/e203_srams.v fpga/fpga_tb_top/fpga_tb_top.v tb/tb_top.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("e200_opensource") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o /eda/processor_ci_utils/labels.json"
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
                                dir("e200_opensource") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p e200_opensource -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("e200_opensource") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p e200_opensource -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("e200_opensource") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                    sh 'python3 /eda/processor_ci_tests/test_runner/run.py --config "/eda/processor_ci_tests/test_runner/config.json" --port /dev/ttyACM0"'
                                }
                            }
                        }
                    }
                }
                
                stage('digilent_arty_a7_100t') {
                    options {
                        lock(resource: 'digilent_arty_a7_100t')
                    }
                    stages {
                        stage('Synthesis and PnR') {
                            steps {
                                dir("e200_opensource") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p e200_opensource -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("e200_opensource") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p e200_opensource -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("e200_opensource") {
                                    sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                    sh 'python3 /eda/processor_ci_tests/test_runner/run.py --config "/eda/processor_ci_tests/test_runner/config.json" --port /dev/ttyUSB1"'
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
