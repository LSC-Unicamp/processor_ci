
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf riscv'
                sh 'git clone --recursive --depth=1 https://github.com/ultraembedded/riscv riscv'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("riscv") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   core/riscv/riscv_alu.v core/riscv/riscv_core.v core/riscv/riscv_csr.v core/riscv/riscv_csr_regfile.v core/riscv/riscv_decode.v core/riscv/riscv_decoder.v core/riscv/riscv_defs.v core/riscv/riscv_divider.v core/riscv/riscv_exec.v core/riscv/riscv_fetch.v core/riscv/riscv_issue.v core/riscv/riscv_lsu.v core/riscv/riscv_mmu.v core/riscv/riscv_multiplier.v core/riscv/riscv_pipe_ctrl.v core/riscv/riscv_regfile.v core/riscv/riscv_trace_sim.v core/riscv/riscv_xilinx_2r1w.v top_cache_axi/src_v/dcache.v top_cache_axi/src_v/dcache_axi.v top_cache_axi/src_v/dcache_axi_axi.v top_cache_axi/src_v/dcache_core.v top_cache_axi/src_v/dcache_core_data_ram.v top_cache_axi/src_v/dcache_core_tag_ram.v top_cache_axi/src_v/dcache_if_pmem.v top_cache_axi/src_v/dcache_mux.v top_cache_axi/src_v/dcache_pmem_mux.v top_cache_axi/src_v/icache.v top_cache_axi/src_v/icache_data_ram.v top_cache_axi/src_v/icache_tag_ram.v top_cache_axi/src_v/riscv_top.v top_tcm_axi/src_v/dport_axi.v top_tcm_axi/src_v/dport_mux.v top_tcm_axi/src_v/riscv_tcm_top.v top_tcm_axi/src_v/tcm_mem.v top_tcm_axi/src_v/tcm_mem_pmem.v top_tcm_axi/src_v/tcm_mem_ram.v top_tcm_wrapper/dport_axi.v top_tcm_wrapper/dport_mux.v top_tcm_wrapper/riscv_tcm_wrapper.v top_tcm_wrapper/tcm_mem.v top_tcm_wrapper/tcm_mem_pmem.v top_tcm_wrapper/tcm_mem_ram.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("riscv") {
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
                                dir("riscv") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p riscv -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("riscv") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p riscv -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("riscv") {
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
                                dir("riscv") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p riscv -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("riscv") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p riscv -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("riscv") {
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
