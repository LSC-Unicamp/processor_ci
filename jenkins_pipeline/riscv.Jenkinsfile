
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf riscv'
                sh 'git clone --recursive --depth=1 https://github.com/ultraembedded/riscv riscv'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("riscv") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s riscv_core -I core/riscv/ core/riscv/riscv_alu.v core/riscv/riscv_core.v core/riscv/riscv_csr.v core/riscv/riscv_csr_regfile.v core/riscv/riscv_decode.v core/riscv/riscv_decoder.v core/riscv/riscv_defs.v core/riscv/riscv_divider.v core/riscv/riscv_exec.v core/riscv/riscv_fetch.v core/riscv/riscv_issue.v core/riscv/riscv_lsu.v core/riscv/riscv_mmu.v core/riscv/riscv_multiplier.v core/riscv/riscv_pipe_ctrl.v core/riscv/riscv_regfile.v core/riscv/riscv_trace_sim.v core/riscv/riscv_xilinx_2r1w.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("riscv") {
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
                                dir("riscv") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p riscv -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("riscv") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p riscv -b digilent_arty_a7_100t -l'
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
