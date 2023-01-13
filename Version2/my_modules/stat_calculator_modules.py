import my_modules .my_tracing as debugging
import my_modules .my_io as io

class StatCalculatorModule :
    def __init__ (self, set_of_ues, duration, common_config) :
        self .lambda_threshold = common_config ['lambda']
        self .sst_threshold = common_config ['sst_th']
        self .journey_length = common_config ['journey_length']
        self .set_of_ues = set_of_ues
        self .duration = duration
        self .stat_connection = {t:{ue:-1 for ue in self .set_of_ues} for t in range (self .duration)}
        self .stat_lba_connection = {t:{ue:-1 for ue in self .set_of_ues} for t in range (self .duration)}
        self .stat_lba_before = {}
        self .stat_lba_after = {}

    @debugging .trace (level =2)
    def display (self) :
        #Handovers Journal
        total_ho = 0
        total_ho_lba = 0
        for t in range (self .duration) :
            for ue in self .set_of_ues :
                if self .stat_connection [t] [ue] != -1:
                    src, dst, dst_rsrp, dst_dbm = self .stat_connection [t] [ue]
                    print ("[HO] Time", t, "UE", ue, "handover from", src, "to", dst, "with", dst_dbm, "dBm strength")
                    if src != dst:
                        total_ho += 1
                if self .stat_lba_connection [t] [ue] != -1:
                    src, dst, dst_rsrp, dst_dbm = self .stat_lba_connection [t] [ue]
                    print ("[LBA] Time", t, "UE", ue, "handover from", src, "to", dst, "with", dst_dbm, "dBm strength")
                    total_ho_lba += 1
        
        #LSRL values
        lsrl_per_ue = {}
        for ue in self .set_of_ues :
            lsrl = self .LSRL_counter (ue)
            lsrl_per_ue [ue] = sum ([d * c for d,c in lsrl])
            print ("UE :", ue, "LSRL_count :", lsrl, "Handover count :", self .handover_counter (ue))

        #LBA stats
        for t in self .stat_lba_before :
            print ("[Before]", "Time", t, 
                        "high_load_count", len (self .stat_lba_before [t] [0]), 
                        "low_load_count", len (self .stat_lba_before [t] [1]))
            if t in self .stat_lba_after :
                print ("[After]", "Time", t, 
                            "high_load_count", len (self .stat_lba_after [t] [0]), 
                            "low_load_count", len (self .stat_lba_after [t] [1]))
        #fairness = {}
        #for t in self .lba_stat_connection :
        #    distribution = {len (}

        print ("Normal Handovers per UE [Avg]", total_ho / len (self .set_of_ues))
        print ("LBA Handovers per UE [Avg]", total_ho_lba / len (self .set_of_ues))
        ho_stat = [self .handover_counter (ue) for ue in self .set_of_ues]
        print ("Handovers [Max/ Min/ Avg]", max (ho_stat), min (ho_stat), round (sum (ho_stat) / len (ho_stat), 4))
        lsrl_stat = [round (l / self .journey_length, 4) * 100 for l in lsrl_per_ue .values ()]
        print ("LSRL [Max/ Min/ Avg]", max (lsrl_stat), min (lsrl_stat), round (sum (lsrl_stat) / len (lsrl_stat), 4))

    @debugging .trace (level = 1)
    def save (self, outdir, prefix):
        outfilenames = []

        for suffix, obj in zip (["connection", "lba_connection", "lba_before", "lba_after"], 
                                [self .stat_connection, self .stat_lba_connection, self .stat_lba_before, self .stat_lba_after]):
            outfile =  '/' .join ([outdir, prefix + '.' + suffix])
            debugging .progress ("Writing to file", outfile)
            io .pickle_dump (obj, outfile)
            debugging .progress ("Write complete")
            outfilenames .append (outfile)

        return outfilenames

    @debugging .trace (level = 1)
    def update_stat_lba_before (self ,t, val): #val (high_load_enb_list, in_use_enb_list)
        self .stat_lba_before [t] = io .deep_copy (val)

    @debugging .trace (level = 1)
    def update_stat_lba_after (self, t, val):
        self .stat_lba_after [t] = io .deep_copy (val)

    @debugging .trace (level = 1)
    def update_stat_lba_connection (self, t, ue, val):
        self .stat_lba_connection [t] [ue] = io .deep_copy (val)

    @debugging .trace (level = 1)
    def update_stat_connection (self, t, ue, val):
        self .stat_connection [t] [ue] = io .deep_copy (val)

    @debugging .trace (level = 2)
    def handover_counter (self, ue) : 
        ue_timed_connections = []
        for t in range (self .duration) :
            if self .stat_connection [t] [ue] != -1 :
                ue_timed_connections.append (self .stat_connection [t] [ue] [1])
            else :
                ue_timed_connections .append (-1)
        return self .count_handovers (ue_timed_connections)

    @debugging .trace (level = 2)
    def LSRL_counter (self, ue): 
        ue_timed_signals = []
        for t in range (self .duration) :
            if self .stat_connection [t] [ue] != -1 :
                ue_timed_signals .append (self .stat_connection [t] [ue] [3])
            else :
                ue_timed_signals .append (-1)
        return self .count_LSRL (ue_timed_signals)

    @debugging .trace (level = 3)
    def count_handovers (self, ue_connections_list):
        ue_connections = list (filter (lambda x: x != -1, ue_connections_list))
        ho_count = 0
        for e, e_nxt in zip (ue_connections, ue_connections [1:]) :
            if e != e_nxt:
                ho_count += 1
        return ho_count

    @debugging .trace (level = 2)
    def count_LSRL (self, ue_signals_list):
        ue_signals = list (filter (lambda x: x != -1, ue_signals_list))
        print (ue_signals)
        lsrl_dict = {}
        current_lsrl = 0
        for v in ue_signals :
            if v < self .sst_threshold :
                current_lsrl += 1
            elif current_lsrl :
                if current_lsrl not in lsrl_dict:
                    lsrl_dict [current_lsrl] = 1
                else :
                    lsrl_dict [current_lsrl] += 1
                current_lsrl = 0
        return list (lsrl_dict .items ()) #[(lsrl, count), ...]

    @debugging .trace (level = 2)
    def load_handover_counter (self, ue) :
        ue_timed_connections = []
        for t in range (self .duration) :
            if self .stat_lba_connection [t] [ue] != -1 :
                ue_timed_connections.append (self .stat_lba_connection [t] [ue] [1])
            else :
                ue_timed_connections .append (-1)
        return self .count_handovers (ue_timed_connections)


if __name__ == '__main__':
    debugging .log ("StatCounterModule")
