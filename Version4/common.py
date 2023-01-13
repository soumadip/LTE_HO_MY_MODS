#!/usr/bin/python

import sys
import os
import my_modules .my_tracing as debugging
debugging .trace .min_level = 0
debugging .log .DEBUG = True
import my_modules .my_io as io
import my_modules .load_balance_algo_modules as lba_mod
import my_modules .handover_algo_modules as hoa_mod
import my_modules .stat_calculator_modules as sc_mod
import my_modules .connection_status_modules as cs_mod
import my_modules .handover_process_modules as hp_mod
import my_modules .measurement_provider_modules as mp_mod
import my_modules .position_provider_modules as pp_mod


class SimulatorModule :
    def __init__ (  self, all_conf_file = ""):
        #load all config
        self .all_config = io .load_json_config (all_conf_file)
        
        #segregation of configs
        self .common_config = self .all_config ['common_configs']
        self .ho_config = self .all_config [self .common_config ['ho_algo'] + self .all_config ['ho_conf']]
        self .lb_config = self .all_config [self .common_config ['lb_algo'] + self .all_config ['lb_conf']]

        #identify source directory for data and data_file_names
        self .source_dir = self .all_config ['context']
        self .data_file_names = self .all_config ['processed_data']
        #load the necessary data from source directory
        self .ue_pos = io .read_from_file_basic (self .source_dir, self .data_file_names ['ue_pos'])
        self .enb_pos = io .read_from_file_basic (self .source_dir, self .data_file_names ['enb_pos'])
        self .rsrp_meas = io .read_from_file_basic (self .source_dir, self .data_file_names ['rsrp_meas'])
        self .rsrq_meas = io .read_from_file_basic (self .source_dir, self .data_file_names ['rsrq_meas'])
        self .ue_start_times = io .read_from_file_basic (self .source_dir, self .all_config ['ue_start_times_prefix'] +
                                                                                    str (self .common_config ['number_ue']) + '_' +
                                                                                    str (self .all_config ['ue_start_times_set_no']) +
                                                                                    self .all_config ['ue_start_times_suffix'])
        #ue start_times generator -- 
            #{i+1:int (random .random () * (self .duration - self .journey_length)) for i in range (self .common_config ['number_ue'])}

        self .duration = int (self .common_config ['duration'])

        self .set_of_enbs = None
        self .set_of_ues = None

        self .handover_module = None
        self .load_module = None
        self .enbcs_module = None
        self .uecs_module = None
        self .he_module = None
        self .sc_module = None
        self .rsrpmp_module = None
        self .rsrqmp_module = None

    def __enter__ (self):
        debugging .log ("__enter__ Simulator Module")
        return self

    def __exit__ (self, exception_type, exception_value, traceback):
        debugging .log ("__exit__ Simulator Module")

    @debugging .trace (level = 4)
    def check_lba_status (self, t, indicator):
        high_load_enbs = [e for e in self .set_of_enbs 
                                if len (self .enbcs_module .get_ues_under_enb (e, t)) > self .lb_config ['beta']]
        enbs_in_use = [e for e in self .set_of_enbs
                                if len (self .enbcs_module .get_ues_under_enb (e, t)) != 0]
        #update stats
        if indicator == 'before' :
            self .sc_module .update_stat_lba_before (t, (high_load_enbs, enbs_in_use))
        elif indicator == 'after' :
            self .sc_module .update_stat_lba_after (t, (high_load_enbs, enbs_in_use))

        return ' ' .join (["#High load:", str (len (high_load_enbs)), "#Total in Use:", str (len (enbs_in_use))])

    @debugging .trace (level = 2)
    def simulate_at_time (self, t_now):
        self .he_module .initialize_connection_status_for_time (t_now)

        for ue in self .set_of_ues :
            debugging .log ("Time", t_now, "UE", ue)
            if t_now < self .ue_start_times [ue] or t_now > (self .ue_start_times [ue] + self .common_config ['journey_length']):
                #skip as journey is not yet started or journey has finished
                debugging .log("Ignoring UE", ue, "at time", t_now, "as journey start time is", self .ue_start_times [ue])
                continue

            elif t_now == (self .ue_start_times [ue] + self .common_config ['journey_length']) :
                #clean up UE from the system as the journey has ended
                self .he_module .execute_handover (t_now, ue, self .uecs_module .get_serving_enb_of (ue, t_now), -1)
                continue
            
            serving = self .uecs_module .get_serving_enb_of (ue, t_now)
            if serving == -1 and self .lb_config ['name'] == 'jula':
                self .load_module .new_join (ue)

            if self .ho_config ['name'] != 'none':
                #engage handover module
                (time, ue, src, dst) = self .handover_module .run (t_now, ue, serving)

                #Process handover module output
                if (src != -1) and (dst != -1):
                    #update stats
                    rsrp, dbm = self .rsrpmp_module .get_reading_for (ue, t_now, dst)
                    self .sc_module .update_stat_connection (t_now, ue, (src, dst, rsrp, dbm))

                self .he_module .execute_handover (t_now, ue, src, dst)

        if t_now != 0 and t_now % self .common_config ['load_check_interval'] == 0:
            debugging .log ("Time", t_now, ":Checking system load status")
            debugging .log ("STAT: Time", t_now, "[Before]", self .check_lba_status (t_now, 'before'))

            #engage load balancing module
            if self .lb_config ['name'] == 'greedy':
                lba_transfers = self .load_module .run (t_now, self .enbcs_module .get_enb_connection_status_at (t_now))
            elif self .lb_config ['name'] in ['maxflow', 'jula', 'uara', 'dlba', 'none'] :
                lba_transfers = self .load_module .run (t_now)

            #process load module outputs
            debugging .log ("Executing LBA transfers as follows", lba_transfers)
            for t, u, s, d in lba_transfers :
                self .he_module .execute_handover (t, u, s, d)

                #update stats
                rsrp, dbm = self .rsrpmp_module .get_reading_for (u, t, d)
                self .sc_module .update_stat_lba_connection (t, u, (s, d, rsrp, dbm))
                self .sc_module .update_stat_connection (t, u, (s, d, rsrp, dbm))

            debugging .log ("STAT: Time", t_now, "[After]", self .check_lba_status (t_now, 'after'))
            debugging .log ("STAT: Total number of handovers due to balancing", len (lba_transfers))

        #timely connection status update
        debugging .log ("Time", t_now, "UE connection status")
        ue_cs = self .uecs_module .get_ue_connection_status_at (t_now)
        for k in filter (lambda x: ue_cs [x] != -1, ue_cs) :
            debugging .log ("UE", k, "is connected to eNB", ue_cs [k])
    
        enb_cs = self .enbcs_module .get_enb_connection_status_at (t_now)
        debugging .log ("Time", t_now, "eNB connection status")
        for k in filter (lambda x : bool (enb_cs [x]), enb_cs) :
            debugging .log ("eNB", k, "has UEs", enb_cs [k])

    @debugging .trace (level = 2)
    def simulate (self):
        for t in range (self .duration):
            debugging .log ("Simulating for time", t)
            debugging .progress ("Simulating for time", t)
            self .simulate_at_time (t)

    @debugging .trace (level = 2)
    def configure (self):
        #position provider modules
        self .uepp_module = pp_mod .UEPositionProviderModule (self .common_config, self .ue_start_times, self .ue_pos)
        self .enbpp_module = pp_mod .eNBPositionProviderModule (self .enb_pos)
        
        #measurement provider module
        self .rsrpmp_module = mp_mod .RSRPMeasurementProviderModule (   self .rsrp_meas,
                                                                        self .enbpp_module, 
                                                                        self .uepp_module,
                                                                        self .common_config ['lambda'])
        self .rsrqmp_module = mp_mod .RSRQMeasurementProviderModule (   self .rsrq_meas,
                                                                        self .enbpp_module,
                                                                        self .uepp_module,
                                                                        self .common_config ['lambda'])

        #inititalize set of ues and set of enbs
        self .set_of_ues = self .uepp_module .get_set_of_ues ()
        self .set_of_enbs = self .enbpp_module .get_set_of_enbs ()

        #connection status modules
        self .uecs_module = cs_mod .UEConnectionStatusModule (self .set_of_ues)
        self .enbcs_module = cs_mod .eNBConnectionStatusModule (self .set_of_enbs)

        #handover execution module
        self .he_module = hp_mod .HandoverExecutionModule (self .uecs_module, self .enbcs_module)
        
        #setup hadnover module
        self .choose_handover_module ()

        #setup load module
        self .choose_load_module ()

        #stat calculator module
        self .sc_module = sc_mod .StatCalculatorModule ( self .set_of_ues, 
                                                         self .duration,
                                                         self .common_config)

    @debugging .trace (level = 1)
    def choose_handover_module (self):
        if self .ho_config ['name'] == 'ussl-a' or self .ho_config ['name'] == 'ussl-c':
            debugging .log ("UEASHandoverModule is chosen for the codename --", self .ho_config ['name'])
            self .handover_module = hoa_mod .UEASHandoverModule (   self .ho_config, 
                                                                    self .common_config,
                                                                    uepp_obj = self .uepp_module,
                                                                    rsrpmp_obj = self .rsrpmp_module)
        elif self .ho_config ['name'] == 'a3' :
            debugging .log ("A3HandoverModule is chosen for the codename --", self .ho_config ['name'])
            self .handover_module = hoa_mod .A3HandoverModule (     self .ho_config, self .common_config, 
                                                                    uepp_obj = self .uepp_module,
                                                                    rsrpmp_obj = self .rsrpmp_module)
        elif self .ho_config ['name'] == 'ombfra' :
            debugging .log ("OMBFRAHandoverModule is chosen for the codename --", self .ho_config ['name'])
            self .handover_module = hoa_mod .OMBFRAHandoverModule ( self .ho_config, self .common_config,
                                                                    uepp_obj = self .uepp_module,
                                                                    enbpp_obj = self .enbpp_module,
                                                                    enbcs_obj = self .enbcs_module,
                                                                    rsrpmp_obj = self .rsrpmp_module)
        elif self .ho_config ['name'] == 'ubbho' :
            debugging .log ("UBBHOHandoverModule is chosen for the codename --", self .ho_config ['name'])
            self .handover_module = hoa_mod .UBBHOHandoverModule (  self .ho_config, self .common_config,
                                                                    uepp_obj = self .uepp_module,
                                                                    enbpp_obj = self .enbpp_module,
                                                                    rsrpmp_obj = self .rsrpmp_module)
        elif self .ho_config ['name'] == 'a2a4' :
            debugging .log ("A2A4HandoverModule is chosen for the codename --", self .ho_config ['name'])
            self .handover_module = hoa_mod .A2A4HandoverModule (   self .ho_config, self .common_config,
                                                                    uepp_obj = self .uepp_module,
                                                                    rsrqmp_obj = self .rsrqmp_module)
        elif self .ho_config ['name'] == 'attach' :
            debugging .log ("AttachUEModule is chosen for the codename --", self .ho_config ['name'])
            self .handover_module = hoa_mod .AttachUEModule (       self .ho_config, self .common_config,
                                                                    uepp_obj = self .uepp_module,
                                                                    rsrpmp_obj = self .rsrpmp_module)
        elif self .ho_config ['name'] == 'none' :
            debugging .log ("NoHandoverModule is chosen for the codename --", self .ho_config ['name'])
            self .handover_module = hoa_mod .NoHandoverModule (  self .ho_config, self .common_config)
        else :
            debugging .log("No handover module found for the codename --", ho_config ['name'])
            exit (0)

    @debugging .trace (level = 1)
    def choose_load_module (self) :
        if self .lb_config ['name'] == 'none' :
            debugging .log ("NoLoadModule is chosen for the codename --", self .lb_config ['name'])
            self .load_module = lba_mod .NoLoadModule (                 self .lb_config, self .common_config)
        elif self .lb_config ['name'] == 'greedy' :
            debugging .log ("GreedyLoadModule is chosen for the codename --", self .lb_config ['name'])
            self .load_module = lba_mod .GreedyLoadModule (             self .lb_config, self .common_config, 
                                                                        ues = self .set_of_ues, 
                                                                        enbs = self .set_of_enbs, 
                                                                        start_times = self .ue_start_times, 
                                                                        meas_data = self .rsrp_meas)
        elif self .lb_config ['name'] == 'maxflow' :
            debugging .log ("NetworkFlowBasedLoadModule is chosen for the codename --", self .lb_config ['name'])
            self .load_module = lba_mod .NetworkFlowBasedLoadModule (   self .lb_config, self .common_config, 
                                                                        rsrpmp_obj = self .rsrpmp_module, 
                                                                        uecs_obj = self .uecs_module, 
                                                                        enbcs_obj = self .enbcs_module)
        elif self .lb_config ['name'] == 'jula' :
            debugging .log ("JointUEASLoadModule is chosen for the codename --", self .lb_config ['name'])
            self .load_module = lba_mod .JointUEASLoadModule (   self .lb_config, self .common_config, 
                                                                        uepp_obj = self .uepp_module,
                                                                        rsrpmp_obj = self .rsrpmp_module, 
                                                                        uecs_obj = self .uecs_module, 
                                                                        enbcs_obj = self .enbcs_module)
        elif self .lb_config ['name'] == 'dlba' :
            debugging .log ("Cmp1LoadModule is chosen for the codename --", self .lb_config ['name'])
            self .load_module = lba_mod .Cmp1LoadModule (   self .lb_config, self .common_config, 
                                                                        uepp_obj = self .uepp_module,
                                                                        rsrpmp_obj = self .rsrpmp_module, 
                                                                        uecs_obj = self .uecs_module, 
                                                                        enbcs_obj = self .enbcs_module)
        elif self .lb_config ['name'] == 'uara' :
            debugging .log ("Cmp2LoadModule is chosen for the codename --", self .lb_config ['name'])
            self .load_module = lba_mod .Cmp2LoadModule (   self .lb_config, self .common_config, 
                                                                        uepp_obj = self .uepp_module,
                                                                        rsrpmp_obj = self .rsrpmp_module, 
                                                                        uecs_obj = self .uecs_module, 
                                                                        enbcs_obj = self .enbcs_module)
        else :
            debugging .log ("No load module found for the codename --", self .lb_config ['name'])
            exit (0)

    @debugging .trace (level = 1)
    def run (self, save_output = False):
        fname_prefix = '_' .join ([ self .ho_config ['name'], 
                                    self .lb_config ['name'], 
                                    'a' + (str (self .lb_config ['alpha'] * 100) if 'alpha' in self .lb_config else '0'), 
                                    'b' + (str (self .lb_config ['beta']) if 'beta' in self .lb_config else '0'),
                                    'g' + (str (self .lb_config ['gamma']) if 'gamma' in self .lb_config else '0'),
                                    'p' + str (self .common_config ['load_check_interval']),
                                    'u' + str (self .common_config ['number_ue'])])

        if save_output :
            fname_prefix = sys .argv [2] + '_' + fname_prefix
            outdir = '/' .join ([self .source_dir, fname_prefix, "V4"])
            if not os .path .exists (outdir):
                debugging .progress ("Creating output directory", outdir)
                os .makedirs (outdir)
            else :
                debugging .progress ("Directory", outdir, "already exists, using that as output directory")

            debug_fname = '/' .join ([outdir, fname_prefix + '.debug'])
            debugging .progress ("Opening file", debug_fname, "as stdout")
            backup = sys .stdout
            sys .stdout = open (debug_fname, 'w') 
            
        self .configure ()
        self .simulate ()
        self .sc_module .display ()

        if save_output :
            out_file_names = self .sc_module .save (outdir, fname_prefix)
            sys .stdout .close()
            sys .stdout = backup
            debugging .progress ("Write complete")

            debugging .progress ("Output filenames")
            for fname in out_file_names: 
                debugging .progress (fname)

            #plot related code
            import my_modules .plot_modules as pl_mod
            with pl_mod .PlotModule (debug_fname) as pm :
                if self .lb_config ['name'] != 'none':
                    debugging .progress ("Plotting the data")
                    pm .plot_bar_with_noLBAcase (debug_fname, debug_fname 
                                                                .replace (self .lb_config ['name'], "none") 
                                                                .replace ("a" + str (self .lb_config ['alpha'] * 100), "a0.0"))
                    pm .save_as ()
                    debugging .progress ("Plotting done")
                pm .show_stats (debug_fname)
                


if __name__ == '__main__':
    debugging .progress ("Simlulation program has started")

    savefile_flag = True if len (sys .argv) == 3 else False

    with SimulatorModule (all_conf_file = sys .argv [1]) as sim:
        sim .run (save_output = savefile_flag)
    
    debugging .progress ("Simulation program has finished")

#python % <common config> <ho config> <lb config"
