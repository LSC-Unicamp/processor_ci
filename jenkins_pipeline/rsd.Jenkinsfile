
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf rsd'
                sh 'git clone --recursive --depth=1 https://github.com/rsd-devel/rsd rsd'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("rsd") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2012                  -s   Processor/Src/BasicMacros.sv Processor/Src/BasicTypes.sv Processor/Src/Controller.sv Processor/Src/ControllerIF.sv Processor/Src/Core.sv Processor/Src/Main.sv Processor/Src/MicroArchConf.sv Processor/Src/ResetController.sv Processor/Src/SynthesisMacros.sv Processor/Src/Cache/CacheFlushManager.sv Processor/Src/Cache/CacheFlushManagerIF.sv Processor/Src/Cache/CacheSystemIF.sv Processor/Src/Cache/CacheSystemTypes.sv Processor/Src/Cache/DCache.sv Processor/Src/Cache/DCacheIF.sv Processor/Src/Cache/ICache.sv Processor/Src/Cache/MemoryAccessController.sv Processor/Src/Debug/Debug.sv Processor/Src/Debug/DebugIF.sv Processor/Src/Debug/DebugTypes.sv Processor/Src/Debug/PerformanceCounter.sv Processor/Src/Debug/PerformanceCounterIF.sv Processor/Src/Decoder/DecodedBranchResolver.sv Processor/Src/Decoder/Decoder.sv Processor/Src/Decoder/MicroOp.sv Processor/Src/Decoder/OpFormat.sv Processor/Src/ExecUnit/BitCounter.sv Processor/Src/ExecUnit/DividerUnit.sv Processor/Src/ExecUnit/IntALU.sv Processor/Src/ExecUnit/MultiplierUnit.sv Processor/Src/ExecUnit/PipelinedRefDivider.sv Processor/Src/ExecUnit/Shifter.sv Processor/Src/FetchUnit/Bimodal.sv Processor/Src/FetchUnit/BranchPredictor.sv Processor/Src/FetchUnit/FetchUnitTypes.sv Processor/Src/FetchUnit/Gshare.sv Processor/Src/FloatingPointUnit/FP32DivSqrter.sv Processor/Src/FloatingPointUnit/FP32PipelinedAdder.sv Processor/Src/FloatingPointUnit/FP32PipelinedFMA.sv Processor/Src/FloatingPointUnit/FP32PipelinedMultiplier.sv Processor/Src/FloatingPointUnit/FP32PipelinedOther.sv Processor/Src/FloatingPointUnit/FPDivSqrtUnit.sv Processor/Src/FloatingPointUnit/FPDivSqrtUnitIF.sv Processor/Src/FloatingPointUnit/FPUTypes.sv Processor/Src/IO/IO_Unit.sv Processor/Src/IO/IO_UnitIF.sv Processor/Src/IO/IO_UnitTypes.sv Processor/Src/LoadStoreUnit/LoadQueue.sv Processor/Src/LoadStoreUnit/LoadStoreUnit.sv Processor/Src/LoadStoreUnit/LoadStoreUnitIF.sv Processor/Src/LoadStoreUnit/LoadStoreUnitTypes.sv Processor/Src/LoadStoreUnit/StoreCommitter.sv Processor/Src/LoadStoreUnit/StoreQueue.sv Processor/Src/Memory/Axi4LiteControlMemoryIF.sv Processor/Src/Memory/Axi4LiteControlRegister.sv Processor/Src/Memory/Axi4LiteControlRegisterIF.sv Processor/Src/Memory/Axi4LiteMemory.sv Processor/Src/Memory/Axi4Memory.sv Processor/Src/Memory/Axi4MemoryIF.sv Processor/Src/Memory/ControlQueue.sv Processor/Src/Memory/Memory.sv Processor/Src/Memory/MemoryLatencySimulator.sv Processor/Src/Memory/MemoryMapTypes.sv Processor/Src/Memory/MemoryReadReqQueue.sv Processor/Src/Memory/MemoryTypes.sv Processor/Src/Memory/MemoryWriteDataQueue.sv Processor/Src/MulDivUnit/MulDivUnit.sv Processor/Src/MulDivUnit/MulDivUnitIF.sv Processor/Src/Pipeline/CommitStage.sv Processor/Src/Pipeline/CommitStageIF.sv Processor/Src/Pipeline/DecodeStage.sv Processor/Src/Pipeline/DecodeStageIF.sv Processor/Src/Pipeline/DispatchStage.sv Processor/Src/Pipeline/DispatchStageIF.sv Processor/Src/Pipeline/PipelineTypes.sv Processor/Src/Pipeline/PreDecodeStage.sv Processor/Src/Pipeline/PreDecodeStageIF.sv Processor/Src/Pipeline/RenameStage.sv Processor/Src/Pipeline/RenameStageIF.sv Processor/Src/Pipeline/ScheduleStage.sv Processor/Src/Pipeline/ScheduleStageIF.sv Processor/Src/Pipeline/ComplexIntegerBackEnd/ComplexIntegerExecutionStage.sv Processor/Src/Pipeline/ComplexIntegerBackEnd/ComplexIntegerExecutionStageIF.sv Processor/Src/Pipeline/ComplexIntegerBackEnd/ComplexIntegerIssueStage.sv Processor/Src/Pipeline/ComplexIntegerBackEnd/ComplexIntegerIssueStageIF.sv Processor/Src/Pipeline/ComplexIntegerBackEnd/ComplexIntegerRegisterReadStage.sv Processor/Src/Pipeline/ComplexIntegerBackEnd/ComplexIntegerRegisterReadStageIF.sv Processor/Src/Pipeline/FPBackEnd/FPExecutionStage.sv Processor/Src/Pipeline/FPBackEnd/FPExecutionStageIF.sv Processor/Src/Pipeline/FPBackEnd/FPIssueStage.sv Processor/Src/Pipeline/FPBackEnd/FPIssueStageIF.sv Processor/Src/Pipeline/FPBackEnd/FPRegisterReadStage.sv Processor/Src/Pipeline/FPBackEnd/FPRegisterReadStageIF.sv Processor/Src/Pipeline/FetchStage/FetchStage.sv Processor/Src/Pipeline/FetchStage/FetchStageIF.sv Processor/Src/Pipeline/FetchStage/NextPCStage.sv Processor/Src/Pipeline/FetchStage/NextPCStageIF.sv Processor/Src/Pipeline/FetchStage/PC.sv Processor/Src/Pipeline/IntegerBackEnd/IntegerExecutionStage.sv Processor/Src/Pipeline/IntegerBackEnd/IntegerExecutionStageIF.sv Processor/Src/Pipeline/IntegerBackEnd/IntegerIssueStage.sv Processor/Src/Pipeline/IntegerBackEnd/IntegerIssueStageIF.sv Processor/Src/Pipeline/IntegerBackEnd/IntegerRegisterReadStage.sv Processor/Src/Pipeline/IntegerBackEnd/IntegerRegisterReadStageIF.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryAccessStage.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryAccessStageIF.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryExecutionStage.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryExecutionStageIF.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryIssueStage.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryIssueStageIF.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryRegisterReadStage.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryRegisterReadStageIF.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryTagAccessStage.sv Processor/Src/Pipeline/MemoryBackEnd/MemoryTagAccessStageIF.sv Processor/Src/Primitives/Divider.sv Processor/Src/Primitives/FlipFlop.sv Processor/Src/Primitives/FreeList.sv Processor/Src/Primitives/LRU_Counter.sv Processor/Src/Primitives/Multiplier.sv Processor/Src/Primitives/Picker.sv Processor/Src/Primitives/Queue.sv Processor/Src/Primitives/RAM.sv Processor/Src/Primitives/RAM_Synplify.sv Processor/Src/Primitives/RAM_Vivado.sv Processor/Src/Privileged/CSR_Unit.sv Processor/Src/Privileged/CSR_UnitIF.sv Processor/Src/Privileged/CSR_UnitTypes.sv Processor/Src/Privileged/InterruptController.sv Processor/Src/Recovery/RecoveryManager.sv Processor/Src/Recovery/RecoveryManagerIF.sv Processor/Src/RegisterFile/BypassController.sv Processor/Src/RegisterFile/BypassNetwork.sv Processor/Src/RegisterFile/BypassNetworkIF.sv Processor/Src/RegisterFile/BypassTypes.sv Processor/Src/RegisterFile/RegisterFile.sv Processor/Src/RegisterFile/RegisterFileIF.sv Processor/Src/RenameLogic/ActiveList.sv Processor/Src/RenameLogic/ActiveListIF.sv Processor/Src/RenameLogic/ActiveListIndexTypes.sv Processor/Src/RenameLogic/RMT.sv Processor/Src/RenameLogic/RenameLogic.sv Processor/Src/RenameLogic/RenameLogicCommitter.sv Processor/Src/RenameLogic/RenameLogicIF.sv Processor/Src/RenameLogic/RenameLogicTypes.sv Processor/Src/RenameLogic/RetirementRMT.sv Processor/Src/Scheduler/DestinationRAM.sv Processor/Src/Scheduler/IssueQueue.sv Processor/Src/Scheduler/MemoryDependencyPredictor.sv Processor/Src/Scheduler/ProducerMatrix.sv Processor/Src/Scheduler/ReadyBitTable.sv Processor/Src/Scheduler/ReplayQueue.sv Processor/Src/Scheduler/Scheduler.sv Processor/Src/Scheduler/SchedulerIF.sv Processor/Src/Scheduler/SchedulerTypes.sv Processor/Src/Scheduler/SelectLogic.sv Processor/Src/Scheduler/SourceCAM.sv Processor/Src/Scheduler/WakeupLogic.sv Processor/Src/Scheduler/WakeupPipelineRegister.sv Processor/Src/Scheduler/WakeupSelectIF.sv "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("rsd") {
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
                                dir("rsd") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p rsd -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("rsd") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p rsd -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("rsd") {
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
                                dir("rsd") {
                                    echo 'Starting synthesis for FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p rsd -b digilent_nexys4_ddr'
                                }
                            }
                        }
                        stage('Flash digilent_nexys4_ddr') {
                            steps {
                                dir("rsd") {
                                    echo 'Flashing FPGA digilent_nexys4_ddr.'
                                sh 'python3 /eda/processor-ci/main.py -c /eda/processor-ci/config.json \
                                            -p rsd -b digilent_nexys4_ddr -l'
                                }
                            }
                        }
                        stage('Test digilent_nexys4_ddr') {
                            steps {
                                echo 'Testing FPGA digilent_nexys4_ddr.'
                                dir("rsd") {
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
