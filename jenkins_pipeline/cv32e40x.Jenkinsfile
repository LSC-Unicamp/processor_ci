
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf cv32e40x'
                sh 'git clone --recursive --depth=1 https://github.com/openhwgroup/cv32e40x cv32e40x'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("cv32e40x") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s   bhv/cv32e40x_core_log.sv bhv/cv32e40x_dbg_helper.sv bhv/cv32e40x_rvfi.sv bhv/cv32e40x_rvfi_data_obi.sv bhv/cv32e40x_rvfi_instr_obi.sv bhv/cv32e40x_rvfi_sim_trace.sv bhv/cv32e40x_sim_clock_gate.sv bhv/cv32e40x_wrapper.sv bhv/include/cv32e40x_rvfi_pkg.sv rtl/cv32e40x_a_decoder.sv rtl/cv32e40x_align_check.sv rtl/cv32e40x_alignment_buffer.sv rtl/cv32e40x_alu.sv rtl/cv32e40x_alu_b_cpop.sv rtl/cv32e40x_b_decoder.sv rtl/cv32e40x_clic_int_controller.sv rtl/cv32e40x_compressed_decoder.sv rtl/cv32e40x_controller.sv rtl/cv32e40x_controller_bypass.sv rtl/cv32e40x_controller_fsm.sv rtl/cv32e40x_core.sv rtl/cv32e40x_cs_registers.sv rtl/cv32e40x_csr.sv rtl/cv32e40x_data_obi_interface.sv rtl/cv32e40x_debug_triggers.sv rtl/cv32e40x_decoder.sv rtl/cv32e40x_div.sv rtl/cv32e40x_ex_stage.sv rtl/cv32e40x_ff_one.sv rtl/cv32e40x_i_decoder.sv rtl/cv32e40x_id_stage.sv rtl/cv32e40x_if_c_obi.sv rtl/cv32e40x_if_stage.sv rtl/cv32e40x_if_xif.sv rtl/cv32e40x_instr_obi_interface.sv rtl/cv32e40x_int_controller.sv rtl/cv32e40x_load_store_unit.sv rtl/cv32e40x_lsu_response_filter.sv rtl/cv32e40x_m_decoder.sv rtl/cv32e40x_mpu.sv rtl/cv32e40x_mult.sv rtl/cv32e40x_pc_target.sv rtl/cv32e40x_pma.sv rtl/cv32e40x_popcnt.sv rtl/cv32e40x_prefetch_unit.sv rtl/cv32e40x_prefetcher.sv rtl/cv32e40x_register_file.sv rtl/cv32e40x_register_file_wrapper.sv rtl/cv32e40x_sequencer.sv rtl/cv32e40x_sleep_unit.sv rtl/cv32e40x_wb_stage.sv rtl/cv32e40x_wpt.sv rtl/cv32e40x_write_buffer.sv rtl/include/cv32e40x_pkg.sv sva/cv32e40x_alignment_buffer_sva.sv sva/cv32e40x_clic_int_controller_sva.sv sva/cv32e40x_controller_fsm_sva.sv sva/cv32e40x_core_sva.sv sva/cv32e40x_cs_registers_sva.sv sva/cv32e40x_debug_triggers_sva.sv sva/cv32e40x_decoder_sva.sv sva/cv32e40x_div_sva.sv sva/cv32e40x_ex_stage_sva.sv sva/cv32e40x_id_stage_sva.sv sva/cv32e40x_if_stage_sva.sv sva/cv32e40x_load_store_unit_sva.sv sva/cv32e40x_lsu_response_filter_sva.sv sva/cv32e40x_mpu_sva.sv sva/cv32e40x_mult_sva.sv sva/cv32e40x_parameter_sva.sv sva/cv32e40x_prefetch_unit_sva.sv sva/cv32e40x_prefetcher_sva.sv sva/cv32e40x_register_file_sva.sv sva/cv32e40x_rvfi_sva.sv sva/cv32e40x_sequencer_sva.sv sva/cv32e40x_sleep_unit_sva.sv sva/cv32e40x_wb_stage_sva.sv sva/cv32e40x_wpt_sva.sv sva/cv32e40x_write_buffer_sva.sv "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("cv32e40x") {
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
                                dir("cv32e40x") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e40x -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("cv32e40x") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e40x -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("cv32e40x") {
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
                                dir("cv32e40x") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e40x -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("cv32e40x") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e40x -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("cv32e40x") {
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
