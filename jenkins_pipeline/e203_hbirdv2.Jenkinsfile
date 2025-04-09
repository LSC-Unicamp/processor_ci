
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf e203_hbirdv2'
                sh 'git clone --recursive --depth=1 https://github.com/riscv-mcu/e203_hbirdv2 e203_hbirdv2'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("e203_hbirdv2") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2009                  -DDISABLE_SV_ASSERTION=1 -gsupported-assertions -s e203_cpu_top -I rtl/e203/core/ rtl/e203/core/config.v rtl/e203/core/e203_biu.v rtl/e203/core/e203_clk_ctrl.v rtl/e203/core/e203_clkgate.v rtl/e203/core/e203_core.v rtl/e203/core/e203_cpu.v rtl/e203/core/e203_cpu_top.v rtl/e203/core/e203_defines.v rtl/e203/core/e203_dtcm_ctrl.v rtl/e203/core/e203_dtcm_ram.v rtl/e203/core/e203_extend_csr.v rtl/e203/core/e203_exu.v rtl/e203/core/e203_exu_alu.v rtl/e203/core/e203_exu_alu_bjp.v rtl/e203/core/e203_exu_alu_csrctrl.v rtl/e203/core/e203_exu_alu_dpath.v rtl/e203/core/e203_exu_alu_lsuagu.v rtl/e203/core/e203_exu_alu_muldiv.v rtl/e203/core/e203_exu_alu_rglr.v rtl/e203/core/e203_exu_branchslv.v rtl/e203/core/e203_exu_commit.v rtl/e203/core/e203_exu_csr.v rtl/e203/core/e203_exu_decode.v rtl/e203/core/e203_exu_disp.v rtl/e203/core/e203_exu_excp.v rtl/e203/core/e203_exu_longpwbck.v rtl/e203/core/e203_exu_nice.v rtl/e203/core/e203_exu_oitf.v rtl/e203/core/e203_exu_regfile.v rtl/e203/core/e203_exu_wbck.v rtl/e203/core/e203_ifu.v rtl/e203/core/e203_ifu_ifetch.v rtl/e203/core/e203_ifu_ift2icb.v rtl/e203/core/e203_ifu_litebpu.v rtl/e203/core/e203_ifu_minidec.v rtl/e203/core/e203_irq_sync.v rtl/e203/core/e203_itcm_ctrl.v rtl/e203/core/e203_itcm_ram.v rtl/e203/core/e203_lsu.v rtl/e203/core/e203_lsu_ctrl.v rtl/e203/core/e203_reset_ctrl.v rtl/e203/core/e203_srams.v rtl/e203/general/sirv_1cyc_sram_ctrl.v rtl/e203/general/sirv_gnrl_bufs.v rtl/e203/general/sirv_gnrl_dffs.v rtl/e203/general/sirv_gnrl_icbs.v rtl/e203/general/sirv_gnrl_ram.v rtl/e203/general/sirv_gnrl_xchecker.v rtl/e203/general/sirv_sim_ram.v rtl/e203/general/sirv_sram_icb_ctrl.v rtl/e203/subsys/e203_subsys_clint.v rtl/e203/subsys/e203_subsys_gfcm.v rtl/e203/subsys/e203_subsys_hclkgen.v rtl/e203/subsys/e203_subsys_hclkgen_rstsync.v rtl/e203/subsys/e203_subsys_main.v rtl/e203/subsys/e203_subsys_mems.v rtl/e203/subsys/e203_subsys_nice_core.v rtl/e203/subsys/e203_subsys_perips.v rtl/e203/subsys/e203_subsys_plic.v rtl/e203/subsys/e203_subsys_pll.v rtl/e203/subsys/e203_subsys_pllclkdiv.v rtl/e203/subsys/e203_subsys_top.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("e203_hbirdv2") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config -o /jenkins/processor_ci_utils/labels"
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
                                dir("e203_hbirdv2") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p e203_hbirdv2 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("e203_hbirdv2") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p e203_hbirdv2 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyACM0 -m rv32i -k 0x434F4C4F'
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
                                dir("e203_hbirdv2") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p e203_hbirdv2 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("e203_hbirdv2") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p e203_hbirdv2 -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459'
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
