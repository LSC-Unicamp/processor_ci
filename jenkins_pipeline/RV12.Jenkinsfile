
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf RV12'
                sh 'git clone --recursive --depth=1 https://github.com/roalogic/RV12 RV12'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("RV12") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s riscv_core  rtl/verilog/ahb3lite/biu_ahb3lite.sv rtl/verilog/ahb3lite/riscv_top_ahb3lite.sv rtl/verilog/core/riscv_bp.sv rtl/verilog/core/riscv_core.sv rtl/verilog/core/riscv_du.sv rtl/verilog/core/riscv_dwb.sv rtl/verilog/core/riscv_ex.sv rtl/verilog/core/riscv_id.sv rtl/verilog/core/riscv_if.sv rtl/verilog/core/riscv_mem.sv rtl/verilog/core/riscv_parcel_queue.sv rtl/verilog/core/riscv_pd.sv rtl/verilog/core/riscv_rf.sv rtl/verilog/core/riscv_rsb.sv rtl/verilog/core/riscv_state1.10.sv rtl/verilog/core/riscv_state1.7.sv rtl/verilog/core/riscv_state1.9.sv rtl/verilog/core/riscv_state_20240411.sv rtl/verilog/core/riscv_wb.sv rtl/verilog/core/cache/riscv_cache_biu_ctrl.sv rtl/verilog/core/cache/riscv_cache_memory.sv rtl/verilog/core/cache/riscv_cache_setup.sv rtl/verilog/core/cache/riscv_cache_tag.sv rtl/verilog/core/cache/riscv_dcache_core.sv rtl/verilog/core/cache/riscv_dcache_fsm.sv rtl/verilog/core/cache/riscv_icache_core.sv rtl/verilog/core/cache/riscv_icache_fsm.sv rtl/verilog/core/cache/riscv_nodcache_core.sv rtl/verilog/core/cache/riscv_noicache_core.sv rtl/verilog/core/ex/riscv_alu.sv rtl/verilog/core/ex/riscv_bu.sv rtl/verilog/core/ex/riscv_div.sv rtl/verilog/core/ex/riscv_lsu.sv rtl/verilog/core/ex/riscv_mul.sv rtl/verilog/core/memory/riscv_dmem_ctrl.sv rtl/verilog/core/memory/riscv_imem_ctrl.sv rtl/verilog/core/memory/riscv_membuf.sv rtl/verilog/core/memory/riscv_memmisaligned.sv rtl/verilog/core/memory/riscv_mmu.sv rtl/verilog/core/memory/riscv_pmachk.sv rtl/verilog/core/memory/riscv_pmpchk.sv rtl/verilog/core/memory/riscv_wbuf.sv rtl/verilog/core/mmu/riscv_nommu.sv rtl/verilog/pkg/biu_constants_pkg.sv rtl/verilog/pkg/riscv_cache_pkg.sv rtl/verilog/pkg/riscv_du_pkg.sv rtl/verilog/pkg/riscv_opcodes_pkg.sv rtl/verilog/pkg/riscv_pma_pkg.sv rtl/verilog/pkg/riscv_rv12_pkg.sv rtl/verilog/pkg/riscv_state1.10_pkg.sv rtl/verilog/pkg/riscv_state1.7_pkg.sv rtl/verilog/pkg/riscv_state1.9_pkg.sv rtl/verilog/pkg/riscv_state_20240411_pkg.sv "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("RV12") {
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
                                dir("RV12") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p RV12 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("RV12") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p RV12 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("RV12") {
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
                                dir("RV12") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p RV12 -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("RV12") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p RV12 -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("RV12") {
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
