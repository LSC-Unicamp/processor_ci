
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf Anfield'
                sh 'git clone --recursive --depth=1 https://github.com/Kaigard/Anfield Anfield'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("Anfield") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s Balotelli -I vsrc/ vsrc/defines.v vsrc/Anfield/Balotelli/Balotelli.v vsrc/Anfield/Balotelli/ALU/Adder/CLA.v vsrc/Anfield/Balotelli/ALU/Adder/CasAdder3_2.v vsrc/Anfield/Balotelli/ALU/Adder/CasAdder4_2.v vsrc/Anfield/Balotelli/ALU/Div/Div.v vsrc/Anfield/Balotelli/ALU/Div/DivCore.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_FinL.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_FivL.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_ForL.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_SecL.v vsrc/Anfield/Balotelli/ALU/Mul/AddPP_ThiL.v vsrc/Anfield/Balotelli/ALU/Mul/GenPP.v vsrc/Anfield/Balotelli/ALU/Mul/Mul.v vsrc/Anfield/Balotelli/ALU/Mul/MulPreProcessing.v vsrc/Anfield/Balotelli/Cache/DCache.v vsrc/Anfield/Balotelli/Cache/ICache.v vsrc/Anfield/Balotelli/Controler/Ctrl.v vsrc/Anfield/Balotelli/Controler/Fwu.v vsrc/Anfield/Balotelli/Interface/AxiLiteMasterInterface.v vsrc/Anfield/Balotelli/Pipeline/Ex.v vsrc/Anfield/Balotelli/Pipeline/Ex2Mem.v vsrc/Anfield/Balotelli/Pipeline/Id.v vsrc/Anfield/Balotelli/Pipeline/Id2Ex.v vsrc/Anfield/Balotelli/Pipeline/If2Id.v vsrc/Anfield/Balotelli/Pipeline/Ifu.v vsrc/Anfield/Balotelli/Pipeline/Mem.v vsrc/Anfield/Balotelli/Pipeline/Mem2Wb.v vsrc/Anfield/Balotelli/Pipeline/Pc.v vsrc/Anfield/Balotelli/Pipeline/PrePc.v vsrc/Anfield/Balotelli/Pipeline/RegFile.v vsrc/Anfield/Balotelli/Privileged/Clint.v vsrc/Anfield/Balotelli/Privileged/CrsRegFile.v vsrc/Anfield/Balotelli/Privileged/Plic.v vsrc/Anfield/Balotelli/ShareCell/DualPortRam.v vsrc/Anfield/Balotelli/ShareCell/OneDeepthFIFO.v vsrc/Anfield/Balotelli/ShareCell/SycnFIFO.v vsrc/Anfield/Balotelli/Template/MuxKeyInternal.v vsrc/Anfield/Balotelli/Template/MuxKeyWithDefault.v vsrc/Anfield/Balotelli/Template/Reg.v vsrc/Anfield/Balotelli/Template/RegClintClear.v vsrc/Anfield/Balotelli/Template/RegWithEnClearData.v vsrc/Anfield/Balotelli/Template/RegWithEnHoldData.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("Anfield") {
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
                                dir("Anfield") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Anfield -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("Anfield") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p Anfield -b digilent_arty_a7_100t -l'
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
