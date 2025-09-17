
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
                    sh "iverilog -o simulation.out -g2005                  -s VexiiRiscv  VexiiRiscv.v ext/SpinalHDL/sim/yolo/adder.v ext/SpinalHDL/sim/yolo/counter.v ext/SpinalHDL/sim/yolo/rtl/TestMemIVerilog.v ext/SpinalHDL/sim/yolo/rtl/TestMemVerilator.v ext/SpinalHDL/sim/yolo/rtl/TestMemVerilatorW.v ext/SpinalHDL/tester/src/test/python/spinal/AnalogConnectionTester/PortBlackBox.v ext/SpinalHDL/tester/src/test/python/spinal/Apb3SpiDdrMasterCtrlTester/toplevel.v ext/SpinalHDL/tester/src/test/python/spinal/Axi4SharedSdramCtrlTester/Axi4SharedSdramCtrlTester_tb.v ext/SpinalHDL/tester/src/test/python/spinal/Axi4SharedSdramCtrlTester/mt48lc16m16a2.v ext/SpinalHDL/tester/src/test/python/spinal/BlackBoxTester/BlackBoxToTest.v ext/SpinalHDL/tester/src/test/python/spinal/Dummy/Dummy.v ext/SpinalHDL/tester/src/test/python/spinal/InOutTester/BlackBoxed.v ext/SpinalHDL/tester/src/test/python/spinal/InOutTester2/BlackBoxed.v ext/SpinalHDL/tester/src/test/python/spinal/InOutTester3/BlackBoxed.v ext/SpinalHDL/tester/src/test/python/spinal/Pinsec/common/PinsecTester_tb.v ext/SpinalHDL/tester/src/test/python/spinal/Pinsec/common/mt48lc16m16a2.v ext/SpinalHDL/tester/src/test/python/spinal/PllAAssertSDeassertTester/PllAAssertSDeassertTesterBB.v ext/SpinalHDL/tester/src/test/python/spinal/SdramCtrlTester/SdramCtrlTester_tb.v ext/SpinalHDL/tester/src/test/python/spinal/SdramCtrlTester/mt48lc16m16a2.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/Ddr2ModelTester/ddr2.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/Ddr3ModelTester/ddr3.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/Ddr3S7Tester/IOBUFDS.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/Ddr3S7Tester/OBUFDS.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/Ddr3S7Tester/OSERDESE2.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/Ddr3S7Tester/ddr3.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/Ddr3S7Tester/glbl.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/Ddr3S7Tester/ip.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/SdrModelTester/mt48lc16m16a2.v ext/SpinalHDL/tester/src/test/python/spinal/SdramXdr/SdrTester/mt48lc16m16a2.v ext/SpinalHDL/tester/src/test/python/spinal/TopLevel/dump.v ext/SpinalHDL/tester/src/test/resources/FormalBlackboxTest.v ext/SpinalHDL/tester/src/test/scala/spinal/demo/phy/ddr3_dfi_phy.v ext/SpinalHDL/sim/yolo/adder.vhd ext/SpinalHDL/tester/src/test/python/spinal/AnalogConnectionTester/PortBlackBox.vhd ext/SpinalHDL/tester/src/test/python/spinal/BlackBoxTester/BlackBoxToTest.vhd ext/SpinalHDL/tester/src/test/python/spinal/Dummy/Dummy.vhd ext/SpinalHDL/tester/src/test/python/spinal/InOutTester/BlackBoxed.vhd ext/SpinalHDL/tester/src/test/python/spinal/InOutTester2/BlackBoxed.vhd ext/SpinalHDL/tester/src/test/python/spinal/InOutTester3/BlackBoxed.vhd ext/SpinalHDL/tester/src/test/python/spinal/PllAAssertSDeassertTester/PllAAssertSDeassertTesterBB.vhd ext/SpinalHDL/tester/src/test/resources/AvalonVgaCtrl_tb.vhd ext/SpinalHDL/tester/src/test/resources/BundleTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/CommonTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/CoreWrapperV_tb.vhd ext/SpinalHDL/tester/src/test/resources/CoreWrapper_tb.vhd ext/SpinalHDL/tester/src/test/resources/Core_tb.vhd ext/SpinalHDL/tester/src/test/resources/DataCache_tb.vhd ext/SpinalHDL/tester/src/test/resources/FixedPointTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/GrayCounterTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/InternalClockTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/JtagAvalonDebugger_tb.vhd ext/SpinalHDL/tester/src/test/resources/LibTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/MandelbrotTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/MultiClockTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/RomTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/SerdesSerialTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/StreamTester_tb.vhd ext/SpinalHDL/tester/src/test/resources/UartCtrlUsageExample_tb.vhd ext/SpinalHDL/tester/src/test/resources/UartTesterGhdl_tb.vhd ext/SpinalHDL/tester/src/test/resources/WhenTester_tb.vhd"
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
