
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf biriscv'
                sh 'git clone --recursive --depth=1 https://github.com/ultraembedded/biriscv biriscv'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("biriscv") {
                    sh "iverilog -o simulation.out -g2005                  -s riscv_top -I src/core -I src/dcache -I src/icache src/core/biriscv_alu.v src/core/biriscv_csr.v src/core/biriscv_csr_regfile.v src/core/biriscv_decode.v src/core/biriscv_decoder.v src/core/biriscv_defs.v src/core/biriscv_divider.v src/core/biriscv_exec.v src/core/biriscv_fetch.v src/core/biriscv_frontend.v src/core/biriscv_issue.v src/core/biriscv_lsu.v src/core/biriscv_mmu.v src/core/biriscv_multiplier.v src/core/biriscv_npc.v src/core/biriscv_pipe_ctrl.v src/core/biriscv_regfile.v src/core/biriscv_trace_sim.v src/core/biriscv_xilinx_2r1w.v src/core/riscv_core.v src/dcache/dcache.v src/dcache/dcache_axi.v src/dcache/dcache_axi_axi.v src/dcache/dcache_core.v src/dcache/dcache_core_data_ram.v src/dcache/dcache_core_tag_ram.v src/dcache/dcache_if_pmem.v src/dcache/dcache_mux.v src/dcache/dcache_pmem_mux.v src/icache/icache.v src/icache/icache_data_ram.v src/icache/icache_tag_ram.v src/top/riscv_top.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("biriscv") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config -o /jenkins/processor_ci_utils/labels"
                }            
            }
        }

        stage('FPGA Build Pipeline') {
            parallel {
                
                stage('digilent_arty_a7_100t') {
                    options {
                        lock(resource: 'digilent_arty_a7_100t')
                    }
                    stages {
                        stage('Synthesis and PnR') {
                            steps {
                                dir("biriscv") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p biriscv -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("biriscv") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p biriscv -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32i -k 0x41525459 '
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
