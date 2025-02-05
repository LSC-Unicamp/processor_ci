
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf Rift2Core'
                sh 'git clone --recursive --depth=1 https://github.com/whutddk/Rift2Core Rift2Core'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Rift2Core") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   dependencies/blocks/src/main/resources/BlackBoxDelayBuffer.v dependencies/blocks/vsrc/SRLatch.v dependencies/constellation/src/main/resources/vsrc/TrafficEval.v dependencies/rocket-chip/src/main/resources/vsrc/AsyncResetReg.v dependencies/rocket-chip/src/main/resources/vsrc/ClockDivider2.v dependencies/rocket-chip/src/main/resources/vsrc/ClockDivider3.v dependencies/rocket-chip/src/main/resources/vsrc/EICG_wrapper.v dependencies/rocket-chip/src/main/resources/vsrc/RoccBlackBox.v dependencies/rocket-chip/src/main/resources/vsrc/SimDTM.v dependencies/rocket-chip/src/main/resources/vsrc/SimJTAG.v dependencies/rocket-chip/src/main/resources/vsrc/debug_rob.v dependencies/rocket-chip/src/main/resources/vsrc/plusarg_reader.v dependencies/rocket-chip/hardfloat/hardfloat/tests/resources/vsrc/emulator.v dependencies/rocket-chip/src/main/resources/vsrc/TestDriver.v tb/debugger/SimTop.v tb/verilator/SimLink.v tb/verilator/SimTop.v tb/verilator/test.v tb/verilator/mdl_test/Reservation_top.v tb/verilator/mdl_test/random_csr_req.v tb/verilator/mdl_test/random_op_rsl.v tb/verilator/mdl_test/random_wb_ack.v tb/vtb/SimJTAG.v tb/vtb/axi_full_slv_sram.v tb/vtb/debuger.v tb/vtb/gen_asymmetricFIFO.v tb/vtb/gen_bypassfifo.v tb/vtb/gen_counter.v tb/vtb/gen_csrreg.v tb/vtb/gen_dffr.v tb/vtb/gen_dffren.v tb/vtb/gen_dpdffren.v tb/vtb/gen_fifo.v tb/vtb/gen_ppbuff.v tb/vtb/gen_rsffr.v tb/vtb/gen_slffr.v tb/vtb/gen_sram.v tb/vtb/gen_suffr.v tb/vtb/gen_syn.v tb/vtb/lfsr.v tb/vtb/lzp.v tb/vtb/tl_mem.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Rift2Core") {
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
                                dir("Rift2Core") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Rift2Core -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("Rift2Core") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Rift2Core -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("Rift2Core") {
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
                                dir("Rift2Core") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Rift2Core -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("Rift2Core") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p Rift2Core -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("Rift2Core") {
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
