
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf T03x'
                sh 'git clone --recursive --depth=1 https://github.com/klessydra/T03x T03x'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("T03x") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=08               klessydra-t0-3th/PKG_RiscV_Klessydra_thread_parameters.vhd klessydra-t0-3th/PKG_RiscV_Klessydra.vhd klessydra-t0-3th/PKG_RiscV_Klessydra.vhd klessydra-t0-3th/RTL-CSR_Unit.vhd klessydra-t0-3th/RTL-Debug_Unit.vhd klessydra-t0-3th/RTL-Processing_Pipeline.vhd klessydra-t0-3th/RTL-Program_Counter_unit.vhd klessydra-t0-3th/STR-Klessydra_top.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("T03x") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o /jenkins/processor_ci_utils/labels"
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
                                dir("T03x") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p T03x -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("T03x") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p T03x -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("T03x") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                    sh 'python3 /eda/processor_ci_tests/test_runner/run.py --config                                    /eda/processor_ci_tests/test_runner/config.json --port /dev/ttyACM0'
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
                                dir("T03x") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p T03x -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("T03x") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p T03x -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("T03x") {
                                    sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                    sh 'python3 /eda/processor_ci_tests/test_runner/run.py --config                                    /eda/processor_ci_tests/test_runner/config.json --port /dev/ttyUSB1'
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
