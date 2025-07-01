ifndef VIVADO_PATH
	VIVADO=/eda/vivado24/Vivado/2024.2/bin/vivado
else
	VIVADO=$(VIVADO_PATH)/vivado
endif


all: zedboard.bit

zedboard.bit:
	@echo "Building the Design..."
	$(VIVADO) -mode batch -nolog -nojournal -source $(BUILD_SCRIPT)
clean:
	@echo "Cleaning the build folder..."
	rm -rf build

# openFPGALoader funciona apenas na versão nightly, a versão estavel atual não suporta a vc709 ainda
load:
	@echo "Flashing the FPGA..."
	/eda/oss-cad-suite/bin/openFPGALoader -b zedboard zedboard.bit
#$(VIVADO_PATH)/vivado  -mode batch -nolog -nojournal -source flash.tcl

run_all: zedboard.bit load