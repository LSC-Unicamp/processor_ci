
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf RV32IC-CPU'
                sh 'git clone --recursive --depth=1 https://github.com/djzenma/RV32IC-CPU RV32IC-CPU'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("RV32IC-CPU") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   RTL/Adder.v RTL/CSRRegFile.v RTL/ClkInverter.v RTL/InterruptAddressGenerator.v RTL/Interrupt_Detector.v RTL/PIC.v RTL/RISCV.v RTL/RISCV_TOP.v RTL/RegSrcUnit.v RTL/TMRGenerator.v RTL/decompression.v RTL/memAddressSelectUnit.v RTL/ALU/ALU.v RTL/ALU/AdderSub.v RTL/ALU/Full_Adder.v RTL/ALU/RippleAdder.v RTL/Control/ALUControl.v RTL/Control/BranchUnit.v RTL/Control/ControlUnit.v RTL/Global/values.v RTL/Memory/Memory.v RTL/Other Units/ClkDiv.v RTL/Other Units/ForwardUnit.v RTL/Other Units/ImmGen.v RTL/Others/Decoder5_32.v RTL/Others/Mux2_1.v RTL/Others/Mux4_1.v RTL/Others/SSDDriver.v RTL/Others/ShiftLeft1.v RTL/Others/SignExtend.v RTL/Registers/FlipFlop.v RTL/Registers/RegFile.v RTL/Registers/RegWLoad.v RTL/Registers/regfileModel.v RTL/TestBench/clkDiv_tb.v RTL/TestBench/cpu_tb.v RTL/TestBench/mem_tb.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("RV32IC-CPU") {
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
                                dir("RV32IC-CPU") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p RV32IC-CPU -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("RV32IC-CPU") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p RV32IC-CPU -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("RV32IC-CPU") {
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
                                dir("RV32IC-CPU") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p RV32IC-CPU -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("RV32IC-CPU") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p RV32IC-CPU -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("RV32IC-CPU") {
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
