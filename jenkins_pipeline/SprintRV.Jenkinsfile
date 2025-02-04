
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf SprintRV'
                sh 'git clone --recursive --depth=1 https://github.com/CastoHu/SprintRV SprintRV'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("SprintRV") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   rtl/core/core_top.v rtl/core/ctrl/ctrl.v rtl/core/dec/id.v rtl/core/dec/id_ex.v rtl/core/exu/div.v rtl/core/exu/ex.v rtl/core/exu/ex_mem.v rtl/core/ifu/bp.v rtl/core/ifu/if_id.v rtl/core/ifu/ifu.v rtl/core/include/defines.v rtl/core/lsu/mem.v rtl/core/lsu/mem_wb.v rtl/core/wb/csr.v rtl/core/wb/gpr.v rtl/tb/bus.v rtl/tb/console.v rtl/tb/ram.v rtl/tb/simple_system.v rtl/tb/timer.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("SprintRV") {
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
                                dir("SprintRV") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p SprintRV -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("SprintRV") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p SprintRV -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("SprintRV") {
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
                                dir("SprintRV") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p SprintRV -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("SprintRV") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p SprintRV -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("SprintRV") {
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
