
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf Tethorax'
                sh 'git clone --recursive --depth=1 https://github.com/NikosDelijohn/Tethorax Tethorax'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Tethorax") {
                    sh "ghdl -a --std=08               PIPELINE.vhd RV32I.vhd TOOLBOX.vhd PIPELINE Components/EXE.vhd PIPELINE Components/INSTRUCTION_DECODE.vhd PIPELINE Components/INSTRUCTION_FETCH.vhd PIPELINE Components/MEMORY.vhd PIPELINE Components/PC_REGISTER.vhd PIPELINE Components/PIPE_EXE_TO_MEM_REGISTER.vhd PIPELINE Components/PIPE_ID_TO_EXE_REGISTER.vhd PIPELINE Components/PIPE_IF_TO_ID_REGISTER.vhd PIPELINE Components/PIPE_MEM_TO_WB_REGISTER.vhd PIPELINE Components/WRITE_BACK.vhd TOOLBOX Components/ADDER_2B.vhd TOOLBOX Components/ADDER_2B_MSB.vhd TOOLBOX Components/BARREL_CELL.vhd TOOLBOX Components/BARREL_SHIFTER.vhd TOOLBOX Components/CONTROL_WORD_REGROUP.vhd TOOLBOX Components/DEC5X32.vhd TOOLBOX Components/DECODE_TO_EXECUTE.vhd TOOLBOX Components/EXE_ADDER_SUBBER.vhd TOOLBOX Components/EXE_ADDER_SUBBER_CELL.vhd TOOLBOX Components/EXE_ADDER_SUBBER_CELL_MSB.vhd TOOLBOX Components/EXE_BRANCH_RESOLVE.vhd TOOLBOX Components/EXE_LOGIC_MODULE.vhd TOOLBOX Components/EXE_SLT_MODULE.vhd TOOLBOX Components/ID_ADDER.vhd TOOLBOX Components/ID_DECODER.vhd TOOLBOX Components/ID_IMM_GENERATOR.vhd TOOLBOX Components/IF_INSTRMEM.vhd TOOLBOX Components/MEM_DATAMEM.vhd TOOLBOX Components/MEM_LOADS_MASKING.vhd TOOLBOX Components/MEM_STORE_BYTEEN.vhd TOOLBOX Components/MEM_TO_WB.vhd TOOLBOX Components/MUX2X1.vhd TOOLBOX Components/MUX2X1_BIT.vhd TOOLBOX Components/MUX32X1.vhd TOOLBOX Components/MUX4X1.vhd TOOLBOX Components/MUX8X1.vhd TOOLBOX Components/PC_PLUS_4.vhd TOOLBOX Components/REGISTER_FILE.vhd TOOLBOX Components/REG_32B_CASUAL.vhd TOOLBOX Components/REG_32B_ZERO.vhd TOOLBOX Components/STALL_FWD_PREDICT.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Tethorax") {
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
                                dir("Tethorax") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Tethorax -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("Tethorax") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Tethorax -b digilent_arty_a7_100t -l'
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
