
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf *.xml'
                sh 'rm -rf neorv32'
                sh 'git clone --recursive --depth=1 https://github.com/stnolting/neorv32.git neorv32'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("neorv32") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=08               rtl/core/neorv32_application_image.vhd rtl/core/neorv32_boot_rom.vhd rtl/core/neorv32_bootloader_image.vhd rtl/core/neorv32_bus.vhd rtl/core/neorv32_cache.vhd rtl/core/neorv32_cfs.vhd rtl/core/neorv32_clockgate.vhd rtl/core/neorv32_cpu.vhd rtl/core/neorv32_cpu_alu.vhd rtl/core/neorv32_cpu_control.vhd rtl/core/neorv32_cpu_cp_bitmanip.vhd rtl/core/neorv32_cpu_cp_cfu.vhd rtl/core/neorv32_cpu_cp_cond.vhd rtl/core/neorv32_cpu_cp_crypto.vhd rtl/core/neorv32_cpu_cp_fpu.vhd rtl/core/neorv32_cpu_cp_muldiv.vhd rtl/core/neorv32_cpu_cp_shifter.vhd rtl/core/neorv32_cpu_decompressor.vhd rtl/core/neorv32_cpu_lsu.vhd rtl/core/neorv32_cpu_pmp.vhd rtl/core/neorv32_cpu_regfile.vhd rtl/core/neorv32_crc.vhd rtl/core/neorv32_debug_dm.vhd rtl/core/neorv32_debug_dtm.vhd rtl/core/neorv32_dma.vhd rtl/core/neorv32_dmem.vhd rtl/core/neorv32_fifo.vhd rtl/core/neorv32_gpio.vhd rtl/core/neorv32_gptmr.vhd rtl/core/neorv32_imem.vhd rtl/core/neorv32_mtime.vhd rtl/core/neorv32_neoled.vhd rtl/core/neorv32_onewire.vhd rtl/core/neorv32_package.vhd rtl/core/neorv32_pwm.vhd rtl/core/neorv32_sdi.vhd rtl/core/neorv32_slink.vhd rtl/core/neorv32_spi.vhd rtl/core/neorv32_sys.vhd rtl/core/neorv32_sysinfo.vhd rtl/core/neorv32_top.vhd rtl/core/neorv32_trng.vhd rtl/core/neorv32_twi.vhd rtl/core/neorv32_uart.vhd rtl/core/neorv32_wdt.vhd rtl/core/neorv32_xbus.vhd rtl/core/neorv32_xip.vhd rtl/core/neorv32_xirq.vhd "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("neorv32") {
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
                                dir("neorv32") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p neorv32 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("neorv32") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config \
                                            -p neorv32 -b digilent_arty_a7_100t -l'
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
