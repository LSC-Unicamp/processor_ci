
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf maestro'
                sh 'git clone --recursive https://github.com/Artoriuz/maestro maestro'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("maestro") {
                    sh "ghdl -a --std=08   Project/Components/ALU.vhd Project/Components/EX_MEM_DIV.vhd Project/Components/ID_EX_DIV.vhd Project/Components/IF_ID_DIV.vhd Project/Components/MEM_WB_DIV.vhd Project/Components/adder.vhd Project/Components/controller.vhd Project/Components/datapath.vhd Project/Components/flushing_unit.vhd Project/Components/forwarding_unit.vhd Project/Components/jump_target_unit.vhd Project/Components/mux_2_1.vhd Project/Components/mux_32_1.vhd Project/Components/mux_3_1.vhd Project/Components/mux_5_1.vhd Project/Components/progmem_interface.vhd Project/Components/program_counter.vhd Project/Components/reg1b.vhd Project/Components/reg2b.vhd Project/Components/reg32b.vhd Project/Components/reg32b_falling_edge.vhd Project/Components/reg3b.vhd Project/Components/reg4b.vhd Project/Components/reg5b.vhd Project/Components/register_file.vhd "
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
                        stage('Síntese e PnR') {
                            steps {
                                dir("maestro") {
                                    echo 'Iniciando síntese para FPGA colorlight_i9.'
                                    sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json -p maestro -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("maestro") {
                                    echo 'FPGA colorlight_i9 bloqueada para flash.'
                                    sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json -p maestro -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Teste colorlight_i9') {
                            steps {
                                echo 'Testando FPGA colorlight_i9.'
                                dir("maestro") {
                                    // Insira aqui os comandos de teste necessários
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
                        stage('Síntese e PnR') {
                            steps {
                                dir("maestro") {
                                    echo 'Iniciando síntese para FPGA digilent_nexys4_ddr.'
                                    sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json -p maestro -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("maestro") {
                                    echo 'FPGA digilent_nexys4_ddr bloqueada para flash.'
                                    sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json -p maestro -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Teste digilent_nexys4_ddr') {
                            steps {
                                echo 'Testando FPGA digilent_nexys4_ddr.'
                                dir("maestro") {
                                    // Insira aqui os comandos de teste necessários
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
            dir("maestro") {
                sh 'rm -rf *'
            }
        }
    }
}
