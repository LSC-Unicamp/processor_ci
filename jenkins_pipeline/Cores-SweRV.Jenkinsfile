
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf Cores-SweRV'
                sh 'git clone --recursive --depth=1 https://github.com/chipsalliance/Cores-SweRV Cores-SweRV'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Cores-SweRV") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s veer -I design/include design/dmi/dmi_jtag_to_core_sync.v design/dmi/dmi_wrapper.v design/dma_ctrl.sv design/mem.sv design/pic_ctrl.sv design/veer.sv design/veer_wrapper.sv design/dbg/dbg.sv design/dec/dec.sv design/dec/dec_decode_ctl.sv design/dec/dec_gpr_ctl.sv design/dec/dec_ib_ctl.sv design/dec/dec_tlu_ctl.sv design/dec/dec_trigger.sv design/dmi/rvjtag_tap.sv design/exu/exu.sv design/exu/exu_alu_ctl.sv design/exu/exu_div_ctl.sv design/exu/exu_mul_ctl.sv design/ifu/ifu.sv design/ifu/ifu_aln_ctl.sv design/ifu/ifu_bp_ctl.sv design/ifu/ifu_compress_ctl.sv design/ifu/ifu_ic_mem.sv design/ifu/ifu_iccm_mem.sv design/ifu/ifu_ifc_ctl.sv design/ifu/ifu_mem_ctl.sv design/include/veer_types.sv design/lib/ahb_to_axi4.sv design/lib/axi4_to_ahb.sv design/lib/beh_lib.sv design/lib/mem_lib.sv design/lib/svci_to_axi4.sv design/lsu/lsu.sv design/lsu/lsu_addrcheck.sv design/lsu/lsu_bus_buffer.sv design/lsu/lsu_bus_intf.sv design/lsu/lsu_clkdomain.sv design/lsu/lsu_dccm_ctl.sv design/lsu/lsu_dccm_mem.sv design/lsu/lsu_ecc.sv design/lsu/lsu_lsc_ctl.sv design/lsu/lsu_trigger.sv "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Cores-SweRV") {
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
                                dir("Cores-SweRV") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Cores-SweRV -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("Cores-SweRV") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Cores-SweRV -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("Cores-SweRV") {
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
                                dir("Cores-SweRV") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Cores-SweRV -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("Cores-SweRV") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Cores-SweRV -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("Cores-SweRV") {
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
