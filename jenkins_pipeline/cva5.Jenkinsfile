
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf cva5'
                sh 'git clone --recursive --depth=1 https://github.com/openhwgroup/cva5 cva5'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("cva5") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   examples/zedboard/scripts/design_1_wrapper.v core/cva5.sv core/decode_and_issue.sv core/fp_writeback.sv core/instruction_metadata_and_id_management.sv core/l1_arbiter.sv core/mmu.sv core/register_file.sv core/register_free_list.sv core/renamer.sv core/tlb_lut_ram.sv core/writeback.sv core/common_components/byte_en_bram.sv core/common_components/clz.sv core/common_components/cva5_fifo.sv core/common_components/cycler.sv core/common_components/dual_port_bram.sv core/common_components/lfsr.sv core/common_components/lutram_1w_1r.sv core/common_components/lutram_1w_mr.sv core/common_components/one_hot_to_integer.sv core/common_components/priority_encoder.sv core/common_components/set_clr_reg_with_rst.sv core/common_components/toggle_memory.sv core/common_components/toggle_memory_set.sv core/common_components/vendor_support/intel/intel_byte_enable_ram.sv core/common_components/vendor_support/xilinx/cva5_wrapper_xilinx.sv core/common_components/vendor_support/xilinx/xilinx_byte_enable_ram.sv core/execution_units/alu_unit.sv core/execution_units/barrel_shifter.sv core/execution_units/branch_comparator.sv core/execution_units/branch_unit.sv core/execution_units/csr_unit.sv core/execution_units/custom_unit.sv core/execution_units/div_core.sv core/execution_units/div_unit.sv core/execution_units/gc_unit.sv core/execution_units/mul_unit.sv core/execution_units/fp_unit/fp_add.sv core/execution_units/fp_unit/fp_div.sv core/execution_units/fp_unit/fp_div_sqrt_wrapper.sv core/execution_units/fp_unit/fp_madd_wrapper.sv core/execution_units/fp_unit/fp_mul.sv core/execution_units/fp_unit/fp_normalize_rounding_top.sv core/execution_units/fp_unit/fp_prenormalize.sv core/execution_units/fp_unit/fp_preprocessing.sv core/execution_units/fp_unit/fp_roundup.sv core/execution_units/fp_unit/fp_rs_preprocess.sv core/execution_units/fp_unit/fp_special_case_detection.sv core/execution_units/fp_unit/fp_sqrt.sv core/execution_units/fp_unit/fp_sqrt_core.sv core/execution_units/fp_unit/fp_sticky_tracking.sv core/execution_units/fp_unit/fp_wb2fp_misc.sv core/execution_units/fp_unit/fp_wb2int_misc.sv core/execution_units/fp_unit/fpu_top.sv core/execution_units/fp_unit/divider/carry_save_shift.sv core/execution_units/fp_unit/divider/fp_div_core.sv core/execution_units/fp_unit/divider/on_the_fly.sv core/execution_units/fp_unit/divider/q_lookup.sv core/execution_units/load_store_unit/addr_hash.sv core/execution_units/load_store_unit/amo_alu.sv core/execution_units/load_store_unit/dcache.sv core/execution_units/load_store_unit/dcache_tag_banks.sv core/execution_units/load_store_unit/load_store_queue.sv core/execution_units/load_store_unit/load_store_unit.sv core/execution_units/load_store_unit/store_queue.sv core/fetch_stage/branch_predictor.sv core/fetch_stage/fetch.sv core/fetch_stage/icache.sv core/fetch_stage/icache_tag_banks.sv core/fetch_stage/ras.sv core/memory_sub_units/avalon_master.sv core/memory_sub_units/axi_master.sv core/memory_sub_units/local_mem_sub_unit.sv core/memory_sub_units/wishbone_master.sv core/types_and_interfaces/csr_types.sv core/types_and_interfaces/cva5_config.sv core/types_and_interfaces/cva5_types.sv core/types_and_interfaces/external_interfaces.sv core/types_and_interfaces/fpu_types.sv core/types_and_interfaces/internal_interfaces.sv core/types_and_interfaces/opcodes.sv core/types_and_interfaces/riscv_types.sv debug_module/debug_cfg_types.sv debug_module/debug_interfaces.sv debug_module/debug_module.sv debug_module/jtag_module.sv debug_module/jtag_register.sv debug_module/jtag_registers.sv examples/litex/l1_to_wishbone.sv examples/litex/litex_wrapper.sv examples/nexys/l1_to_axi.sv examples/nexys/nexys_config.sv examples/nexys/nexys_sim.sv examples/nexys/nexys_wrapper.sv examples/zedboard/cva5_wrapper.sv formal/interfaces/axi4_basic_props.sv formal/models/cva5_fbm.sv formal/models/cva5_formal_wrapper.sv l2_arbiter/axi_to_arb.sv l2_arbiter/l2_arbiter.sv l2_arbiter/l2_config_and_types.sv l2_arbiter/l2_external_interfaces.sv l2_arbiter/l2_fifo.sv l2_arbiter/l2_interfaces.sv l2_arbiter/l2_reservation_logic.sv l2_arbiter/l2_round_robin.sv local_memory/local_mem.sv local_memory/local_memory_interface.sv test_benches/axi_mem_sim.sv test_benches/cva5_tb.sv test_benches/sim_mem.sv test_benches/sim_stats.sv test_benches/unit_test_benches/alu_unit_tb.sv test_benches/unit_test_benches/div_unit_tb.sv test_benches/unit_test_benches/mul_unit_tb.sv test_benches/verilator/cva5_sim.sv test_benches/verilator/AXI_DDR_simulation/axi_l2_test.sv"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("cva5") {
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
                                dir("cva5") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cva5 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("cva5") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cva5 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("cva5") {
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
                                dir("cva5") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cva5 -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("cva5") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cva5 -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("cva5") {
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
