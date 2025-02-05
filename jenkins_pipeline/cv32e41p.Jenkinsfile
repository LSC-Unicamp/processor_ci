
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf cv32e41p'
                sh 'git clone --recursive --depth=1 https://github.com/openhwgroup/cv32e41p cv32e41p'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("cv32e41p") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s   bhv/cv32e41p_apu_tracer.sv bhv/cv32e41p_core_log.sv bhv/cv32e41p_sim_clock_gate.sv bhv/cv32e41p_tracer.sv bhv/cv32e41p_wrapper.sv bhv/include/cv32e41p_tracer_pkg.sv rtl/cv32e41p_aligner.sv rtl/cv32e41p_alu.sv rtl/cv32e41p_alu_div.sv rtl/cv32e41p_apu_disp.sv rtl/cv32e41p_controller.sv rtl/cv32e41p_core.sv rtl/cv32e41p_cs_registers.sv rtl/cv32e41p_ex_stage.sv rtl/cv32e41p_ff_one.sv rtl/cv32e41p_fifo.sv rtl/cv32e41p_hwloop_regs.sv rtl/cv32e41p_id_stage.sv rtl/cv32e41p_if_stage.sv rtl/cv32e41p_int_controller.sv rtl/cv32e41p_load_store_unit.sv rtl/cv32e41p_merged_decoder.sv rtl/cv32e41p_mult.sv rtl/cv32e41p_obi_interface.sv rtl/cv32e41p_popcnt.sv rtl/cv32e41p_prefetch_buffer.sv rtl/cv32e41p_prefetch_controller.sv rtl/cv32e41p_register_file_ff.sv rtl/cv32e41p_register_file_latch.sv rtl/cv32e41p_sleep_unit.sv rtl/include/cv32e41p_apu_core_pkg.sv rtl/include/cv32e41p_fpu_pkg.sv rtl/include/cv32e41p_pkg.sv sva/cv32e41p_prefetch_controller_sva.sv example_tb/core/amo_shim.sv example_tb/core/cv32e41p_fp_wrapper.sv example_tb/core/cv32e41p_random_interrupt_generator.sv example_tb/core/cv32e41p_tb_subsystem.sv example_tb/core/dp_ram.sv example_tb/core/mm_ram.sv example_tb/core/riscv_gnt_stall.sv example_tb/core/riscv_rvalid_stall.sv example_tb/core/tb_top.sv example_tb/core/include/perturbation_pkg.sv"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("cv32e41p") {
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
                                dir("cv32e41p") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e41p -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("cv32e41p") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e41p -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("cv32e41p") {
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
                                dir("cv32e41p") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e41p -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("cv32e41p") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p cv32e41p -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("cv32e41p") {
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
