
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf ReonV'
                sh 'git clone --recursive --depth=1 https://github.com/lcbcFoo/ReonV ReonV'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("ReonV") {
                    sh "/eda/oss-cad-suite/bin/ghdl -a --std=2005               bin/altera/altera_mf.vhd boards/altera-c5ekit/ddr3ctrl1.vhd boards/altera-c5ekit/lpddr2ctrl1.vhd boards/altera-c5ekit/syspll1.vhd boards/terasic-de4/ddr2ctrl.vhd boards/terasic-de4/uniphy_266.vhd boards/terasic-de4/uniphy_333.vhd boards/terasic-sockit/ddr3controller.vhd designs/leon3-ahbfile/ahbfile.vhd designs/leon3-ahbfile/config.vhd designs/leon3-ahbfile/leon3mp.vhd designs/leon3-altera-c5ekit/ahbrom.vhd designs/leon3-altera-c5ekit/clkgen_c5ekit.vhd designs/leon3-altera-c5ekit/config.vhd designs/leon3-altera-c5ekit/ddr3if.vhd designs/leon3-altera-c5ekit/leon3mp.vhd designs/leon3-altera-c5ekit/lpddr2if.vhd designs/leon3-altera-c5ekit/memifsim.vhd designs/leon3-altera-c5ekit/pllsim.vhd designs/leon3-altera-de2-ep2c35/apblcd.vhd designs/leon3-altera-de2-ep2c35/clkgen_de2.vhd designs/leon3-altera-de2-ep2c35/config.vhd designs/leon3-altera-de2-ep2c35/leon3mp.vhd designs/leon3-altera-de2-ep2c35/mt48lc16m16a2.vhd designs/leon3-altera-de2-ep2c35/mypackage.vhd designs/leon3-altera-de2-ep2c35/sdctrl16.vhd designs/leon3-altera-ep2s60-ddr/ahbrom.vhd designs/leon3-altera-ep2s60-ddr/config.vhd designs/leon3-altera-ep2s60-ddr/leon3mp.vhd designs/leon3-altera-ep2s60-ddr/smc_mctrl.vhd designs/leon3-altera-ep2s60-sdr/ahbrom.vhd designs/leon3-altera-ep2s60-sdr/config.vhd designs/leon3-altera-ep2s60-sdr/leon3mp.vhd designs/leon3-altera-ep2s60-sdr/smc_mctrl.vhd designs/leon3-altera-ep3c25-eek/ahbrom.vhd designs/leon3-altera-ep3c25-eek/altera_eek_clkgen.vhd designs/leon3-altera-ep3c25-eek/config.vhd designs/leon3-altera-ep3c25-eek/lcd.in.vhd designs/leon3-altera-ep3c25-eek/leon3mp.vhd designs/leon3-altera-ep3c25-eek/serializer.vhd designs/leon3-altera-ep3c25/ahbrom.vhd designs/leon3-altera-ep3c25/config.vhd designs/leon3-altera-ep3c25/leon3mp.vhd designs/leon3-altera-ep3sl150/ahbrom.vhd designs/leon3-altera-ep3sl150/config.vhd designs/leon3-altera-ep3sl150/leon3mp.vhd designs/leon3-arrow-bemicro-sdk/ahbrom.vhd designs/leon3-arrow-bemicro-sdk/config.vhd designs/leon3-arrow-bemicro-sdk/leon3mp.vhd designs/leon3-asic/bschain.vhd designs/leon3-asic/config.vhd designs/leon3-asic/core.vhd designs/leon3-asic/core_clock_mux.vhd designs/leon3-asic/leon3core.vhd designs/leon3-asic/leon3mp.vhd designs/leon3-asic/pads.vhd designs/leon3-asic/spw_lvttl_pads.vhd designs/leon3-avnet-3s1500/config.vhd designs/leon3-avnet-3s1500/leon3mp.vhd designs/leon3-avnet-3s1500/mctrl_avnet.vhd designs/leon3-avnet-eval-xc4vlx25/ahbrom.vhd designs/leon3-avnet-eval-xc4vlx25/config.vhd designs/leon3-avnet-eval-xc4vlx25/leon3mp.vhd designs/leon3-avnet-eval-xc4vlx60/ahb2mig_avnet_eval.vhd designs/leon3-avnet-eval-xc4vlx60/ahbrom.vhd designs/leon3-avnet-eval-xc4vlx60/config.vhd designs/leon3-avnet-eval-xc4vlx60/leon3mp.vhd designs/leon3-clock-gate/ahbrom.vhd designs/leon3-clock-gate/clkgate.vhd designs/leon3-clock-gate/config.vhd designs/leon3-clock-gate/leon3mp.vhd designs/leon3-digilent-anvyl/ahbrom.vhd designs/leon3-digilent-anvyl/config.vhd designs/leon3-digilent-anvyl/leon3mp.vhd designs/leon3-digilent-atlys/ahbrom.vhd designs/leon3-digilent-atlys/config.vhd designs/leon3-digilent-atlys/leon3mp.vhd designs/leon3-digilent-atlys/vga2tmds.vhd designs/leon3-digilent-atlys/vga_clkgen.vhd designs/leon3-digilent-basys3/ahbrom.vhd designs/leon3-digilent-basys3/config.vhd designs/leon3-digilent-basys3/leon3mp.vhd designs/leon3-digilent-nexys-video/ahbrom.vhd designs/leon3-digilent-nexys-video/config.vhd designs/leon3-digilent-nexys-video/leon3mp.vhd designs/leon3-digilent-nexys3/ahbrom.vhd designs/leon3-digilent-nexys3/config.vhd designs/leon3-digilent-nexys3/leon3mp.vhd designs/leon3-digilent-nexys4/ahbrom.vhd designs/leon3-digilent-nexys4/config.vhd designs/leon3-digilent-nexys4/leon3mp.vhd designs/leon3-digilent-nexys4ddr/ahbrom.vhd designs/leon3-digilent-nexys4ddr/config.vhd designs/leon3-digilent-nexys4ddr/leon3mp.vhd designs/leon3-digilent-nexys4ddr/dprc_fir_demo/fir_ahb_dma_apb.vhd designs/leon3-digilent-nexys4ddr/dprc_fir_demo/fir_v1.vhd designs/leon3-digilent-nexys4ddr/dprc_fir_demo/fir_v2.vhd designs/leon3-digilent-xc3s1000/ahbrom.vhd designs/leon3-digilent-xc3s1000/config.vhd designs/leon3-digilent-xc3s1000/leon3mp.vhd designs/leon3-digilent-xc3s1000/vga_clkgen.vhd designs/leon3-digilent-xc3s1600e/ahbrom.vhd designs/leon3-digilent-xc3s1600e/config.vhd designs/leon3-digilent-xc3s1600e/leon3mp.vhd designs/leon3-digilent-xc7z020/ahb2axi.vhd designs/leon3-digilent-xc7z020/ahbrom.vhd designs/leon3-digilent-xc7z020/config.vhd designs/leon3-digilent-xc7z020/leon3_zedboard_stub_sim.vhd designs/leon3-digilent-xc7z020/leon3mp.vhd designs/leon3-digilent-xup/ahbrom.vhd designs/leon3-digilent-xup/config.vhd designs/leon3-digilent-xup/leon3mp.vhd designs/leon3-gr-cpci-xc4v/config.vhd designs/leon3-gr-cpci-xc4v/leon3mp.vhd designs/leon3-gr-cpci-xc4v/dprc_fir_demo/fir_ahb_dma_apb.vhd designs/leon3-gr-cpci-xc4v/dprc_fir_demo/fir_v1.vhd designs/leon3-gr-cpci-xc4v/dprc_fir_demo/fir_v2.vhd designs/leon3-gr-pci-xc5v/config.vhd designs/leon3-gr-pci-xc5v/leon3mp.vhd designs/leon3-gr-pci-xc5v/lfclkgen.vhd designs/leon3-gr-xc3s-1500/ahbrom.vhd designs/leon3-gr-xc3s-1500/config.vhd designs/leon3-gr-xc3s-1500/leon3mp.vhd designs/leon3-gr-xc3s-1500/vga_clkgen.vhd designs/leon3-gr-xc6s/ahb2mig_grxc6s_2p.vhd designs/leon3-gr-xc6s/ahbrom.vhd designs/leon3-gr-xc6s/config.vhd designs/leon3-gr-xc6s/leon3mp.vhd designs/leon3-gr-xc6s/svga2ch7301c.vhd designs/leon3-gr-xc6s/vga_clkgen.vhd designs/leon3-minimal/ahbrom.vhd designs/leon3-minimal/config.vhd designs/leon3-minimal/leon3mp.vhd designs/leon3-nuhorizons-3s1500/ahbrom.vhd designs/leon3-nuhorizons-3s1500/config.vhd designs/leon3-nuhorizons-3s1500/leon3mp.vhd designs/leon3-nuhorizons-3s1500/nuhosp3.vhd designs/leon3-nuhorizons-3s1500/smc_mctrl.vhd designs/leon3-terasic-de0-nano/ahbrom.vhd designs/leon3-terasic-de0-nano/clkgen_de0.vhd designs/leon3-terasic-de0-nano/config.vhd designs/leon3-terasic-de0-nano/leon3mp.vhd designs/leon3-terasic-de0-nano/mt48lc16m16a2.vhd designs/leon3-terasic-de0-nano/sdctrl16.vhd designs/leon3-terasic-de2-115/config.vhd designs/leon3-terasic-de2-115/leon3mp.vhd designs/leon3-terasic-de4/config.vhd designs/leon3-terasic-de4/grlib_config.vhd designs/leon3-terasic-de4/leon3mp.vhd designs/leon3-terasic-de4/pll_125.vhd designs/leon3-terasic-s5gs-dsp/config.vhd designs/leon3-terasic-s5gs-dsp/ddr3ctrl.vhd designs/leon3-terasic-s5gs-dsp/ddr3if.vhd designs/leon3-terasic-s5gs-dsp/grlib_config.vhd designs/leon3-terasic-s5gs-dsp/leon3mp.vhd designs/leon3-terasic-s5gs-dsp/memifsim.vhd designs/leon3-xilinx-ac701/ahbrom.vhd designs/leon3-xilinx-ac701/config.vhd designs/leon3-xilinx-ac701/ddr_dummy.vhd designs/leon3-xilinx-ac701/leon3mp.vhd designs/leon3-xilinx-kc705/ahbrom.vhd designs/leon3-xilinx-kc705/config.vhd designs/leon3-xilinx-kc705/ddr_dummy.vhd designs/leon3-xilinx-kc705/leon3mp.vhd designs/leon3-xilinx-ml403/ahbrom.vhd designs/leon3-xilinx-ml403/config.vhd designs/leon3-xilinx-ml403/leon3mp.vhd designs/leon3-xilinx-ml40x/ahbrom.vhd designs/leon3-xilinx-ml40x/config.vhd designs/leon3-xilinx-ml40x/leon3mp.vhd designs/leon3-xilinx-ml501/ahb2mig_ml50x.vhd designs/leon3-xilinx-ml501/ahbrom.vhd designs/leon3-xilinx-ml501/config.vhd designs/leon3-xilinx-ml501/leon3mp.vhd designs/leon3-xilinx-ml501/svga2ch7301c.vhd designs/leon3-xilinx-ml50x/ahb2mig_ml50x.vhd designs/leon3-xilinx-ml50x/ahbrom.vhd designs/leon3-xilinx-ml50x/config.vhd designs/leon3-xilinx-ml50x/leon3mp.vhd designs/leon3-xilinx-ml50x/svga2ch7301c.vhd designs/leon3-xilinx-ml510/ahbrom.vhd designs/leon3-xilinx-ml510/config.vhd designs/leon3-xilinx-ml510/leon3mp.vhd designs/leon3-xilinx-ml510/svga2ch7301c.vhd designs/leon3-xilinx-ml605/ahb2mig_ml605.vhd designs/leon3-xilinx-ml605/ahbrom.vhd designs/leon3-xilinx-ml605/config.vhd designs/leon3-xilinx-ml605/gtxclk.vhd designs/leon3-xilinx-ml605/leon3mp.vhd designs/leon3-xilinx-ml605/svga2ch7301c.vhd designs/leon3-xilinx-sp601/ahb2mig_sp601.vhd designs/leon3-xilinx-sp601/ahbrom.vhd designs/leon3-xilinx-sp601/config.vhd designs/leon3-xilinx-sp601/leon3mp.vhd designs/leon3-xilinx-sp605/ahb2mig_sp605.vhd designs/leon3-xilinx-sp605/ahbrom.vhd designs/leon3-xilinx-sp605/config.vhd designs/leon3-xilinx-sp605/dmactrl.vhd designs/leon3-xilinx-sp605/leon3mp.vhd designs/leon3-xilinx-sp605/pciahbmst.vhd designs/leon3-xilinx-sp605/pcie.vhd designs/leon3-xilinx-sp605/svga2ch7301c.vhd designs/leon3-xilinx-sp605/vga_clkgen.vhd designs/leon3-xilinx-vc707/ahbrom.vhd designs/leon3-xilinx-vc707/axi_mig_7series.vhd designs/leon3-xilinx-vc707/config.vhd designs/leon3-xilinx-vc707/ddr_dummy.vhd designs/leon3-xilinx-vc707/leon3mp.vhd designs/leon3-xilinx-vc707/sgmii_vc707.vhd designs/leon3-xilinx-xc3sd-1800/ahbrom.vhd designs/leon3-xilinx-xc3sd-1800/config.vhd designs/leon3-xilinx-xc3sd-1800/leon3mp.vhd designs/leon3-xilinx-zc702/ahbrom.vhd designs/leon3-xilinx-zc702/config.vhd designs/leon3-xilinx-zc702/leon3_zc702_stub_sim.vhd designs/leon3-xilinx-zc702/leon3mp.vhd designs/leon3-ztex-ufm-111/ahb2mig_ztex.vhd designs/leon3-ztex-ufm-111/ahbrom.vhd designs/leon3-ztex-ufm-111/config.vhd designs/leon3-ztex-ufm-111/leon3mp.vhd designs/leon3-ztex-ufm-115/ahb2mig_ztex.vhd designs/leon3-ztex-ufm-115/ahbrom.vhd designs/leon3-ztex-ufm-115/config.vhd designs/leon3-ztex-ufm-115/leon3mp.vhd designs/leon3mp/ahbrom.vhd designs/leon3mp/config.vhd designs/leon3mp/leon3mp.vhd lib/contrib/devices/devices_con.vhd lib/cypress/ssram/components.vhd lib/cypress/ssram/cy7c1354b.vhd lib/cypress/ssram/cy7c1380d.vhd lib/cypress/ssram/package_utility.vhd lib/esa/memoryctrl/mctrl.in.vhd lib/esa/memoryctrl/mctrl.vhd lib/esa/memoryctrl/memoryctrl.vhd lib/esa/pci/pci_arb.in.vhd lib/esa/pci/pci_arb.vhd lib/esa/pci/pci_arb_pkg.vhd lib/esa/pci/pciarb.vhd lib/esa/pci/pcicomp.vhd lib/eth/comp/ethcomp.vhd lib/eth/core/eth_ahb_mst.vhd lib/eth/core/eth_edcl_ahb_mst.vhd lib/eth/core/eth_rstgen.vhd lib/eth/core/greth_pkg.vhd lib/eth/core/greth_rx.vhd lib/eth/core/greth_tx.vhd lib/eth/core/grethc.vhd lib/eth/wrapper/greth_gbit_gen.vhd lib/eth/wrapper/greth_gen.vhd lib/fmf/fifo/idt7202.vhd lib/fmf/flash/flash.vhd lib/fmf/flash/m25p80.vhd lib/fmf/flash/s25fl064a.vhd lib/fmf/utilities/conversions.vhd lib/fmf/utilities/gen_utils.vhd lib/gaisler/arith/arith.vhd lib/gaisler/arith/div32.vhd lib/gaisler/arith/mul32.vhd lib/gaisler/axi/ahb2axi3b.vhd lib/gaisler/axi/ahb2axi4b.vhd lib/gaisler/axi/ahb2axi_l.vhd lib/gaisler/axi/ahb2axib.vhd lib/gaisler/axi/ahbm2axi.vhd lib/gaisler/axi/ahbm2axi3.vhd lib/gaisler/axi/ahbm2axi4.vhd lib/gaisler/axi/axi.vhd lib/gaisler/axi/axinullslv.vhd lib/gaisler/can/can.vhd lib/gaisler/can/can_mc.in.vhd lib/gaisler/can/can_mc.vhd lib/gaisler/can/can_mod.vhd lib/gaisler/can/can_oc.in.vhd lib/gaisler/can/can_oc.vhd lib/gaisler/can/can_rd.vhd lib/gaisler/can/canmux.vhd lib/gaisler/can/grcan.in.vhd lib/gaisler/ddr/ahb2avl_async.vhd lib/gaisler/ddr/ahb2avl_async_be.vhd lib/gaisler/ddr/ahb2axi_mig_7series.vhd lib/gaisler/ddr/ahb2mig_7series.vhd lib/gaisler/ddr/ahb2mig_7series_cpci_xc7k.vhd lib/gaisler/ddr/ahb2mig_7series_ddr2_dq16_ad13_ba3.vhd lib/gaisler/ddr/ahb2mig_7series_ddr3_dq16_ad15_ba3.vhd lib/gaisler/ddr/ahb2mig_7series_pkg.vhd lib/gaisler/ddr/ddr1spax.vhd lib/gaisler/ddr/ddr1spax_ddr.vhd lib/gaisler/ddr/ddr2buf.vhd lib/gaisler/ddr/ddr2sp.in.vhd lib/gaisler/ddr/ddr2spa.vhd lib/gaisler/ddr/ddr2spax.vhd lib/gaisler/ddr/ddr2spax_ahb.vhd lib/gaisler/ddr/ddr2spax_ddr.vhd lib/gaisler/ddr/ddrintpkg.vhd lib/gaisler/ddr/ddrphy_wrap.vhd lib/gaisler/ddr/ddrpkg.vhd lib/gaisler/ddr/ddrsp.in.vhd lib/gaisler/ddr/ddrspa.vhd lib/gaisler/ddr/mig.in.vhd lib/gaisler/ddr/mig_7series.in.vhd lib/gaisler/gr1553b/gr1553b.in.vhd lib/gaisler/gr1553b/gr1553b_2.in.vhd lib/gaisler/gr1553b/gr1553b_nlw.vhd lib/gaisler/gr1553b/gr1553b_pads.vhd lib/gaisler/gr1553b/gr1553b_pkg.vhd lib/gaisler/gr1553b/gr1553b_stdlogic.vhd lib/gaisler/gr1553b/simtrans1553.vhd lib/gaisler/grdmac/apbmem.vhd lib/gaisler/grdmac/grdmac.vhd lib/gaisler/grdmac/grdmac_1p.vhd lib/gaisler/grdmac/grdmac_ahbmst.vhd lib/gaisler/grdmac/grdmac_alignram.vhd lib/gaisler/grdmac/grdmac_pkg.vhd lib/gaisler/greth/ethernet_mac.vhd lib/gaisler/greth/greth.in.vhd lib/gaisler/greth/greth.vhd lib/gaisler/greth/greth2.in.vhd lib/gaisler/greth/greth_gbit.vhd lib/gaisler/greth/greth_gbit_mb.vhd lib/gaisler/greth/greth_mb.vhd lib/gaisler/greth/grethm.vhd lib/gaisler/greth/grethm_mb.vhd lib/gaisler/greth/greths.vhd lib/gaisler/greth/greths_mb.vhd lib/gaisler/greth/adapters/comma_detect.vhd lib/gaisler/greth/adapters/elastic_buffer.vhd lib/gaisler/greth/adapters/gmii_to_mii.vhd lib/gaisler/greth/adapters/rgmii.vhd lib/gaisler/greth/adapters/sgmii.vhd lib/gaisler/greth/adapters/word_aligner.vhd lib/gaisler/i2c/i2c.in.vhd lib/gaisler/i2c/i2c.vhd lib/gaisler/i2c/i2c2ahb.in.vhd lib/gaisler/i2c/i2c2ahb.vhd lib/gaisler/i2c/i2c2ahb_apb.vhd lib/gaisler/i2c/i2c2ahb_apb_gen.vhd lib/gaisler/i2c/i2c2ahb_gen.vhd lib/gaisler/i2c/i2c2ahbx.vhd lib/gaisler/i2c/i2cmst.vhd lib/gaisler/i2c/i2cmst_gen.vhd lib/gaisler/i2c/i2cslv.in.vhd lib/gaisler/i2c/i2cslv.vhd lib/gaisler/irqmp/irqmp.in.vhd lib/gaisler/irqmp/irqmp.vhd lib/gaisler/jtag/ahbjtag.vhd lib/gaisler/jtag/ahbjtag_bsd.vhd lib/gaisler/jtag/bscan.in.vhd lib/gaisler/jtag/bscanregs.vhd lib/gaisler/jtag/bscanregsbd.vhd lib/gaisler/jtag/jtag.in.vhd lib/gaisler/jtag/jtag.vhd lib/gaisler/jtag/jtag2.in.vhd lib/gaisler/jtag/jtagcom.vhd lib/gaisler/jtag/jtagcom2.vhd lib/gaisler/jtag/jtagtst.vhd lib/gaisler/jtag/libjtagcom.vhd lib/gaisler/l2cache/l2c.in.vhd lib/gaisler/l2cache/pkg/l2cache.vhd lib/gaisler/leon3/cpu_disasx.vhd lib/gaisler/leon3/grfpushwx.vhd lib/gaisler/leon3/l3stat.in.vhd lib/gaisler/leon3/leon3.in.vhd lib/gaisler/leon3/leon3.vhd lib/gaisler/leon3v3/cachemem.vhd lib/gaisler/leon3v3/cmvalidbits.vhd lib/gaisler/leon3v3/dsu3.vhd lib/gaisler/leon3v3/dsu3_mb.vhd lib/gaisler/leon3v3/dsu3x.vhd lib/gaisler/leon3v3/grfpwx.vhd lib/gaisler/leon3v3/grfpwxsh.vhd lib/gaisler/leon3v3/grlfpwx.vhd lib/gaisler/leon3v3/iu3.vhd lib/gaisler/leon3v3/l3stat.vhd lib/gaisler/leon3v3/leon3cg.vhd lib/gaisler/leon3v3/leon3s.vhd lib/gaisler/leon3v3/leon3sh.vhd lib/gaisler/leon3v3/leon3x.vhd lib/gaisler/leon3v3/libcache.vhd lib/gaisler/leon3v3/libfpu.vhd lib/gaisler/leon3v3/libiu.vhd lib/gaisler/leon3v3/libleon3.vhd lib/gaisler/leon3v3/mmu_acache.vhd lib/gaisler/leon3v3/mmu_cache.vhd lib/gaisler/leon3v3/mmu_dcache.vhd lib/gaisler/leon3v3/mmu_icache.vhd lib/gaisler/leon3v3/proc3.vhd lib/gaisler/leon3v3/regfile_3p_l3.vhd lib/gaisler/leon4/l4stat.in.vhd lib/gaisler/leon4/leon4.in.vhd lib/gaisler/leon4/leon4.vhd lib/gaisler/memctrl/ftmctrl.in.vhd lib/gaisler/memctrl/ftsdctrl.in.vhd lib/gaisler/memctrl/ftsrctrl.in.vhd lib/gaisler/memctrl/memctrl.vhd lib/gaisler/memctrl/sdctrl.in.vhd lib/gaisler/memctrl/sdctrl.vhd lib/gaisler/memctrl/sdctrl64.vhd lib/gaisler/memctrl/sdmctrl.vhd lib/gaisler/memctrl/srctrl.in.vhd lib/gaisler/memctrl/srctrl.vhd lib/gaisler/memctrl/ssrctrl.in.vhd lib/gaisler/misc/ahb_mst_iface.vhd lib/gaisler/misc/ahbdma.vhd lib/gaisler/misc/ahbdpram.vhd lib/gaisler/misc/ahbmmux.vhd lib/gaisler/misc/ahbram.in.vhd lib/gaisler/misc/ahbram.vhd lib/gaisler/misc/ahbrom.in.vhd lib/gaisler/misc/ahbsmux.vhd lib/gaisler/misc/ahbstat.in.vhd lib/gaisler/misc/ahbstat.vhd lib/gaisler/misc/ahbtrace.vhd lib/gaisler/misc/ahbtrace_mb.vhd lib/gaisler/misc/ahbtrace_mmb.vhd lib/gaisler/misc/apb3cdc.vhd lib/gaisler/misc/apbps2.vhd lib/gaisler/misc/apbvga.vhd lib/gaisler/misc/charrom.vhd lib/gaisler/misc/charrom_package.vhd lib/gaisler/misc/ftahbram.in.vhd lib/gaisler/misc/gptimer.in.vhd lib/gaisler/misc/gptimer.vhd lib/gaisler/misc/gracectrl.in.vhd lib/gaisler/misc/gracectrl.vhd lib/gaisler/misc/grgpio.in.vhd lib/gaisler/misc/grgpio.vhd lib/gaisler/misc/grgpio2.in.vhd lib/gaisler/misc/grgprbank.vhd lib/gaisler/misc/grgpreg.vhd lib/gaisler/misc/grsysmon.in.vhd lib/gaisler/misc/grsysmon.vhd lib/gaisler/misc/logan.vhd lib/gaisler/misc/misc.vhd lib/gaisler/misc/ps2.in.vhd lib/gaisler/misc/ps2vga.in.vhd lib/gaisler/misc/rstgen.vhd lib/gaisler/misc/svgactrl.in.vhd lib/gaisler/misc/svgactrl.vhd lib/gaisler/net/edcl.in.vhd lib/gaisler/net/net.vhd lib/gaisler/pci/pci.vhd lib/gaisler/pci/pcipads.vhd lib/gaisler/pci/grpci1/pci.in.vhd lib/gaisler/pci/grpci2/grpci2.in.vhd lib/gaisler/pci/grpci2/grpci2.vhd lib/gaisler/pci/grpci2/grpci2_ahb_mst.vhd lib/gaisler/pci/grpci2/grpci2_phy.vhd lib/gaisler/pci/grpci2/grpci2_phy_wrapper.vhd lib/gaisler/pci/grpci2/pcilib2.vhd lib/gaisler/pci/grpci2/wrapper/grpci2_gen.vhd lib/gaisler/pci/pcitrace/pcitrace.in.vhd lib/gaisler/pci/ptf/pt_pci_arb.vhd lib/gaisler/pci/ptf/pt_pci_master.vhd lib/gaisler/pci/ptf/pt_pci_monitor.vhd lib/gaisler/pci/ptf/pt_pci_target.vhd lib/gaisler/pci/ptf/pt_pkg.vhd lib/gaisler/pcie/pcie.in.vhd lib/gaisler/pcie/pcie.vhd lib/gaisler/spacewire/router.in.vhd lib/gaisler/spacewire/spacewire.in.vhd lib/gaisler/spacewire/spacewire.vhd lib/gaisler/spi/spi.vhd lib/gaisler/spi/spi2ahb.in.vhd lib/gaisler/spi/spi2ahb.vhd lib/gaisler/spi/spi2ahb_apb.vhd lib/gaisler/spi/spi2ahbx.vhd lib/gaisler/spi/spi_flash.vhd lib/gaisler/spi/spictrl.in.vhd lib/gaisler/spi/spictrl.vhd lib/gaisler/spi/spictrlx.vhd lib/gaisler/spi/spimctrl.in.vhd lib/gaisler/spi/spimctrl.vhd lib/gaisler/srmmu/libmmu.vhd lib/gaisler/srmmu/mmu.vhd lib/gaisler/srmmu/mmuconfig.vhd lib/gaisler/srmmu/mmuiface.vhd lib/gaisler/srmmu/mmulru.vhd lib/gaisler/srmmu/mmulrue.vhd lib/gaisler/srmmu/mmutlb.vhd lib/gaisler/srmmu/mmutlbcam.vhd lib/gaisler/srmmu/mmutw.vhd lib/gaisler/subsys/leon_dsu_stat_base.in.vhd lib/gaisler/subsys/leon_dsu_stat_base.vhd lib/gaisler/subsys/subsys.vhd lib/gaisler/uart/ahbuart.vhd lib/gaisler/uart/apbuart.vhd lib/gaisler/uart/dcom.in.vhd lib/gaisler/uart/dcom.vhd lib/gaisler/uart/dcom_uart.vhd lib/gaisler/uart/libdcom.vhd lib/gaisler/uart/uart.vhd lib/gaisler/uart/uart1.in.vhd lib/gaisler/uart/uart2.in.vhd lib/gaisler/usb/grusb.vhd lib/gaisler/usb/grusb_dcl.in.vhd lib/gaisler/usb/grusbdc.in.vhd lib/gaisler/usb/grusbhc.in.vhd lib/grlib/amba/ahbctrl.vhd lib/grlib/amba/ahbmst.vhd lib/grlib/amba/amba.in.vhd lib/grlib/amba/amba.vhd lib/grlib/amba/amba_tp.vhd lib/grlib/amba/apbctrl.vhd lib/grlib/amba/apbctrldp.vhd lib/grlib/amba/apbctrlsp.vhd lib/grlib/amba/apbctrlx.vhd lib/grlib/amba/defmst.vhd lib/grlib/amba/devices.vhd lib/grlib/amba/dma2ahb.vhd lib/grlib/amba/dma2ahb_pkg.vhd lib/grlib/amba/dma2ahb_tp.vhd lib/grlib/dftlib/dftlib.vhd lib/grlib/modgen/leaves.vhd lib/grlib/modgen/multlib.vhd lib/grlib/sparc/cpu_disas.vhd lib/grlib/sparc/sparc.vhd lib/grlib/sparc/sparc_disas.vhd lib/grlib/stdlib/config.vhd lib/grlib/stdlib/config_types.vhd lib/grlib/stdlib/stdio.vhd lib/grlib/stdlib/stdlib.vhd lib/grlib/stdlib/version.vhd lib/grlib/util/debug.in.vhd lib/grlib/util/fpudummy.vhd lib/grlib/util/util.vhd lib/gsi/ssram/core_burst.vhd lib/gsi/ssram/functions.vhd lib/gsi/ssram/g880e18bt.vhd lib/micron/sdram/components.vhd lib/micron/sdram/mt48lc16m16a2.vhd lib/opencores/can/can_top.vhd lib/opencores/can/cancomp.vhd lib/opencores/ge_1000baseX/ge_1000baseX_comp.vhd lib/opencores/i2c/i2c_master_bit_ctrl.vhd lib/opencores/i2c/i2c_master_byte_ctrl.vhd lib/opencores/i2c/i2coc.vhd lib/spw/comp/spwcomp.vhd lib/spw/wrapper/grspw2_gen.vhd lib/spw/wrapper/grspw_codec_gen.vhd lib/spw/wrapper/grspw_gen.vhd lib/tech/atc18/components/atmel_components.vhd lib/tech/atc18/components/atmel_simprims.vhd lib/tech/ec/orca/ORCA_L.vhd lib/tech/ec/orca/global.vhd lib/tech/ec/orca/mem3.vhd lib/tech/ec/orca/orca.vhd lib/tech/ec/orca/orca_ecmem.vhd lib/tech/ec/orca/orcacomp.vhd lib/tech/snps/dw02/comp/DW02_components.vhd lib/tech/umc18/components/umc_components.vhd lib/tech/umc18/components/umc_simprims.vhd lib/tech/virage/vcomponents/virage_vcomponents.vhd lib/techmap/altera_mf/clkgen_altera_mf.vhd lib/techmap/altera_mf/memory_altera_mf.vhd lib/techmap/altera_mf/tap_altera_mf.vhd lib/techmap/atc18/pads_atc18.vhd lib/techmap/clocks/clkgen.in.vhd lib/techmap/cycloneiii/cycloneiii_clkgen.vhd lib/techmap/cycloneiii/cycloneiii_ddr_phy.vhd lib/techmap/cycloneiii/ddr_phy_cycloneiii.vhd lib/techmap/cycloneiii/alt/aclkout.vhd lib/techmap/cycloneiii/alt/actrlout.vhd lib/techmap/cycloneiii/alt/admout.vhd lib/techmap/cycloneiii/alt/adqin.vhd lib/techmap/cycloneiii/alt/adqout.vhd lib/techmap/cycloneiii/alt/adqsin.vhd lib/techmap/cycloneiii/alt/adqsout.vhd lib/techmap/cycloneiii/alt/apll.vhd lib/techmap/dware/mul_dware.vhd lib/techmap/ec/ddr_ec.vhd lib/techmap/ec/memory_ec.vhd lib/techmap/eclipsee/memory_eclipse.vhd lib/techmap/gencomp/clkgen.in.vhd lib/techmap/gencomp/gencomp.vhd lib/techmap/gencomp/netcomp.vhd lib/techmap/gencomp/tech.in.vhd lib/techmap/grdware/mul_dware.vhd lib/techmap/inferred/ddr_inferred.vhd lib/techmap/inferred/ddr_phy_inferred.vhd lib/techmap/inferred/ddrphy_datapath.vhd lib/techmap/inferred/fifo_inferred.vhd lib/techmap/inferred/lpddr2_phy_inferred.vhd lib/techmap/inferred/memory_inferred.vhd lib/techmap/inferred/mul_inferred.vhd lib/techmap/inferred/sim_pll.vhd lib/techmap/maps/allclkgen.vhd lib/techmap/maps/allddr.vhd lib/techmap/maps/allmem.vhd lib/techmap/maps/allmul.vhd lib/techmap/maps/allpads.vhd lib/techmap/maps/alltap.vhd lib/techmap/maps/cdcbus.vhd lib/techmap/maps/clkand.vhd lib/techmap/maps/clkgen.vhd lib/techmap/maps/clkinv.vhd lib/techmap/maps/clkmux.vhd lib/techmap/maps/clkpad.vhd lib/techmap/maps/clkpad_ds.vhd lib/techmap/maps/cpu_disas_net.vhd lib/techmap/maps/ddr_ireg.vhd lib/techmap/maps/ddr_oreg.vhd lib/techmap/maps/ddrphy.vhd lib/techmap/maps/grfpw_net.vhd lib/techmap/maps/grgates.vhd lib/techmap/maps/grlfpw_net.vhd lib/techmap/maps/grpci2_phy_net.vhd lib/techmap/maps/inpad.vhd lib/techmap/maps/inpad_ddr.vhd lib/techmap/maps/inpad_ds.vhd lib/techmap/maps/iodpad.vhd lib/techmap/maps/iopad.vhd lib/techmap/maps/iopad_ddr.vhd lib/techmap/maps/iopad_ds.vhd lib/techmap/maps/iopad_tm.vhd lib/techmap/maps/leon3_net.vhd lib/techmap/maps/leon4_net.vhd lib/techmap/maps/lvds_combo.vhd lib/techmap/maps/memrwcol.vhd lib/techmap/maps/mul_61x61.vhd lib/techmap/maps/nandtree.vhd lib/techmap/maps/odpad.vhd lib/techmap/maps/outpad.vhd lib/techmap/maps/outpad_ddr.vhd lib/techmap/maps/outpad_ds.vhd lib/techmap/maps/regfile_3p.vhd lib/techmap/maps/ringosc.vhd lib/techmap/maps/scanreg.vhd lib/techmap/maps/sdram_phy.vhd lib/techmap/maps/serdes.vhd lib/techmap/maps/skew_outpad.vhd lib/techmap/maps/spictrl_net.vhd lib/techmap/maps/syncfifo_2p.vhd lib/techmap/maps/syncram.vhd lib/techmap/maps/syncram128.vhd lib/techmap/maps/syncram128bw.vhd lib/techmap/maps/syncram156bw.vhd lib/techmap/maps/syncram256bw.vhd lib/techmap/maps/syncram64.vhd lib/techmap/maps/syncram_2p.vhd lib/techmap/maps/syncram_2pbw.vhd lib/techmap/maps/syncram_dp.vhd lib/techmap/maps/syncrambw.vhd lib/techmap/maps/syncreg.vhd lib/techmap/maps/system_monitor.vhd lib/techmap/maps/tap.vhd lib/techmap/maps/techbuf.vhd lib/techmap/maps/techmult.vhd lib/techmap/maps/toutpad.vhd lib/techmap/maps/toutpad_ds.vhd lib/techmap/maps/toutpad_tm.vhd lib/techmap/saed32/clkgen_saed32.vhd lib/techmap/saed32/memory_saed32.vhd lib/techmap/saed32/pads_saed32.vhd lib/techmap/stratixii/clkgen_stratixii.vhd lib/techmap/stratixii/stratixii_ddr_phy.vhd lib/techmap/stratixiii/clkgen_stratixiii.vhd lib/techmap/stratixiii/ddr_phy_stratixiii.vhd lib/techmap/stratixiii/serdes_stratixiii.vhd lib/techmap/stratixiii/adq_dqs/bidir_dq_iobuf_inst.vhd lib/techmap/stratixiii/adq_dqs/bidir_dqs_iobuf_inst.vhd lib/techmap/stratixiii/adq_dqs/dq_dqs_inst.vhd lib/techmap/stratixiii/adq_dqs/output_dqs_iobuf_inst.vhd lib/techmap/stratixiii/alt/aclkout.vhd lib/techmap/stratixiii/alt/actrlout.vhd lib/techmap/stratixiii/alt/admout.vhd lib/techmap/stratixiii/alt/adqin.vhd lib/techmap/stratixiii/alt/adqout.vhd lib/techmap/stratixiii/alt/adqsin.vhd lib/techmap/stratixiii/alt/adqsout.vhd lib/techmap/stratixiii/alt/apll.vhd lib/techmap/stratixiv/ddr_uniphy.vhd lib/techmap/stratixv/clkgen_stratixv.vhd lib/techmap/umc18/memory_umc18.vhd lib/techmap/umc18/pads_umc18.vhd lib/techmap/virage/memory_virage.vhd lib/techmap/virtex/clkgen_virtex.vhd lib/techmap/virtex/memory_virtex.vhd lib/techmap/virtex5/serdes_unisim.vhd lib/work/debug/cpu_disas.vhd lib/work/debug/debug.vhd riscv/tools/iu3.original.vhd lib/opencores/ge_1000baseX/ge_1000baseX_test.v designs/leon3-ahbfile/testbench.vhd designs/leon3-altera-c5ekit/testbench.vhd designs/leon3-altera-de2-ep2c35/testbench.vhd designs/leon3-altera-ep2s60-ddr/testbench.vhd designs/leon3-altera-ep2s60-sdr/testbench.vhd designs/leon3-altera-ep3c25-eek/testbench.vhd designs/leon3-altera-ep3c25/testbench.vhd designs/leon3-altera-ep3sl150/testbench.vhd designs/leon3-arrow-bemicro-sdk/testbench.vhd designs/leon3-asic/testbench.vhd designs/leon3-asic/testbench_netlist.vhd designs/leon3-avnet-3s1500/testbench.vhd designs/leon3-avnet-eval-xc4vlx25/testbench.vhd designs/leon3-avnet-eval-xc4vlx60/testbench.vhd designs/leon3-clock-gate/testbench.vhd designs/leon3-digilent-anvyl/testbench.vhd designs/leon3-digilent-atlys/testbench.vhd designs/leon3-digilent-basys3/testbench.vhd designs/leon3-digilent-nexys-video/testbench.vhd designs/leon3-digilent-nexys3/testbench.vhd designs/leon3-digilent-nexys4/testbench.vhd designs/leon3-digilent-nexys4ddr/testbench.vhd designs/leon3-digilent-xc3s1000/testbench.vhd designs/leon3-digilent-xc3s1600e/testbench.vhd designs/leon3-digilent-xc7z020/testbench.vhd designs/leon3-digilent-xup/testbench.vhd designs/leon3-gr-cpci-xc4v/testbench.vhd designs/leon3-gr-pci-xc5v/testbench.vhd designs/leon3-gr-xc3s-1500/testbench.vhd designs/leon3-gr-xc6s/testbench.vhd designs/leon3-minimal/testbench.vhd designs/leon3-nuhorizons-3s1500/testbench.vhd designs/leon3-terasic-de0-nano/testbench.vhd designs/leon3-terasic-de2-115/testbench.vhd designs/leon3-terasic-de4/testbench.vhd designs/leon3-terasic-s5gs-dsp/testbench.vhd designs/leon3-xilinx-ac701/testbench.vhd designs/leon3-xilinx-kc705/testbench.vhd designs/leon3-xilinx-ml403/testbench.vhd designs/leon3-xilinx-ml40x/testbench.vhd designs/leon3-xilinx-ml501/testbench.vhd designs/leon3-xilinx-ml50x/testbench.vhd designs/leon3-xilinx-ml510/testbench.vhd designs/leon3-xilinx-ml605/testbench.vhd designs/leon3-xilinx-sp601/testbench.vhd designs/leon3-xilinx-sp605/testbench.vhd designs/leon3-xilinx-vc707/testbench.vhd designs/leon3-xilinx-xc3sd-1800/testbench.vhd designs/leon3-xilinx-zc702/testbench.vhd designs/leon3-ztex-ufm-111/testbench.vhd designs/leon3-ztex-ufm-115/testbench.vhd designs/leon3mp/testbench.vhd lib/gaisler/ambatest/ahbtbm.vhd lib/gaisler/ambatest/ahbtbp.vhd lib/gaisler/ambatest/ahbtbs.vhd lib/gaisler/leon3v3/tbufmem.vhd lib/gaisler/leon3v3/tbufmem_2p.vhd lib/gaisler/sim/ahbram_sim.vhd lib/gaisler/sim/ahbrep.vhd lib/gaisler/sim/aximem.vhd lib/gaisler/sim/axirep.vhd lib/gaisler/sim/ddr2ram.vhd lib/gaisler/sim/ddr3ram.vhd lib/gaisler/sim/ddrram.vhd lib/gaisler/sim/delay_wire.vhd lib/gaisler/sim/phy.vhd lib/gaisler/sim/pwm_check.vhd lib/gaisler/sim/sdrtestmod.vhd lib/gaisler/sim/ser_phy.vhd lib/gaisler/sim/sim.vhd lib/gaisler/sim/sram.vhd lib/gaisler/sim/sram16.vhd lib/grlib/dftlib/synciotest.vhd lib/grlib/stdlib/stdio_tb.vhd lib/grlib/stdlib/testlib.vhd lib/tech/dware/simprims/DW_Foundation_arith.vhd lib/tech/dware/simprims/DW_Foundation_comp.vhd lib/tech/dware/simprims/DW_Foundation_comp_arith.vhd lib/tech/dware/simprims/DWpackages.vhd lib/tech/eclipsee/simprims/eclipse.vhd lib/tech/simprim/vcomponents/vcomponents.vhd lib/tech/virage/simprims/virage_simprims.vhd lib/techmap/unisim/buffer_unisim.vhd lib/techmap/unisim/clkgen_unisim.vhd lib/techmap/unisim/ddr_phy_unisim.vhd lib/techmap/unisim/ddr_unisim.vhd lib/techmap/unisim/memory_unisim.vhd lib/techmap/unisim/mul_unisim.vhd lib/techmap/unisim/pads_unisim.vhd lib/techmap/unisim/spictrl_unisim.vhd lib/techmap/unisim/sysmon_unisim.vhd lib/techmap/unisim/tap_unisim.vhd lib/testgrouppolito/pr/async_dprc.vhd lib/testgrouppolito/pr/d2prc.vhd lib/testgrouppolito/pr/d2prc_edac.vhd lib/testgrouppolito/pr/dprc.vhd lib/testgrouppolito/pr/dprc_pkg.vhd lib/testgrouppolito/pr/pr.in.vhd lib/testgrouppolito/pr/sync_dprc.vhd lib/work/debug/grtestmod.vhd"
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("ReonV") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o /eda/processor_ci_utils/labels.json"
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
                                dir("ReonV") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p ReonV -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("ReonV") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p ReonV -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("ReonV") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                }
                            }
                        }
                    }
                }
                
                stage('digilent_arty_a7_100t') {
                    options {
                        lock(resource: 'digilent_arty_a7_100t')
                    }
                    stages {
                        stage('Synthesis and PnR') {
                            steps {
                                dir("ReonV") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p ReonV -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("ReonV") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p ReonV -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("ReonV") {
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
