
pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                sh 'rm -rf openc910'
                sh 'git clone --recursive --depth=1 https://github.com/XUANTIE-RV/openc910/ openc910'
            }
        }

        

        stage('Simulation') {
            steps {
                dir("openc910") {
                    sh "/eda/oss-cad-suite/bin/iverilog -o simulation.out -g2005                  -s   C910_RTL_FACTORY/gen_rtl/biu/rtl/ct_biu_csr_req_arbiter.v C910_RTL_FACTORY/gen_rtl/biu/rtl/ct_biu_lowpower.v C910_RTL_FACTORY/gen_rtl/biu/rtl/ct_biu_other_io_sync.v C910_RTL_FACTORY/gen_rtl/biu/rtl/ct_biu_read_channel.v C910_RTL_FACTORY/gen_rtl/biu/rtl/ct_biu_req_arbiter.v C910_RTL_FACTORY/gen_rtl/biu/rtl/ct_biu_snoop_channel.v C910_RTL_FACTORY/gen_rtl/biu/rtl/ct_biu_top.v C910_RTL_FACTORY/gen_rtl/biu/rtl/ct_biu_write_channel.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_apbif.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_bmbif.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_bmbif_kid.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_ctcq.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_ctcq_reqq_entry.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_ctcq_respq_entry.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_ebiuif.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_l2cif.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_ncq.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_ncq_gm.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_regs.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_regs_kid.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_snb.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_snb_arb.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_snb_dp_sel.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_snb_dp_sel_16.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_snb_dp_sel_8.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_snb_sab.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_snb_sab_entry.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_top.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_vb.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ciu_vb_aw_entry.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ebiu_cawt_entry.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ebiu_lowpower.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ebiu_ncwt_entry.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ebiu_read_channel.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ebiu_snoop_channel_dummy.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ebiu_top.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_ebiu_write_channel.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_fifo.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_piu_other_io.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_piu_other_io_dummy.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_piu_other_io_sync.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_piu_top.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_piu_top_dummy.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_piu_top_dummy_device.v C910_RTL_FACTORY/gen_rtl/ciu/rtl/ct_prio.v C910_RTL_FACTORY/gen_rtl/clint/rtl/ct_clint_func.v C910_RTL_FACTORY/gen_rtl/clint/rtl/ct_clint_top.v C910_RTL_FACTORY/gen_rtl/clk/rtl/ct_clk_top.v C910_RTL_FACTORY/gen_rtl/clk/rtl/ct_mp_clk_top.v C910_RTL_FACTORY/gen_rtl/clk/rtl/gated_clk_cell.v C910_RTL_FACTORY/gen_rtl/common/rtl/BUFGCE.v C910_RTL_FACTORY/gen_rtl/common/rtl/booth_code.v C910_RTL_FACTORY/gen_rtl/common/rtl/booth_code_v1.v C910_RTL_FACTORY/gen_rtl/common/rtl/compressor_32.v C910_RTL_FACTORY/gen_rtl/common/rtl/compressor_42.v C910_RTL_FACTORY/gen_rtl/common/rtl/sync_level2level.v C910_RTL_FACTORY/gen_rtl/common/rtl/sync_level2pulse.v C910_RTL_FACTORY/gen_rtl/cp0/rtl/ct_cp0_iui.v C910_RTL_FACTORY/gen_rtl/cp0/rtl/ct_cp0_lpmd.v C910_RTL_FACTORY/gen_rtl/cp0/rtl/ct_cp0_regs.v C910_RTL_FACTORY/gen_rtl/cp0/rtl/ct_cp0_top.v C910_RTL_FACTORY/gen_rtl/cpu/rtl/ct_core.v C910_RTL_FACTORY/gen_rtl/cpu/rtl/ct_rmu_top_dummy.v C910_RTL_FACTORY/gen_rtl/cpu/rtl/ct_sysio_kid.v C910_RTL_FACTORY/gen_rtl/cpu/rtl/ct_sysio_top.v C910_RTL_FACTORY/gen_rtl/cpu/rtl/ct_top.v C910_RTL_FACTORY/gen_rtl/cpu/rtl/mp_top_golden_port.v C910_RTL_FACTORY/gen_rtl/cpu/rtl/openC910.v C910_RTL_FACTORY/gen_rtl/cpu/rtl/top_golden_port.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_1024x128.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_1024x144.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_1024x32.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_1024x59.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_1024x64.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_1024x92.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_128x104.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_128x144.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_128x16.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_16384x128.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_2048x128.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_2048x144.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_2048x32.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_2048x59.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_2048x88.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x100.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x144.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x196.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x23.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x52.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x54.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x59.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x7.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_256x84.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_32768x128.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_4096x128.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_4096x144.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_4096x32.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_4096x84.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_512x144.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_512x22.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_512x44.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_512x52.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_512x54.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_512x59.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_512x7.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_512x96.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_64x108.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_65536x128.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_8192x128.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/ct_f_spsram_8192x32.v C910_RTL_FACTORY/gen_rtl/fpga/rtl/fpga_ram.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_bkpt.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_common_dbg_info.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_common_regs.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_common_top.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_ctrl.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_dbg_info.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_ddc_ctrl.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_ddc_dp.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_etm.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_etm_if.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_event.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_io.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_ir.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_nirv_bkpt.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_pcfifo.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_private_ir.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_private_top.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_regs.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_serial.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_sm.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_sync_3flop.v C910_RTL_FACTORY/gen_rtl/had/rtl/ct_had_trace.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_dep_reg_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_dep_reg_src2_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_dep_vreg_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_dep_vreg_srcv2_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_id_ctrl.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_id_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_id_decd_special.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_id_dp.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_id_fence.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_id_split_long.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_id_split_short.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_ir_ctrl.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_ir_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_ir_dp.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_ir_frt.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_ir_rt.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_ir_vrt.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_aiq0.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_aiq0_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_aiq1.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_aiq1_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_aiq_lch_rdy_1.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_aiq_lch_rdy_2.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_aiq_lch_rdy_3.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_biq.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_biq_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_ctrl.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_dp.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_lsiq.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_lsiq_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_pipe_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_sdiq.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_sdiq_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_viq0.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_viq0_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_viq1.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_is_viq1_entry.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_ctrl.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_dp.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_fwd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_fwd_preg.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_fwd_vreg.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_pipe0_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_pipe1_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_pipe2_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_pipe3_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_pipe4_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_pipe6_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_pipe7_decd.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_prf_eregfile.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_prf_fregfile.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_prf_gated_ereg.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_prf_gated_preg.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_prf_gated_vreg.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_prf_pregfile.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_rf_prf_vregfile.v C910_RTL_FACTORY/gen_rtl/idu/rtl/ct_idu_top.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_addrgen.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_bht.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_bht_pre_array.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_bht_sel_array.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_debug.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_decd_normal.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ibctrl.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ibdp.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ibuf.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ibuf_entry.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_icache_data_array0.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_icache_data_array1.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_icache_if.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_icache_predecd_array0.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_icache_predecd_array1.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_icache_tag_array.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ifctrl.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ifdp.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ipb.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ipctrl.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ipdecode.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ipdp.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_l1_refill.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_lbuf.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_lbuf_entry.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_pcfifo_if.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_pcgen.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_precode.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_ras.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_sfp.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_sfp_entry.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_top.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_ifu_vector.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_1024x59.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_1024x64.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_128x16.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_2048x32_split.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_2048x59.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_256x23.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_256x59.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_512x22.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_512x44.v C910_RTL_FACTORY/gen_rtl/ifu/rtl/ct_spsram_512x59.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_alu.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_bju.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_bju_pcfifo.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_bju_pcfifo_entry.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_bju_pcfifo_read_entry.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_cbus.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_div.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_div_entry.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_div_srt_radix16.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_mult.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_rbus.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_special.v C910_RTL_FACTORY/gen_rtl/iu/rtl/ct_iu_top.v C910_RTL_FACTORY/gen_rtl/iu/rtl/multiplier_65x65_3_stage.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_cmp.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_data.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_icc.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_prefetch.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_sub_bank.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_tag.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_tag_ecc.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_top.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2c_wb.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2cache_data_array.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2cache_dirty_array_16way.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2cache_tag_array_16way.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_l2cache_top.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_1024x128.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_1024x144.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_1024x92.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_128x104.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_128x144.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_16384x128.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_2048x128.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_2048x144.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_2048x88.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_256x100.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_256x144.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_32768x128.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_4096x128.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_4096x144.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_4096x84.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_512x144.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_512x96.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_64x108.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_65536x128.v C910_RTL_FACTORY/gen_rtl/l2c/rtl/ct_spsram_8192x128.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_amr.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_bus_arb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_cache_buffer.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_ctrl.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_dcache_arb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_dcache_data_array.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_dcache_dirty_array.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_dcache_info_update.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_dcache_ld_tag_array.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_dcache_tag_array.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_dcache_top.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_icc.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_idfifo_8.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_idfifo_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_ld_ag.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_ld_da.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_ld_dc.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_ld_wb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_lfb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_lfb_addr_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_lfb_data_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_lm.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_lq.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_lq_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_mcic.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_gpfb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_gsdb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_pfb_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_pfb_l1sm.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_pfb_l2sm.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_pfb_tsm.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_pmb_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_sdb_cmp.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_pfu_sdb_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_rb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_rb_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_rot_data.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_sd_ex1.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_snoop_ctcq.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_snoop_ctcq_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_snoop_req_arbiter.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_snoop_resp.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_snoop_snq.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_snoop_snq_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_spec_fail_predict.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_sq.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_sq_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_st_ag.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_st_da.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_st_dc.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_st_wb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_top.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_vb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_vb_addr_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_vb_sdb_data.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_vb_sdb_data_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_wmb.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_wmb_ce.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_lsu_wmb_entry.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_1024x32.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_2048x32.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_256x52.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_256x54.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_256x7.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_4096x32.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_512x52.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_512x54.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_512x7.v C910_RTL_FACTORY/gen_rtl/lsu/rtl/ct_spsram_8192x32.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_arb.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_dplru.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_dutlb.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_dutlb_entry.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_dutlb_huge_entry.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_dutlb_read.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_iplru.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_iutlb.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_iutlb_entry.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_iutlb_fst_entry.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_jtlb.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_jtlb_data_array.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_jtlb_tag_array.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_ptw.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_regs.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_sysmap.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_sysmap_hit.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_tlboper.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_mmu_top.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_spsram_256x196.v C910_RTL_FACTORY/gen_rtl/mmu/rtl/ct_spsram_256x84.v C910_RTL_FACTORY/gen_rtl/plic/rtl/csky_apb_1tox_matrix.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_32to1_arb.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_arb_ctrl.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_ctrl.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_granu2_arb.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_granu_arb.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_hart_arb.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_hreg_busif.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_int_kid.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_kid_busif.v C910_RTL_FACTORY/gen_rtl/plic/rtl/plic_top.v C910_RTL_FACTORY/gen_rtl/pmp/rtl/ct_pmp_acc.v C910_RTL_FACTORY/gen_rtl/pmp/rtl/ct_pmp_comp_hit.v C910_RTL_FACTORY/gen_rtl/pmp/rtl/ct_pmp_regs.v C910_RTL_FACTORY/gen_rtl/pmp/rtl/ct_pmp_top.v C910_RTL_FACTORY/gen_rtl/pmu/rtl/ct_hpcp_adder_sel.v C910_RTL_FACTORY/gen_rtl/pmu/rtl/ct_hpcp_cnt.v C910_RTL_FACTORY/gen_rtl/pmu/rtl/ct_hpcp_cntinten_reg.v C910_RTL_FACTORY/gen_rtl/pmu/rtl/ct_hpcp_cntof_reg.v C910_RTL_FACTORY/gen_rtl/pmu/rtl/ct_hpcp_event.v C910_RTL_FACTORY/gen_rtl/pmu/rtl/ct_hpcp_top.v C910_RTL_FACTORY/gen_rtl/rst/rtl/ct_mp_rst_top.v C910_RTL_FACTORY/gen_rtl/rst/rtl/ct_rst_top.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_compare_iid.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_encode_32.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_encode_64.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_encode_8.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_encode_96.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_expand_32.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_expand_64.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_expand_8.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_expand_96.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_pst_ereg.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_pst_ereg_entry.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_pst_preg.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_pst_preg_entry.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_pst_vreg.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_pst_vreg_dummy.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_pst_vreg_entry.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_retire.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_rob.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_rob_entry.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_rob_expt.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_rob_rt.v C910_RTL_FACTORY/gen_rtl/rtu/rtl/ct_rtu_top.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_close_s0_d.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_close_s0_h.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_close_s1_d.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_close_s1_h.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_ctrl.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_double_dp.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_half_dp.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_onehot_sel_d.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_onehot_sel_h.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_scalar_dp.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fadd_top.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_ctrl.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_double_dp.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_dtoh_sh.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_dtos_sh.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_ftoi_sh.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_htos_sh.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_itof_sh.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_scalar_dp.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_stod_sh.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_stoh_sh.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fcnvt_top.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fspu_ctrl.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fspu_double.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fspu_dp.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fspu_half.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fspu_single.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_fspu_top.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_vfalu_dp_pipe6.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_vfalu_dp_pipe7.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_vfalu_top_pipe6.v C910_RTL_FACTORY/gen_rtl/vfalu/rtl/ct_vfalu_top_pipe7.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_ctrl.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_double.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_ff1.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_pack.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_prepare.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_round.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_scalar_dp.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_srt.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_srt_radix16_bound_table.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_srt_radix16_only_div.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_srt_radix16_with_sqrt.v C910_RTL_FACTORY/gen_rtl/vfdsu/rtl/ct_vfdsu_top.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_ctrl.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_dp.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_ff1_10bit.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_lza.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_lza_32.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_lza_42.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_lza_simd_half.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_mult1.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_mult_compressor.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_mult_simd_half.v C910_RTL_FACTORY/gen_rtl/vfmau/rtl/ct_vfmau_top.v C910_RTL_FACTORY/gen_rtl/vfpu/rtl/ct_vfpu_cbus.v C910_RTL_FACTORY/gen_rtl/vfpu/rtl/ct_vfpu_ctrl.v C910_RTL_FACTORY/gen_rtl/vfpu/rtl/ct_vfpu_dp.v C910_RTL_FACTORY/gen_rtl/vfpu/rtl/ct_vfpu_rbus.v C910_RTL_FACTORY/gen_rtl/vfpu/rtl/ct_vfpu_top.v smart_run/logical/ahb/ahb.v smart_run/logical/ahb/ahb2apb.v smart_run/logical/apb/apb.v smart_run/logical/apb/apb_bridge.v smart_run/logical/axi/axi2ahb.v smart_run/logical/axi/axi_err128.v smart_run/logical/axi/axi_fifo.v smart_run/logical/axi/axi_fifo_entry.v smart_run/logical/axi/axi_interconnect128.v smart_run/logical/axi/axi_slave128.v smart_run/logical/common/BUFGCE.v smart_run/logical/common/clk_gen.v smart_run/logical/common/cpu_sub_system_axi.v smart_run/logical/common/err_gen.v smart_run/logical/common/fifo_counter.v smart_run/logical/common/fpga_clk_gen.v smart_run/logical/common/rv_integration_platform.v smart_run/logical/common/soc.v smart_run/logical/common/timer.v smart_run/logical/common/wid_entry.v smart_run/logical/common/wid_for_axi4.v smart_run/logical/gpio/gpio.v smart_run/logical/gpio/gpio_apbif.v smart_run/logical/gpio/gpio_ctrl.v smart_run/logical/mem/f_spsram_32768x128.v smart_run/logical/mem/f_spsram_large.v smart_run/logical/mem/mem_ctrl.v smart_run/logical/mem/ram.v smart_run/logical/pmu/pmu.v smart_run/logical/pmu/px_had_sync.v smart_run/logical/pmu/sync.v smart_run/logical/pmu/tap2_sm.v smart_run/logical/uart/uart.v smart_run/logical/uart/uart_apb_reg.v smart_run/logical/uart/uart_baud_gen.v smart_run/logical/uart/uart_ctrl.v smart_run/logical/uart/uart_receive.v smart_run/logical/uart/uart_trans.v "
                }
            }
        }

         stage('Utilities')  {
            steps {
                dir("openc910") {
                    sh "python3 /eda/processor_ci/core/labeler_prototype.py -d \$(pwd) -c /eda/processor_ci/config.json -o  /jenkins/processor_ci_utils/labels"
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
                                dir("openc910") {
                                    echo 'Starting synthesis for FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p openc910 -b colorlight_i9'
                                }
                            }
                        }
                        stage('Flash colorlight_i9') {
                            steps {
                                dir("openc910") {
                                    echo 'Flashing FPGA colorlight_i9.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p openc910 -b colorlight_i9 -l'
                                }
                            }
                        }
                        stage('Test colorlight_i9') {
                            steps {
                                echo 'Testing FPGA colorlight_i9.'
                                dir("openc910") {
                                    sh 'echo "Test for FPGA in /dev/ttyACM0"'
                                    sh 'python3 /eda/processor_ci_tests/test_runner/run.py --config                                    /eda/processor_ci_tests/test_runner/config.json --port /dev/ttyACM0'
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
                                dir("openc910") {
                                    echo 'Starting synthesis for FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p openc910 -b digilent_arty_a7_100t'
                                }
                            }
                        }
                        stage('Flash digilent_arty_a7_100t') {
                            steps {
                                dir("openc910") {
                                    echo 'Flashing FPGA digilent_arty_a7_100t.'
                                sh 'python3 /eda/processor_ci/main.py -c /eda/processor_ci/config.json \
                                            -p openc910 -b digilent_arty_a7_100t -l'
                                }
                            }
                        }
                        stage('Test digilent_arty_a7_100t') {
                            steps {
                                echo 'Testing FPGA digilent_arty_a7_100t.'
                                dir("openc910") {
                                    sh 'echo "Test for FPGA in /dev/ttyUSB1"'
                                    sh 'python3 /eda/processor_ci_tests/test_runner/run.py --config                                    /eda/processor_ci_tests/test_runner/config.json --port /dev/ttyUSB1'
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
