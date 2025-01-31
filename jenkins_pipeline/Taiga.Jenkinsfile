
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf Taiga'
                sh 'git clone --recursive --depth=1 https://gitlab.com/sfu-rcl/Taiga Taiga'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Taiga") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s taiga  core/addr_hash.sv core/alu_unit.sv core/amo_alu.sv core/avalon_master.sv core/axi_master.sv core/axi_to_arb.sv core/barrel_shifter.sv core/binary_occupancy.sv core/branch_comparator.sv core/branch_predictor.sv core/branch_predictor_ram.sv core/branch_unit.sv core/byte_en_BRAM.sv core/clz.sv core/csr_types.sv core/csr_unit.sv core/cycler.sv core/dbram.sv core/dcache.sv core/ddata_bank.sv core/decode_and_issue.sv core/div_core.sv core/div_unit.sv core/dtag_banks.sv core/external_interfaces.sv core/fetch.sv core/gc_unit.sv core/ibram.sv core/icache.sv core/illegal_instruction_checker.sv core/instruction_metadata_and_id_management.sv core/interfaces.sv core/itag_banks.sv core/l1_arbiter.sv core/lfsr.sv core/load_queue.sv core/load_store_queue.sv core/load_store_unit.sv core/mmu.sv core/mul_unit.sv core/one_hot_occupancy.sv core/one_hot_to_integer.sv core/placer_randomizer.sv core/priority_encoder.sv core/ras.sv core/reg_inuse.sv core/register_bank.sv core/register_file.sv core/register_free_list.sv core/renamer.sv core/riscv_types.sv core/set_clr_reg_with_rst.sv core/shift_counter.sv core/store_queue.sv core/tag_bank.sv core/taiga.sv core/taiga_config.sv core/taiga_fifo.sv core/taiga_types.sv core/tlb_lut_ram.sv core/toggle_memory.sv core/toggle_memory_set.sv core/wishbone_master.sv core/writeback.sv "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Taiga") {
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
                                dir("Taiga") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p Taiga -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("Taiga") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p Taiga -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("Taiga") {
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
                                dir("Taiga") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p Taiga -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("Taiga") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p Taiga -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("Taiga") {
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
