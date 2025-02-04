
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf Anfield'
                sh 'git clone --recursive --depth=1 https://github.com/Kaigard/Anfield Anfield'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Anfield") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   vsrc/defines.v vsrc/Anfield/Anfield.v vsrc/Anfield/Balotelli/Balotelli.v vsrc/Anfield/Balotelli/ALU/Adder/CLA.v vsrc/Anfield/Balotelli/ALU/Adder/CasAdder3_2.v vsrc/Anfield/Balotelli/ALU/Adder/CasAdder4_2.v vsrc/Anfield/Balotelli/ALU/Div/Div.v vsrc/Anfield/Balotelli/ALU/Div/DivCore.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_FinL.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_FivL.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_ForL.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_SecL.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_ThiL.v vsrc/Anfield/Balotelli/ALU/Mul/GenPP.v vsrc/Anfield/Balotelli/ALU/Mul/Mul.v vsrc/Anfield/Balotelli/ALU/Mul/MulPreProcessing.v vsrc/Anfield/Balotelli/Cache/DCache.v vsrc/Anfield/Balotelli/Cache/ICache.v vsrc/Anfield/Balotelli/Controler/Ctrl.v vsrc/Anfield/Balotelli/Controler/Fwu.v vsrc/Anfield/Balotelli/Interface/AxiLiteMasterInterface.v vsrc/Anfield/Balotelli/Pipeline/Ex.v vsrc/Anfield/Balotelli/Pipeline/Ex2Mem.v vsrc/Anfield/Balotelli/Pipeline/Id.v vsrc/Anfield/Balotelli/Pipeline/Id2Ex.v vsrc/Anfield/Balotelli/Pipeline/If2Id.v vsrc/Anfield/Balotelli/Pipeline/Ifu.v vsrc/Anfield/Balotelli/Pipeline/Mem.v vsrc/Anfield/Balotelli/Pipeline/Mem2Wb.v vsrc/Anfield/Balotelli/Pipeline/Pc.v vsrc/Anfield/Balotelli/Pipeline/PrePc.v vsrc/Anfield/Balotelli/Pipeline/RegFile.v vsrc/Anfield/Balotelli/Privileged/Clint.v vsrc/Anfield/Balotelli/Privileged/CrsRegFile.v vsrc/Anfield/Balotelli/Privileged/Plic.v vsrc/Anfield/Balotelli/ShareCell/DualPortRam.v vsrc/Anfield/Balotelli/ShareCell/OneDeepthFIFO.v vsrc/Anfield/Balotelli/ShareCell/SycnFIFO.v vsrc/Anfield/Balotelli/Template/MuxKeyInternal.v vsrc/Anfield/Balotelli/Template/MuxKeyWithDefault.v vsrc/Anfield/Balotelli/Template/Reg.v vsrc/Anfield/Balotelli/Template/RegClintClear.v vsrc/Anfield/Balotelli/Template/RegWithEnClearData.v vsrc/Anfield/Balotelli/Template/RegWithEnHoldData.v vsrc/Anfield/BusMatrix/DataBusMatix/DataBusDecode.v vsrc/Anfield/BusMatrix/DataBusMatix/DataBusMatrix.v vsrc/Anfield/Interface/AxiLiteSlaverInterface.v vsrc/Anfield/Peripherals/Memory/Ram.v vsrc/Anfield/Peripherals/Memory/Rom.v vsrc/Anfield/Peripherals/Timer/Timer0.v vsrc/Anfield/Peripherals/Vga/GMemory.v vsrc/Anfield/Peripherals/Vga/Vga.v vsrc/Anfield/Peripherals/Vga/vga_ctrl.v vsrc/Anfield/BusMatrix/InstBusMatrix/InstBusMatrix.v"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Anfield") {
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
                                dir("Anfield") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Anfield -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("Anfield") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Anfield -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("Anfield") {
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
                                dir("Anfield") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Anfield -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("Anfield") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor_ci/config.json \
                                            -p Anfield -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("Anfield") {
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
