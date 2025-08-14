
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf VexiiRiscv'
                sh 'git clone --recursive --depth=1 https://github.com/SpinalHDL/VexiiRiscv VexiiRiscv'
            }
        }

        
        stage('Verilog Convert') {
            steps {
                dir("VexiiRiscv") {
                    sh 'sbt "Test/runMain vexiiriscv.Generate --xlen 32 --with-rvm --with-rvc --with-rva --with-rvf --with-rvd --dual-issue --max-ipc --with-btb --with-gshare --with-ras --gshare-bytes 4 --btb-sets 256 --btb-hash-width 12 --with-fetch-l1 --fetch-l1 --fetch-wishbone --with-lsu-l1 --lsu-l1 --lsu-l1-wishbone --with-lsu-bypass --without-mmu --reset-vector 0 --lsu-wishbone"'
                }
            }
        }
        

        stage('Simulation') {
            steps {
                dir("VexiiRiscv") {
                    echo "simulation not supported for mixed VHDL and Verilog files"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("VexiiRiscv") {
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
                                dir("VexiiRiscv") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p VexiiRiscv -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("VexiiRiscv") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p VexiiRiscv -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                sh 'python3 /eda/processor_ci_tests/main.py -b 115200 -s 2 -c                                /eda/processor_ci_tests/config.json --p /dev/ttyUSB1 -m rv32imafdbc -k 0x41525459 -ctm'
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
