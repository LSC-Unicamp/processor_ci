all: colorlight_i9.bit

colorlight_i9.bit: colorlight_i9.config
	/eda/oss-cad-suite/bin/ecppack --compress --input colorlight_i9.config  --bit colorlight_i9.bit

colorlight_i9.config: colorlight_i9.json
	/eda/oss-cad-suite/bin/nextpnr-ecp5 --json colorlight_i9.json --write colorlight_i9_pnr.json --45k \
		--lpf /eda/processor_ci/constraints/colorlight_i9.lpf --textcfg colorlight_i9.config --package CABGA381 \
		--speed 6 --lpf-allow-unconstrained

colorlight_i9.json:
	/eda/oss-cad-suite/bin/synlig -c $(BUILD_SCRIPT)

clean:
	rm -rf build

load:
	/eda/oss-cad-suite/bin/openFPGALoader -b colorlight-i9 colorlight_i9.bit

run_all: colorlight_i9.bit load