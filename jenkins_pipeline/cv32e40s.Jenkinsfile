
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf cv32e40s'
                sh 'git clone --recursive --depth=1 https://github.com/openhwgroup/cv32e40s cv32e40s'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("cv32e40s") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s   bhv/cv32e40s_core_log.sv bhv/cv32e40s_dbg_helper.sv bhv/cv32e40s_rvfi.sv bhv/cv32e40s_rvfi_data_obi.sv bhv/cv32e40s_rvfi_instr_obi.sv bhv/cv32e40s_rvfi_sim_trace.sv bhv/cv32e40s_sim_clock_gate.sv bhv/cv32e40s_sim_sffr.sv bhv/cv32e40s_sim_sffs.sv bhv/cv32e40s_wrapper.sv bhv/include/cv32e40s_rvfi_pkg.sv rtl/cv32e40s_alert.sv rtl/cv32e40s_alignment_buffer.sv rtl/cv32e40s_alu.sv rtl/cv32e40s_alu_b_cpop.sv rtl/cv32e40s_b_decoder.sv rtl/cv32e40s_clic_int_controller.sv rtl/cv32e40s_compressed_decoder.sv rtl/cv32e40s_controller.sv rtl/cv32e40s_controller_bypass.sv rtl/cv32e40s_controller_fsm.sv rtl/cv32e40s_core.sv rtl/cv32e40s_cs_registers.sv rtl/cv32e40s_csr.sv rtl/cv32e40s_data_obi_interface.sv rtl/cv32e40s_debug_triggers.sv rtl/cv32e40s_decoder.sv rtl/cv32e40s_div.sv rtl/cv32e40s_dummy_instr.sv rtl/cv32e40s_ex_stage.sv rtl/cv32e40s_ff_one.sv rtl/cv32e40s_i_decoder.sv rtl/cv32e40s_id_stage.sv rtl/cv32e40s_if_c_obi.sv rtl/cv32e40s_if_stage.sv rtl/cv32e40s_instr_obi_interface.sv rtl/cv32e40s_int_controller.sv rtl/cv32e40s_lfsr.sv rtl/cv32e40s_load_store_unit.sv rtl/cv32e40s_lsu_response_filter.sv rtl/cv32e40s_m_decoder.sv rtl/cv32e40s_mpu.sv rtl/cv32e40s_mult.sv rtl/cv32e40s_obi_integrity_fifo.sv rtl/cv32e40s_pc_check.sv rtl/cv32e40s_pc_target.sv rtl/cv32e40s_pma.sv rtl/cv32e40s_pmp.sv rtl/cv32e40s_popcnt.sv rtl/cv32e40s_prefetch_unit.sv rtl/cv32e40s_prefetcher.sv rtl/cv32e40s_rchk_check.sv rtl/cv32e40s_register_file.sv rtl/cv32e40s_register_file_ecc.sv rtl/cv32e40s_register_file_wrapper.sv rtl/cv32e40s_sequencer.sv rtl/cv32e40s_sleep_unit.sv rtl/cv32e40s_wb_stage.sv rtl/cv32e40s_wpt.sv rtl/cv32e40s_write_buffer.sv rtl/include/cv32e40s_pkg.sv sva/cv32e40s_alignment_buffer_sva.sv sva/cv32e40s_clic_int_controller_sva.sv sva/cv32e40s_controller_fsm_sva.sv sva/cv32e40s_core_sva.sv sva/cv32e40s_cs_registers_sva.sv sva/cv32e40s_data_obi_interface_sva.sv sva/cv32e40s_debug_triggers_sva.sv sva/cv32e40s_decoder_sva.sv sva/cv32e40s_div_sva.sv sva/cv32e40s_dummy_instr_sva.sv sva/cv32e40s_ex_stage_sva.sv sva/cv32e40s_id_stage_sva.sv sva/cv32e40s_if_stage_sva.sv sva/cv32e40s_instr_obi_interface_sva.sv sva/cv32e40s_load_store_unit_sva.sv sva/cv32e40s_lsu_response_filter_sva.sv sva/cv32e40s_mpu_sva.sv sva/cv32e40s_mult_sva.sv sva/cv32e40s_parameter_sva.sv sva/cv32e40s_pc_check_sva.sv sva/cv32e40s_prefetch_unit_sva.sv sva/cv32e40s_prefetcher_sva.sv sva/cv32e40s_register_file_sva.sv sva/cv32e40s_rvfi_sva.sv sva/cv32e40s_sequencer_sva.sv sva/cv32e40s_sleep_unit_sva.sv sva/cv32e40s_wb_stage_sva.sv sva/cv32e40s_wpt_sva.sv sva/cv32e40s_write_buffer_sva.sv "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("cv32e40s") {
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
                                dir("cv32e40s") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e40s -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("cv32e40s") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e40s -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("cv32e40s") {
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
                                dir("cv32e40s") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e40s -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("cv32e40s") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e40s -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("cv32e40s") {
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
