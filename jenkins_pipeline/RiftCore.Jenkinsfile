
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf RiftCore'
                sh 'git clone --recursive --depth=1 https://github.com/whutddk/RiftCore RiftCore'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("RiftCore") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s riftChip -I RiftChip RiftChip/riftChip.v RiftChip/axi/axi_full_mst.v RiftChip/axi/axi_full_slv.v RiftChip/axi/axi_lite_mst.v RiftChip/axi/axi_lite_slv.v RiftChip/axi/AXI BUS TEMPLE/axi4_full_master.v RiftChip/axi/AXI BUS TEMPLE/axi4_full_slave.v RiftChip/axi/AXI BUS TEMPLE/axi4_lite_master.v RiftChip/axi/AXI BUS TEMPLE/axi4_lite_slave.v RiftChip/debug/DM.v RiftChip/debug/DMI.v RiftChip/debug/DTM.v RiftChip/debug/core_monitor.v RiftChip/element/gen_asymmetricFIFO.v RiftChip/element/gen_bypassfifo.v RiftChip/element/gen_counter.v RiftChip/element/gen_csrreg.v RiftChip/element/gen_dffr.v RiftChip/element/gen_dffren.v RiftChip/element/gen_dpdffren.v RiftChip/element/gen_fifo.v RiftChip/element/gen_ppbuff.v RiftChip/element/gen_ringStack.v RiftChip/element/gen_rsffr.v RiftChip/element/gen_slffr.v RiftChip/element/gen_sram.v RiftChip/element/gen_suffr.v RiftChip/element/gen_syn.v RiftChip/element/lfsr.v RiftChip/element/lzp.v RiftChip/riftCore/backEnd.v RiftChip/riftCore/frontEnd.v RiftChip/riftCore/instr_fifo.v RiftChip/riftCore/riftCore.v RiftChip/riftCore/backend/commit.v RiftChip/riftCore/backend/csrFiles.v RiftChip/riftCore/backend/dispatch.v RiftChip/riftCore/backend/phyRegister.v RiftChip/riftCore/backend/regFiles.v RiftChip/riftCore/backend/rename.v RiftChip/riftCore/backend/writeBack.v RiftChip/riftCore/backend/execute/alu.v RiftChip/riftCore/backend/execute/bru.v RiftChip/riftCore/backend/execute/csr.v RiftChip/riftCore/backend/execute/lsu.v RiftChip/riftCore/backend/execute/mul.v RiftChip/riftCore/backend/issue/alu_issue.v RiftChip/riftCore/backend/issue/bru_issue.v RiftChip/riftCore/backend/issue/csr_issue.v RiftChip/riftCore/backend/issue/issue_buffer.v RiftChip/riftCore/backend/issue/issue_fifo.v RiftChip/riftCore/backend/issue/lsu_issue.v RiftChip/riftCore/backend/issue/mul_issue.v RiftChip/riftCore/cache/L2cache.v RiftChip/riftCore/cache/L3cache.v RiftChip/riftCore/cache/cache.v RiftChip/riftCore/cache/cache_mem.v RiftChip/riftCore/cache/dirty_block.v RiftChip/riftCore/cache/wt_block.v RiftChip/riftCore/frontend/branch_predict.v RiftChip/riftCore/frontend/decoder.v RiftChip/riftCore/frontend/decoder16.v RiftChip/riftCore/frontend/decoder32.v RiftChip/riftCore/frontend/iAlign.v RiftChip/riftCore/frontend/icache.v RiftChip/riftCore/frontend/iqueue.v RiftChip/riftCore/frontend/pcGenerate.v RiftChip/riftCore/frontend/preDecode.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("RiftCore") {
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
                                dir("RiftCore") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RiftCore -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("RiftCore") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RiftCore -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("RiftCore") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                    sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                    /eda/processor_ci_tests/config.json --p /dev/ttyACM0 -m rv32i -k 0x434F4C4F'
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
                                dir("RiftCore") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RiftCore -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("RiftCore") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p RiftCore -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("RiftCore") {
                                    sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                    sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                    /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459'
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
            junit '**/*.xml'
        }
    }
}
