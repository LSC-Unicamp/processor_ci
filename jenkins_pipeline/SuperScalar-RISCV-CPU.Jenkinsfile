
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf SuperScalar-RISCV-CPU'
                sh 'git clone --recursive --depth=1 https://github.com/risclite/SuperScalar-RISCV-CPU SuperScalar-RISCV-CPU'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("SuperScalar-RISCV-CPU") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   rtl/alu.v rtl/define.v rtl/define_para.v rtl/include_func.v rtl/instrbits.v rtl/instrman.v rtl/lsu.v rtl/membuf.v rtl/mprf.v rtl/mul.v rtl/predictor.v rtl/schedule.v rtl/ssrv_top.v rtl/sys_csr.v ssrv-on-scr1/fpga/DE2_115/DE2_115.v ssrv-on-scr1/fpga/pll/plll.v ssrv-on-scr1/fpga/pll/plll_bb.v ssrv-on-scr1/fpga/pll/plll_inst.v ssrv-on-scr1/fpga/ram/dualram.v ssrv-on-scr1/fpga/ram/dualram_bb.v ssrv-on-scr1/fpga/ram/dualram_inst.v ssrv-on-scr1/fpga/rtl/alu.v ssrv-on-scr1/fpga/rtl/define.v ssrv-on-scr1/fpga/rtl/define_para.v ssrv-on-scr1/fpga/rtl/include_func.v ssrv-on-scr1/fpga/rtl/instrbits.v ssrv-on-scr1/fpga/rtl/instrman.v ssrv-on-scr1/fpga/rtl/lsu.v ssrv-on-scr1/fpga/rtl/membuf.v ssrv-on-scr1/fpga/rtl/mprf.v ssrv-on-scr1/fpga/rtl/mul.v ssrv-on-scr1/fpga/rtl/predictor.v ssrv-on-scr1/fpga/rtl/schedule.v ssrv-on-scr1/fpga/rtl/ssrv_top.v ssrv-on-scr1/fpga/rtl/sys_csr.v scr1/src/core/scr1_clk_ctrl.sv scr1/src/core/scr1_core_top.sv scr1/src/core/scr1_dm.sv scr1/src/core/scr1_dmi.sv scr1/src/core/scr1_scu.sv scr1/src/core/scr1_tapc.sv scr1/src/core/scr1_tapc_shift_reg.sv scr1/src/core/scr1_tapc_synchronizer.sv scr1/src/core/primitives/scr1_cg.sv scr1/src/core/primitives/scr1_reset_cells.sv scr1/src/pipeline/scr1_ipic.sv scr1/src/pipeline/scr1_pipe_csr.sv scr1/src/pipeline/scr1_pipe_exu.sv scr1/src/pipeline/scr1_pipe_hdu.sv scr1/src/pipeline/scr1_pipe_ialu.sv scr1/src/pipeline/scr1_pipe_idu.sv scr1/src/pipeline/scr1_pipe_ifu.sv scr1/src/pipeline/scr1_pipe_lsu.sv scr1/src/pipeline/scr1_pipe_mprf.sv scr1/src/pipeline/scr1_pipe_tdu.sv scr1/src/pipeline/scr1_pipe_top.sv scr1/src/pipeline/scr1_tracelog.sv scr1/src/top/scr1_dmem_ahb.sv scr1/src/top/scr1_dmem_router.sv scr1/src/top/scr1_dp_memory.sv scr1/src/top/scr1_imem_ahb.sv scr1/src/top/scr1_imem_router.sv scr1/src/top/scr1_mem_axi.sv scr1/src/top/scr1_tcm.sv scr1/src/top/scr1_timer.sv scr1/src/top/scr1_top_ahb.sv scr1/src/top/scr1_top_axi.sv ssrv-on-scr1/fpga/rtl/ssrv_pipe_top.sv ssrv-on-scr1/fpga/scr1/core/scr1_clk_ctrl.sv ssrv-on-scr1/fpga/scr1/core/scr1_core_top.sv ssrv-on-scr1/fpga/scr1/core/scr1_dm.sv ssrv-on-scr1/fpga/scr1/core/scr1_dmi.sv ssrv-on-scr1/fpga/scr1/core/scr1_scu.sv ssrv-on-scr1/fpga/scr1/core/scr1_tapc.sv ssrv-on-scr1/fpga/scr1/core/scr1_tapc_shift_reg.sv ssrv-on-scr1/fpga/scr1/core/scr1_tapc_synchronizer.sv ssrv-on-scr1/fpga/scr1/core/primitives/scr1_cg.sv ssrv-on-scr1/fpga/scr1/core/primitives/scr1_reset_cells.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_ipic.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_csr.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_exu.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_hdu.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_ialu.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_idu.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_ifu.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_lsu.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_mprf.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_tdu.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_pipe_top.sv ssrv-on-scr1/fpga/scr1/pipeline/scr1_tracelog.sv ssrv-on-scr1/fpga/scr1/top/scr1_dmem_ahb.sv ssrv-on-scr1/fpga/scr1/top/scr1_dmem_router.sv ssrv-on-scr1/fpga/scr1/top/scr1_dp_memory.sv ssrv-on-scr1/fpga/scr1/top/scr1_imem_ahb.sv ssrv-on-scr1/fpga/scr1/top/scr1_imem_router.sv ssrv-on-scr1/fpga/scr1/top/scr1_mem_axi.sv ssrv-on-scr1/fpga/scr1/top/scr1_tcm.sv ssrv-on-scr1/fpga/scr1/top/scr1_timer.sv ssrv-on-scr1/fpga/scr1/top/scr1_top_ahb.sv ssrv-on-scr1/fpga/scr1/top/scr1_top_axi.sv ssrv-on-scr1/fpga/test/rxtx.v ssrv-on-scr1/fpga/test/ssrv_memory.v ssrv-on-scr1/sim/rtl/alu.v ssrv-on-scr1/sim/rtl/define.v ssrv-on-scr1/sim/rtl/define_para.v ssrv-on-scr1/sim/rtl/include_func.v ssrv-on-scr1/sim/rtl/instrbits.v ssrv-on-scr1/sim/rtl/instrman.v ssrv-on-scr1/sim/rtl/lsu.v ssrv-on-scr1/sim/rtl/membuf.v ssrv-on-scr1/sim/rtl/mprf.v ssrv-on-scr1/sim/rtl/mul.v ssrv-on-scr1/sim/rtl/predictor.v ssrv-on-scr1/sim/rtl/schedule.v ssrv-on-scr1/sim/rtl/ssrv_top.v ssrv-on-scr1/sim/rtl/sys_csr.v testbench/tb_ssrv.v scr1/src/tb/scr1_memory_tb_ahb.sv scr1/src/tb/scr1_memory_tb_axi.sv scr1/src/tb/scr1_top_tb_ahb.sv scr1/src/tb/scr1_top_tb_axi.sv ssrv-on-scr1/fpga/scr1/tb/scr1_memory_tb_ahb.sv ssrv-on-scr1/fpga/scr1/tb/scr1_memory_tb_axi.sv ssrv-on-scr1/fpga/scr1/tb/scr1_top_tb_ahb.sv ssrv-on-scr1/fpga/scr1/tb/scr1_top_tb_axi.sv ssrv-on-scr1/sim/rtl/ssrv_pipe_top.sv ssrv-on-scr1/sim/scr1/src/core/scr1_clk_ctrl.sv ssrv-on-scr1/sim/scr1/src/core/scr1_core_top.sv ssrv-on-scr1/sim/scr1/src/core/scr1_dm.sv ssrv-on-scr1/sim/scr1/src/core/scr1_dmi.sv ssrv-on-scr1/sim/scr1/src/core/scr1_scu.sv ssrv-on-scr1/sim/scr1/src/core/scr1_tapc.sv ssrv-on-scr1/sim/scr1/src/core/scr1_tapc_shift_reg.sv ssrv-on-scr1/sim/scr1/src/core/scr1_tapc_synchronizer.sv ssrv-on-scr1/sim/scr1/src/core/primitives/scr1_cg.sv ssrv-on-scr1/sim/scr1/src/core/primitives/scr1_reset_cells.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_ipic.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_csr.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_exu.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_hdu.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_ialu.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_idu.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_ifu.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_lsu.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_mprf.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_tdu.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_pipe_top.sv ssrv-on-scr1/sim/scr1/src/pipeline/scr1_tracelog.sv ssrv-on-scr1/sim/scr1/src/tb/scr1_memory_tb_ahb.sv ssrv-on-scr1/sim/scr1/src/tb/scr1_memory_tb_axi.sv ssrv-on-scr1/sim/scr1/src/tb/scr1_top_tb_ahb.sv ssrv-on-scr1/sim/scr1/src/tb/scr1_top_tb_axi.sv ssrv-on-scr1/sim/scr1/src/top/scr1_dmem_ahb.sv ssrv-on-scr1/sim/scr1/src/top/scr1_dmem_router.sv ssrv-on-scr1/sim/scr1/src/top/scr1_dp_memory.sv ssrv-on-scr1/sim/scr1/src/top/scr1_imem_ahb.sv ssrv-on-scr1/sim/scr1/src/top/scr1_imem_router.sv ssrv-on-scr1/sim/scr1/src/top/scr1_mem_axi.sv ssrv-on-scr1/sim/scr1/src/top/scr1_tcm.sv ssrv-on-scr1/sim/scr1/src/top/scr1_timer.sv ssrv-on-scr1/sim/scr1/src/top/scr1_top_ahb.sv ssrv-on-scr1/sim/scr1/src/top/scr1_top_axi.sv"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("SuperScalar-RISCV-CPU") {
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
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SuperScalar-RISCV-CPU -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SuperScalar-RISCV-CPU -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("SuperScalar-RISCV-CPU") {
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
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SuperScalar-RISCV-CPU -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("SuperScalar-RISCV-CPU") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p SuperScalar-RISCV-CPU -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("SuperScalar-RISCV-CPU") {
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
