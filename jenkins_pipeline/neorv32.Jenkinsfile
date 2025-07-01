
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf neorv32'
                sh 'git clone --recursive --depth=1 https://github.com/stnolting/neorv32.git neorv32'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("neorv32") {
                    sh "ghdl -a --std=08               rtl/core/neorv32_package.vhd rtl/core/neorv32_cpu_icc.vhd rtl/core/neorv32_fifo.vhd rtl/core/neorv32_cpu_decompressor.vhd rtl/core/neorv32_cpu_frontend.vhd rtl/core/neorv32_cpu_control.vhd rtl/core/neorv32_cpu_counters.vhd rtl/core/neorv32_cpu_regfile.vhd rtl/core/neorv32_cpu_cp_shifter.vhd rtl/core/neorv32_cpu_cp_muldiv.vhd rtl/core/neorv32_cpu_cp_bitmanip.vhd rtl/core/neorv32_cpu_cp_fpu.vhd rtl/core/neorv32_cpu_cp_cfu.vhd rtl/core/neorv32_cpu_cp_cond.vhd rtl/core/neorv32_cpu_cp_crypto.vhd rtl/core/neorv32_cpu_alu.vhd rtl/core/neorv32_cpu_lsu.vhd rtl/core/neorv32_cpu_pmp.vhd rtl/core/neorv32_cpu.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("neorv32") {
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
                                dir("neorv32") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p neorv32 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("neorv32") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p neorv32 -b digilent_arty_a7_100t -l'
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
