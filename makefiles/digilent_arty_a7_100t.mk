ifndef VIVADO_PATH
	VIVADO=/eda/vivado/Vivado/2023.2/bin/vivado
else
	VIVADO=$(VIVADO_PATH)/vivado
endif


all: digilent_arty_a7_100t.bit

digilent_arty_a7_100t.bit:
	@echo "Building the Design..."
	$(VIVADO) -mode batch -nolog -nojournal -source $(BUILD_SCRIPT)

clean:
	@echo "Cleaning the build folder..."
	rm -rf build

load:
	@echo "Flashing the FPGA..."
	/eda/oss-cad-suite/bin/openFPGALoader -b arty_a7_100t digilent_arty_a7_100t.bit

run_all: digilent_arty_a7_100t.bit load