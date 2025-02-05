
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf simodense'
                sh 'git clone --recursive --depth=1 https://github.com/pphilippos/simodense simodense'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("simodense") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   FPGA_Implementation_AXI_peripheral/MAXI_ip.v FPGA_Implementation_AXI_peripheral/MAXI_ip_doublewidth.v FPGA_Implementation_AXI_peripheral/SAXI_ip.v FPGA_Implementation_AXI_peripheral/caches.v FPGA_Implementation_AXI_peripheral/cpu.v FPGA_Implementation_AXI_peripheral/custom.v FPGA_Implementation_AXI_peripheral/system.v Benchmarks/simple_vector_add/custom.v RTL_and_simulation/caches.v RTL_and_simulation/cpu.v RTL_and_simulation/custom.v RTL_and_simulation/system.v RTL_and_simulation/testbench.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("simodense") {
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
                                dir("simodense") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p simodense -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("simodense") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p simodense -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("simodense") {
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
                                dir("simodense") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p simodense -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("simodense") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p simodense -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("simodense") {
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
