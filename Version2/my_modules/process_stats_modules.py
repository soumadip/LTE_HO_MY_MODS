
import numpy as np
import my_modules .my_tracing as debugging
import my_modules .my_io as io


class ProcessStatsModule :
    def __init__ (self, fname) :
        self .fname = fname

    def __enter__ (self) :
        debugging .log ("Enter: ProcessStatsModule")
        debugging .log ("Configuring with", self .fname)
        self .connection = io .pickle_load (self .fname + '.connection')
        self .lba_connection = io .pickle_load (self .fname + '.lba_connection')
        self .lba_before = io .pickle_load (self .fname + '.lba_before')
        self .lba_after = io .pickle_load (self .fname + '.lba_after')
        self .set_of_ues = self .extract_ues ()
        self .duration = self .extract_duration ()
        self .set_of_used_enbs = self .extract_enbs ()
        self .sst_threshold = -90
        self .lambda_threshold = -85
        self .journey_length = 108
        self .win_size = 4
        return self

    def __exit__ (self, exception_type, exception_value, traceback) :
        debugging .log ("Exit: ProcessStatsModule for", self .fname)

    @debugging .trace (level = 1)
    def extract_duration (self) :
        return len (self .connection)

    @debugging .trace (level = 1)
    def extract_enbs (self) :
        all_used_enbs = set ([])
        for t in self .connection :
            for ue in self .connection [t]:
                if self .connection [t] [ue] != -1:
                    enb1, enb2, _, _ = self .connection [t] [ue]
                    all_used_enbs .add (enb1)
                    all_used_enbs .add (enb2)
        return all_used_enbs

    @debugging .trace (level = 1)
    def extract_ues (self):
        all_ues = set ([])
        for t in self .connection :
            for ue in self .connection [t] :
                all_ues .add (ue)
        return all_ues

    @debugging .trace (level = 1)
    def parse_connection (self, time_range) :
        enb_connections ={}
        ue_handover_count = {ue : 0 for ue in self .set_of_ues}
        for t in self .connection :
            if t in range (time_range [0], time_range [1]) :
                enb_connections [t] = {}
                for ue in self .connection [t]:
                    if self .connection [t] [ue] != -1:
                        src, dst, _, _ = self .connection [t] [ue]
                        if dst in enb_connections [t]:
                            enb_connections [t] [dst] += [ue]
                        else :
                            enb_connections [t] [dst] = [ue]
            for ue in self .connection [t]:
                if self .connection [t] [ue] != -1:
                    ue_handover_count [ue] += 1
        return enb_connections, ue_handover_count

    @debugging .trace (level = 1)
    def parse_lba_connection (self, time_range) :
        enb_lba_connections ={}
        for t in self .lba_connection :
            if t in range (time_range [0], time_range [1]) :
                enb_lba_connections [t] = {}
                for ue in self .lba_connection [t]:
                    if self .lba_connection [t] [ue] != -1:
                        src, dst, _, _ = self .lba_connection [t] [ue]
                        if dst in enb_lba_connections [t]:
                            enb_lba_connections [t] [dst] += [ue]
                        else :
                            enb_lba_connections [t] [dst] = [ue]
        return enb_lba_connections

    @debugging .trace (level = 2)
    def get_enb_loads (self, time) :
        ret = {}
        for ue in self .connection [time] :
            if self .connection [time] [ue] != -1 :
                _, enb, _, _ = self .connection [time] [ue]
                if enb not in ret:
                    ret [enb] = 1
                else :
                    ret [enb] += 1
        return ret

    @debugging .trace (level = 2)
    def get_high_load_percentages (self, beta = 5) :
        xv = [i for i in range (self .duration)]
        yv = []
        for t in xv :
            enb_load = self .get_enb_loads (t)
            print (enb_load)
            in_use = len ([enb for enb in enb_load if enb_load [enb] > 0])
            high_load = len ([enb for enb in enb_load if enb_load [enb] > beta])
            if in_use :
                yv .append (100 * high_load / in_use)
            else :
                yv .append (0)

        return xv, yv

    @debugging .trace (level = 1)
    def parse_lba_before (self) :
        x_vals = np .array (list (self .lba_before .keys()))
        y_vals_high_load_enb = np .array ([len (self .lba_before [k] [0]) for k in self .lba_before])
        y_vals_enb_in_use = np .array ([len (self .lba_before [k] [1]) for k in self .lba_before])
        debugging .log ("x_vals", x_vals)
        debugging .log ("y_vals", y_vals_high_load_enb)
        debugging .log ("y_vals", y_vals_enb_in_use)
        return (x_vals, y_vals_high_load_enb, y_vals_enb_in_use) 

    @debugging .trace (level = 1)
    def parse_lba_after (self) :
        x_vals = np .array (list (self .lba_after .keys()))
        y_vals_high_load_enb = np .array ([len (self .lba_after [k] [0]) for k in self .lba_after])
        y_vals_enb_in_use = np .array ([len (self .lba_after [k] [1]) for k in self .lba_after])
        debugging .log ("x_vals", x_vals)
        debugging .log ("y_vals", y_vals_high_load_enb)
        debugging .log ("y_vals", y_vals_enb_in_use)
        return (x_vals, y_vals_high_load_enb, y_vals_enb_in_use) 

    @debugging .trace (level = 1)
    def parse_LSRL (self, lambda_threshold = -85) :
        lsrl_dict = {}
        for ue in self .set_of_ues :
            lsrl_dict [ue] = self .LSRL_counter (ue, lambda_threshold)
            if lsrl_dict [ue] == []:
                lsrl_dict [ue] = [(0, 0)]
        return lsrl_dict

    @debugging .trace (level = 2)
    def get_alpha_vals (self, alpha, times) :
        ec, uc = self .parse_connection ([0,150])
        ret = []
        for t in times :
            ret .append (alpha * len (ec [t]) / 100)
        return ret

    @debugging .trace (level = 2)
    def ping_pong_counter (self, ue) : 
        ue_timed_connections = []
        for t in range (self .duration) :
            if self .connection [t] [ue] != -1 :
                ue_timed_connections.append (self .connection [t] [ue] [1])
            else :
                ue_timed_connections .append (-1)
        return self .count_ping_pong (ue_timed_connections, self .win_size)

    @debugging .trace (level = 2)
    def wrong_ho_counter (self, ue) : 
        ue_timed_connections = []
        for t in range (self .duration) :
            if self .connection [t] [ue] != -1 :
                ue_timed_connections.append (self .connection [t] [ue] [1])
            else :
                ue_timed_connections .append (-1)
        return self .count_wrong_ho (ue_timed_connections, self .win_size)

    @debugging .trace (level = 2)
    def handover_counter (self, ue) : 
        ue_timed_connections = []
        for t in range (self .duration) :
            if self .connection [t] [ue] != -1 :
                ue_timed_connections.append (self .connection [t] [ue] [1])
            else :
                ue_timed_connections .append (-1)
        return self .count_handovers (ue_timed_connections)

    @debugging .trace (level = 2)
    def LSRL_counter (self, ue): 
        ue_timed_signals = []
        for t in range (self .duration) :
            if self .connection [t] [ue] != -1 :
                ue_timed_signals .append (self .connection [t] [ue] [3])
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
    def count_ping_pong (self, ue_connections_list, win_size):
        ueas = list (filter (lambda x: x != -1, ue_connections_list))
        pp_count = 0
        for i in range (len (ueas) - win_size) :
            window = ueas [i : i + win_size]
            if self .is_ping_pong (window) :
                pp_count += 1
        return pp_count

    @debugging .trace (level = 2)
    def count_wrong_ho (self, ue_connections_list, win_size):
        ueas = list (filter (lambda x: x != -1, ue_connections_list))
        wh_count = 0
        for i in range (len (ueas) - win_size) :
            window = ueas [i : i + win_size]
            if self .is_wrong_ho (window) :
                wh_count += 1
        return wh_count

    @debugging .trace (level = 3)
    def is_ping_pong (self, window) :
        for i in range (len (window) - 1):
            if window [i] != window [i + 1]:
                if window [i] in window [i + 1 :] :
                    return True
        return False

    @debugging .trace (level = 3)
    def is_wrong_ho (self, window) :
        if len (set (window)) > 2:
            return True
        else :
            return False
        
    @debugging .trace (level = 2)
    def load_handover_counter (self, ue) :
        ue_timed_connections = []
        for t in range (self .duration) :
            if self .lba_connection [t] [ue] != -1 :
                ue_timed_connections.append (self .lba_connection [t] [ue] [1])
            else :
                ue_timed_connections .append (-1)
        return self .count_handovers (ue_timed_connections)

    @debugging .trace (level =2)
    def display (self) :
        #Handovers Journal
        total_ho = 0
        total_ho_lba = 0
        for t in range (self .duration) :
            for ue in self .set_of_ues :
                if self .connection [t] [ue] != -1:
                    src, dst, dst_rsrp, dst_dbm = self .connection [t] [ue]
                    print ("[HO] Time", t, "UE", ue, "handover from", src, "to", dst, "with", dst_dbm, "dBm strength")
                    if src != dst:
                        total_ho += 1
                if self .lba_connection [t] [ue] != -1:
                    src, dst, dst_rsrp, dst_dbm = self .lba_connection [t] [ue]
                    print ("[LBA] Time", t, "UE", ue, "handover from", src, "to", dst, "with", dst_dbm, "dBm strength")
                    total_ho_lba += 1
        
        #LSRL values
        lsrl_per_ue = {}
        for ue in self .set_of_ues :
            lsrl = self .LSRL_counter (ue)
            lsrl_per_ue [ue] = sum ([d * c for d,c in lsrl])
            print ("UE :", ue, "LSRL_count :", lsrl, "Handover count :", self .handover_counter (ue))

        #LBA stats
        for t in self .lba_before :
            print ("[Before]", "Time", t, 
                        "high_load_count", len (self .lba_before [t] [0]), 
                        "low_load_count", len (self .lba_before [t] [1]))
            if t in self .lba_after :
                print ("[After]", "Time", t, 
                            "high_load_count", len (self .lba_after [t] [0]), 
                            "low_load_count", len (self .lba_after [t] [1]))

        print ("Normal Handovers per UE [Avg]", total_ho / len (self .set_of_ues))
        print ("LBA Handovers per UE [Avg]", total_ho_lba / len (self .set_of_ues))
        ho_stat = [self .handover_counter (ue) for ue in self .set_of_ues]
        print ("Handovers [Max/ Min/ Avg]", max (ho_stat), min (ho_stat), round (sum (ho_stat) / len (ho_stat), 4))
        lsrl_stat = [round (l / self .journey_length, 4) * 100 for l in lsrl_per_ue .values ()]
        print ("LSRL [Max/ Min/ Avg]", max (lsrl_stat), min (lsrl_stat), round (sum (lsrl_stat) / len (lsrl_stat), 4))
        pp_stat = [self .ping_pong_counter (ue) for ue in self .set_of_ues]
        print ("Ping-pong Handovers [Max/ Min/ Avg]", max (pp_stat), min (pp_stat), round (sum (pp_stat) / len (pp_stat), 4))
        wh_stat = [self .wrong_ho_counter (ue) for ue in self .set_of_ues]
        print ("Wrong Handovers [Max/ Min/ Avg]", max (wh_stat), min (wh_stat), round (sum (wh_stat) / len (wh_stat), 4))


if __name__ == "__main__" :
    debugging .log ("Process Stat Module")


