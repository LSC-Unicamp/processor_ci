
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
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   fpga/artydevkit/src/clkdivider.v fpga/artydevkit/src/dummy.v fpga/hbirdkit/src/clkdivider.v fpga/hbirdkit/src/dummy.v fpga/nucleikit/src/clkdivider.v fpga/nucleikit/src/dummy.v rtl/e203/core/config.v rtl/e203/core/e203_biu.v rtl/e203/core/e203_clk_ctrl.v rtl/e203/core/e203_clkgate.v rtl/e203/core/e203_core.v rtl/e203/core/e203_cpu.v rtl/e203/core/e203_cpu_top.v rtl/e203/core/e203_defines.v rtl/e203/core/e203_dtcm_ctrl.v rtl/e203/core/e203_dtcm_ram.v rtl/e203/core/e203_extend_csr.v rtl/e203/core/e203_exu.v rtl/e203/core/e203_exu_alu.v rtl/e203/core/e203_exu_alu_bjp.v rtl/e203/core/e203_exu_alu_csrctrl.v rtl/e203/core/e203_exu_alu_dpath.v rtl/e203/core/e203_exu_alu_lsuagu.v rtl/e203/core/e203_exu_alu_muldiv.v rtl/e203/core/e203_exu_alu_rglr.v rtl/e203/core/e203_exu_branchslv.v rtl/e203/core/e203_exu_commit.v rtl/e203/core/e203_exu_csr.v rtl/e203/core/e203_exu_decode.v rtl/e203/core/e203_exu_disp.v rtl/e203/core/e203_exu_excp.v rtl/e203/core/e203_exu_longpwbck.v rtl/e203/core/e203_exu_oitf.v rtl/e203/core/e203_exu_regfile.v rtl/e203/core/e203_exu_wbck.v rtl/e203/core/e203_ifu.v rtl/e203/core/e203_ifu_ifetch.v rtl/e203/core/e203_ifu_ift2icb.v rtl/e203/core/e203_ifu_litebpu.v rtl/e203/core/e203_ifu_minidec.v rtl/e203/core/e203_irq_sync.v rtl/e203/core/e203_itcm_ctrl.v rtl/e203/core/e203_itcm_ram.v rtl/e203/core/e203_lsu.v rtl/e203/core/e203_lsu_ctrl.v rtl/e203/core/e203_reset_ctrl.v rtl/e203/core/e203_srams.v rtl/e203/debug/sirv_debug_csr.v rtl/e203/debug/sirv_debug_module.v rtl/e203/debug/sirv_debug_ram.v rtl/e203/debug/sirv_debug_rom.v rtl/e203/debug/sirv_jtag_dtm.v rtl/e203/fab/sirv_icb1to16_bus.v rtl/e203/fab/sirv_icb1to2_bus.v rtl/e203/fab/sirv_icb1to8_bus.v rtl/e203/general/sirv_1cyc_sram_ctrl.v rtl/e203/general/sirv_gnrl_bufs.v rtl/e203/general/sirv_gnrl_dffs.v rtl/e203/general/sirv_gnrl_icbs.v rtl/e203/general/sirv_gnrl_ram.v rtl/e203/general/sirv_gnrl_xchecker.v rtl/e203/general/sirv_sim_ram.v rtl/e203/general/sirv_sram_icb_ctrl.v rtl/e203/mems/sirv_mrom.v rtl/e203/mems/sirv_mrom_top.v rtl/e203/perips/i2c_master_bit_ctrl.v rtl/e203/perips/i2c_master_byte_ctrl.v rtl/e203/perips/i2c_master_defines.v rtl/e203/perips/i2c_master_top.v rtl/e203/perips/sirv_AsyncResetReg.v rtl/e203/perips/sirv_AsyncResetRegVec.v rtl/e203/perips/sirv_AsyncResetRegVec_1.v rtl/e203/perips/sirv_AsyncResetRegVec_129.v rtl/e203/perips/sirv_AsyncResetRegVec_36.v rtl/e203/perips/sirv_AsyncResetRegVec_67.v rtl/e203/perips/sirv_DeglitchShiftRegister.v rtl/e203/perips/sirv_LevelGateway.v rtl/e203/perips/sirv_ResetCatchAndSync.v rtl/e203/perips/sirv_ResetCatchAndSync_2.v rtl/e203/perips/sirv_aon.v rtl/e203/perips/sirv_aon_lclkgen_regs.v rtl/e203/perips/sirv_aon_porrst.v rtl/e203/perips/sirv_aon_top.v rtl/e203/perips/sirv_aon_wrapper.v rtl/e203/perips/sirv_clint.v rtl/e203/perips/sirv_clint_top.v rtl/e203/perips/sirv_expl_apb_slv.v rtl/e203/perips/sirv_expl_axi_slv.v rtl/e203/perips/sirv_flash_qspi.v rtl/e203/perips/sirv_flash_qspi_top.v rtl/e203/perips/sirv_gpio.v rtl/e203/perips/sirv_gpio_top.v rtl/e203/perips/sirv_hclkgen_regs.v rtl/e203/perips/sirv_jtaggpioport.v rtl/e203/perips/sirv_otp_top.v rtl/e203/perips/sirv_plic_man.v rtl/e203/perips/sirv_plic_top.v rtl/e203/perips/sirv_pmu.v rtl/e203/perips/sirv_pmu_core.v rtl/e203/perips/sirv_pwm16.v rtl/e203/perips/sirv_pwm16_core.v rtl/e203/perips/sirv_pwm16_top.v rtl/e203/perips/sirv_pwm8.v rtl/e203/perips/sirv_pwm8_core.v rtl/e203/perips/sirv_pwm8_top.v rtl/e203/perips/sirv_pwmgpioport.v rtl/e203/perips/sirv_qspi_1cs.v rtl/e203/perips/sirv_qspi_1cs_top.v rtl/e203/perips/sirv_qspi_4cs.v rtl/e203/perips/sirv_qspi_4cs_top.v rtl/e203/perips/sirv_qspi_arbiter.v rtl/e203/perips/sirv_qspi_fifo.v rtl/e203/perips/sirv_qspi_media.v rtl/e203/perips/sirv_qspi_media_1.v rtl/e203/perips/sirv_qspi_media_2.v rtl/e203/perips/sirv_qspi_physical.v rtl/e203/perips/sirv_qspi_physical_1.v rtl/e203/perips/sirv_qspi_physical_2.v rtl/e203/perips/sirv_queue.v rtl/e203/perips/sirv_queue_1.v rtl/e203/perips/sirv_repeater_6.v rtl/e203/perips/sirv_rtc.v rtl/e203/perips/sirv_spi_flashmap.v rtl/e203/perips/sirv_spigpioport.v rtl/e203/perips/sirv_spigpioport_1.v rtl/e203/perips/sirv_spigpioport_2.v rtl/e203/perips/sirv_tl_repeater_5.v rtl/e203/perips/sirv_tlfragmenter_qspi_1.v rtl/e203/perips/sirv_tlwidthwidget_qspi.v rtl/e203/perips/sirv_uart.v rtl/e203/perips/sirv_uart_top.v rtl/e203/perips/sirv_uartgpioport.v rtl/e203/perips/sirv_uartrx.v rtl/e203/perips/sirv_uarttx.v rtl/e203/perips/sirv_wdog.v rtl/e203/soc/e203_soc_top.v rtl/e203/subsys/e203_subsys_clint.v rtl/e203/subsys/e203_subsys_gfcm.v rtl/e203/subsys/e203_subsys_hclkgen.v rtl/e203/subsys/e203_subsys_hclkgen_rstsync.v rtl/e203/subsys/e203_subsys_main.v rtl/e203/subsys/e203_subsys_mems.v rtl/e203/subsys/e203_subsys_perips.v rtl/e203/subsys/e203_subsys_plic.v rtl/e203/subsys/e203_subsys_pll.v rtl/e203/subsys/e203_subsys_pllclkdiv.v rtl/e203/subsys/e203_subsys_top.v fpga/fpga_tb_top/fpga_tb_top.v tb/tb_top.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("e200_opensource") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o /jenkins/processor_ci_utils/labels.json"
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
