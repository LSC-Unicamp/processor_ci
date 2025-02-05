
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf Hazard3'
                sh 'git clone --recursive --depth=1 https://github.com/Wren6991/Hazard3 Hazard3'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Hazard3") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   example_soc/fpga/fpga_icebreaker.v example_soc/fpga/fpga_orangecrab_25f.v example_soc/fpga/fpga_ulx3s.v example_soc/fpga/pll_25_40.v example_soc/fpga/pll_25_50.v example_soc/libfpga/arith/radix2_mult.v example_soc/libfpga/arith/wallace_adder.v example_soc/libfpga/arith/wallace_mult.v example_soc/libfpga/busfabric/ahbl_arbiter.v example_soc/libfpga/busfabric/ahbl_crossbar.v example_soc/libfpga/busfabric/ahbl_splitter.v example_soc/libfpga/busfabric/ahbl_to_apb.v example_soc/libfpga/busfabric/apb_splitter.v example_soc/libfpga/cdc/async_fifo.v example_soc/libfpga/cdc/gearbox.v example_soc/libfpga/cdc/gray_counter.v example_soc/libfpga/cdc/gray_decode.v example_soc/libfpga/cdc/sync_1bit.v example_soc/libfpga/common/activity_led.v example_soc/libfpga/common/blinky.v example_soc/libfpga/common/clkdiv_frac.v example_soc/libfpga/common/ddr_out.v example_soc/libfpga/common/debounce_ctr.v example_soc/libfpga/common/delay_ff.v example_soc/libfpga/common/dffe_out.v example_soc/libfpga/common/fpga_reset.v example_soc/libfpga/common/memdump.v example_soc/libfpga/common/nbit_sync.v example_soc/libfpga/common/onehot_encoder.v example_soc/libfpga/common/onehot_mux.v example_soc/libfpga/common/onehot_priority.v example_soc/libfpga/common/onehot_priority_dynamic.v example_soc/libfpga/common/popcount.v example_soc/libfpga/common/pullup_input.v example_soc/libfpga/common/reset_sync.v example_soc/libfpga/common/skid_buffer.v example_soc/libfpga/common/sync_fifo.v example_soc/libfpga/common/tristate_io.v example_soc/libfpga/mem/ahb_async_sram.v example_soc/libfpga/mem/ahb_async_sram_halfwidth.v example_soc/libfpga/mem/ahb_cache_readonly.v example_soc/libfpga/mem/ahb_cache_writeback.v example_soc/libfpga/mem/ahb_sync_sram.v example_soc/libfpga/mem/cache_mem_directmapped.v example_soc/libfpga/mem/cache_mem_set_associative.v example_soc/libfpga/mem/sram_sync.v example_soc/libfpga/mem/sram_sync_1r1w.v example_soc/libfpga/mem/behav/sram_async.v example_soc/libfpga/peris/spi/spi_mini.v example_soc/libfpga/peris/spi/spi_regs.v example_soc/libfpga/peris/spi_03h_xip/spi_03h_xip.v example_soc/libfpga/peris/spi_03h_xip/spi_03h_xip_regs.v example_soc/libfpga/peris/uart/uart_mini.v example_soc/libfpga/peris/uart/uart_regs.v example_soc/libfpga/video/dvi_clock_driver.v example_soc/libfpga/video/dvi_serialiser.v example_soc/libfpga/video/dvi_timing.v example_soc/libfpga/video/dvi_tx_parallel.v example_soc/libfpga/video/smoldvi_tmds_encode.v example_soc/libfpga/video/tmds_encode.v example_soc/soc/example_soc.v example_soc/soc/peri/hazard3_riscv_timer.v hdl/hazard3_core.v hdl/hazard3_cpu_1port.v hdl/hazard3_cpu_2port.v hdl/hazard3_csr.v hdl/hazard3_decode.v hdl/hazard3_frontend.v hdl/hazard3_instr_decompress.v hdl/hazard3_irq_ctrl.v hdl/hazard3_pmp.v hdl/hazard3_power_ctrl.v hdl/hazard3_regfile_1w2r.v hdl/hazard3_triggers.v hdl/arith/hazard3_alu.v hdl/arith/hazard3_branchcmp.v hdl/arith/hazard3_mul_fast.v hdl/arith/hazard3_muldiv_seq.v hdl/arith/hazard3_onehot_encode.v hdl/arith/hazard3_onehot_priority.v hdl/arith/hazard3_onehot_priority_dynamic.v hdl/arith/hazard3_priority_encode.v hdl/arith/hazard3_shift_barrel.v hdl/debug/cdc/hazard3_apb_async_bridge.v hdl/debug/cdc/hazard3_reset_sync.v hdl/debug/cdc/hazard3_sync_1bit.v hdl/debug/dm/hazard3_dm.v hdl/debug/dm/hazard3_sbus_to_ahb.v hdl/debug/dtm/hazard3_ecp5_jtag_dtm.v hdl/debug/dtm/hazard3_jtag_dtm.v hdl/debug/dtm/hazard3_jtag_dtm_core.v example_soc/libfpga/test/ahb_cache_readonly/tb.v example_soc/libfpga/test/ahb_cache_writeback/tb.v test/formal/bus_compliance_1port/tb.v test/formal/bus_compliance_2port/tb.v test/formal/common/ahbl_master_assertions.v test/formal/common/ahbl_slave_assumptions.v test/formal/common/sbus_assumptions.v test/formal/frontend_fetch_match/tb.v test/formal/instruction_fetch_match/tb.v test/formal/riscv-formal/riscv-formal/cores/VexRiscv/VexRiscv.v test/formal/riscv-formal/riscv-formal/insns/insn_add.v test/formal/riscv-formal/riscv-formal/insns/insn_addi.v test/formal/riscv-formal/riscv-formal/insns/insn_addiw.v test/formal/riscv-formal/riscv-formal/insns/insn_addw.v test/formal/riscv-formal/riscv-formal/insns/insn_and.v test/formal/riscv-formal/riscv-formal/insns/insn_andi.v test/formal/riscv-formal/riscv-formal/insns/insn_auipc.v test/formal/riscv-formal/riscv-formal/insns/insn_beq.v test/formal/riscv-formal/riscv-formal/insns/insn_bge.v test/formal/riscv-formal/riscv-formal/insns/insn_bgeu.v test/formal/riscv-formal/riscv-formal/insns/insn_blt.v test/formal/riscv-formal/riscv-formal/insns/insn_bltu.v test/formal/riscv-formal/riscv-formal/insns/insn_bne.v test/formal/riscv-formal/riscv-formal/insns/insn_c_add.v test/formal/riscv-formal/riscv-formal/insns/insn_c_addi.v test/formal/riscv-formal/riscv-formal/insns/insn_c_addi16sp.v test/formal/riscv-formal/riscv-formal/insns/insn_c_addi4spn.v test/formal/riscv-formal/riscv-formal/insns/insn_c_addiw.v test/formal/riscv-formal/riscv-formal/insns/insn_c_addw.v test/formal/riscv-formal/riscv-formal/insns/insn_c_and.v test/formal/riscv-formal/riscv-formal/insns/insn_c_andi.v test/formal/riscv-formal/riscv-formal/insns/insn_c_beqz.v test/formal/riscv-formal/riscv-formal/insns/insn_c_bnez.v test/formal/riscv-formal/riscv-formal/insns/insn_c_j.v test/formal/riscv-formal/riscv-formal/insns/insn_c_jal.v test/formal/riscv-formal/riscv-formal/insns/insn_c_jalr.v test/formal/riscv-formal/riscv-formal/insns/insn_c_jr.v test/formal/riscv-formal/riscv-formal/insns/insn_c_ld.v test/formal/riscv-formal/riscv-formal/insns/insn_c_ldsp.v test/formal/riscv-formal/riscv-formal/insns/insn_c_li.v test/formal/riscv-formal/riscv-formal/insns/insn_c_lui.v test/formal/riscv-formal/riscv-formal/insns/insn_c_lw.v test/formal/riscv-formal/riscv-formal/insns/insn_c_lwsp.v test/formal/riscv-formal/riscv-formal/insns/insn_c_mv.v test/formal/riscv-formal/riscv-formal/insns/insn_c_or.v test/formal/riscv-formal/riscv-formal/insns/insn_c_sd.v test/formal/riscv-formal/riscv-formal/insns/insn_c_sdsp.v test/formal/riscv-formal/riscv-formal/insns/insn_c_slli.v test/formal/riscv-formal/riscv-formal/insns/insn_c_srai.v test/formal/riscv-formal/riscv-formal/insns/insn_c_srli.v test/formal/riscv-formal/riscv-formal/insns/insn_c_sub.v test/formal/riscv-formal/riscv-formal/insns/insn_c_subw.v test/formal/riscv-formal/riscv-formal/insns/insn_c_sw.v test/formal/riscv-formal/riscv-formal/insns/insn_c_swsp.v test/formal/riscv-formal/riscv-formal/insns/insn_c_xor.v test/formal/riscv-formal/riscv-formal/insns/insn_div.v test/formal/riscv-formal/riscv-formal/insns/insn_divu.v test/formal/riscv-formal/riscv-formal/insns/insn_divuw.v test/formal/riscv-formal/riscv-formal/insns/insn_divw.v test/formal/riscv-formal/riscv-formal/insns/insn_jal.v test/formal/riscv-formal/riscv-formal/insns/insn_jalr.v test/formal/riscv-formal/riscv-formal/insns/insn_lb.v test/formal/riscv-formal/riscv-formal/insns/insn_lbu.v test/formal/riscv-formal/riscv-formal/insns/insn_ld.v test/formal/riscv-formal/riscv-formal/insns/insn_lh.v test/formal/riscv-formal/riscv-formal/insns/insn_lhu.v test/formal/riscv-formal/riscv-formal/insns/insn_lui.v test/formal/riscv-formal/riscv-formal/insns/insn_lw.v test/formal/riscv-formal/riscv-formal/insns/insn_lwu.v test/formal/riscv-formal/riscv-formal/insns/insn_mul.v test/formal/riscv-formal/riscv-formal/insns/insn_mulh.v test/formal/riscv-formal/riscv-formal/insns/insn_mulhsu.v test/formal/riscv-formal/riscv-formal/insns/insn_mulhu.v test/formal/riscv-formal/riscv-formal/insns/insn_mulw.v test/formal/riscv-formal/riscv-formal/insns/insn_or.v test/formal/riscv-formal/riscv-formal/insns/insn_ori.v test/formal/riscv-formal/riscv-formal/insns/insn_rem.v test/formal/riscv-formal/riscv-formal/insns/insn_remu.v test/formal/riscv-formal/riscv-formal/insns/insn_remuw.v test/formal/riscv-formal/riscv-formal/insns/insn_remw.v test/formal/riscv-formal/riscv-formal/insns/insn_sb.v test/formal/riscv-formal/riscv-formal/insns/insn_sd.v test/formal/riscv-formal/riscv-formal/insns/insn_sh.v test/formal/riscv-formal/riscv-formal/insns/insn_sll.v test/formal/riscv-formal/riscv-formal/insns/insn_slli.v test/formal/riscv-formal/riscv-formal/insns/insn_slliw.v test/formal/riscv-formal/riscv-formal/insns/insn_sllw.v test/formal/riscv-formal/riscv-formal/insns/insn_slt.v test/formal/riscv-formal/riscv-formal/insns/insn_slti.v test/formal/riscv-formal/riscv-formal/insns/insn_sltiu.v test/formal/riscv-formal/riscv-formal/insns/insn_sltu.v test/formal/riscv-formal/riscv-formal/insns/insn_sra.v test/formal/riscv-formal/riscv-formal/insns/insn_srai.v test/formal/riscv-formal/riscv-formal/insns/insn_sraiw.v test/formal/riscv-formal/riscv-formal/insns/insn_sraw.v test/formal/riscv-formal/riscv-formal/insns/insn_srl.v test/formal/riscv-formal/riscv-formal/insns/insn_srli.v test/formal/riscv-formal/riscv-formal/insns/insn_srliw.v test/formal/riscv-formal/riscv-formal/insns/insn_srlw.v test/formal/riscv-formal/riscv-formal/insns/insn_sub.v test/formal/riscv-formal/riscv-formal/insns/insn_subw.v test/formal/riscv-formal/riscv-formal/insns/insn_sw.v test/formal/riscv-formal/riscv-formal/insns/insn_xor.v test/formal/riscv-formal/riscv-formal/insns/insn_xori.v test/formal/riscv-formal/riscv-formal/insns/isa_rv32i.v test/formal/riscv-formal/riscv-formal/insns/isa_rv32ic.v test/formal/riscv-formal/riscv-formal/insns/isa_rv32im.v test/formal/riscv-formal/riscv-formal/insns/isa_rv32imc.v test/formal/riscv-formal/riscv-formal/insns/isa_rv64i.v test/formal/riscv-formal/riscv-formal/insns/isa_rv64ic.v test/formal/riscv-formal/riscv-formal/insns/isa_rv64im.v test/formal/riscv-formal/riscv-formal/insns/isa_rv64imc.v test/formal/riscv-formal/riscv-formal/tests/coverage/riscv_rv32i_insn.v test/formal/riscv-formal/riscv-formal/tests/coverage/riscv_rv32ic_insn.v test/formal/riscv-formal/riscv-formal/tests/coverage/riscv_rv64i_insn.v test/formal/riscv-formal/riscv-formal/tests/coverage/riscv_rv64ic_insn.v test/formal/riscv-formal/tb/hazard3_rvfi_wrapper.v test/sim/tb_cxxrtl/tb.v test/sim/tb_cxxrtl/tb_multicore.v test/formal/riscv-formal/riscv-formal/checks/rvfi_causal_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_channel.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_cover_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_csrw_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_dmem_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_hang_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_ill_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_imem_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_insn_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_liveness_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_pc_bwd_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_pc_fwd_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_reg_check.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_testbench.sv test/formal/riscv-formal/riscv-formal/checks/rvfi_unique_check.sv test/formal/riscv-formal/riscv-formal/cores/VexRiscv/dmemcheck.sv test/formal/riscv-formal/riscv-formal/cores/VexRiscv/imemcheck.sv test/formal/riscv-formal/riscv-formal/cores/VexRiscv/wrapper.sv test/formal/riscv-formal/riscv-formal/cores/picorv32/complete.sv test/formal/riscv-formal/riscv-formal/cores/picorv32/cover.sv test/formal/riscv-formal/riscv-formal/cores/picorv32/dmemcheck.sv test/formal/riscv-formal/riscv-formal/cores/picorv32/honest.sv test/formal/riscv-formal/riscv-formal/cores/picorv32/imemcheck.sv test/formal/riscv-formal/riscv-formal/cores/picorv32/wrapper.sv test/formal/riscv-formal/riscv-formal/cores/rocket/cover.sv test/formal/riscv-formal/riscv-formal/cores/rocket/coverage.sv test/formal/riscv-formal/riscv-formal/cores/rocket/muldivlen.sv test/formal/riscv-formal/riscv-formal/cores/rocket/rocketrvfi.sv test/formal/riscv-formal/riscv-formal/cores/rocket/wrapper.sv test/formal/riscv-formal/riscv-formal/cores/serv/cover.sv test/formal/riscv-formal/riscv-formal/cores/serv/sbram.sv test/formal/riscv-formal/riscv-formal/cores/serv/wrapper.sv test/formal/riscv-formal/riscv-formal/tests/coverage/coverage.sv test/formal/riscv-formal/riscv-formal/tests/semantics/top.sv"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Hazard3") {
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
                                dir("Hazard3") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Hazard3 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("Hazard3") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Hazard3 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("Hazard3") {
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
                                dir("Hazard3") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Hazard3 -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("Hazard3") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Hazard3 -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("Hazard3") {
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
