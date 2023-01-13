#!/usr/bin/pytgon
import sys
import random
import math
import networkx as nx
import itertools as it
import my_modules .my_tracing as debugging
import my_modules .my_io as io

class UEASHandoverModule:
    def __init__ (self, ho_config, common_config, uepp_obj, rsrpmp_obj):
        debugging .log ("Initializing object", ho_config ['full_name'], "for class UEASHandoverModule")

        self .journey_length = common_config ['journey_length']
        self .lambda_threshold = common_config ['lambda']
        self .sst_threshold = common_config ['sst_th']

        self .name = ho_config ['name']
        self .lsrl_threshold = ho_config ['lsrl']
        self .USSL = ho_config ['USSL']

        self .uepp_module = uepp_obj
        self .rsrpmp_module = rsrpmp_obj 
        
        self .ue_LSRL_data = {ue:{} for ue in self .uepp_module .get_set_of_ues ()}


    @debugging .trace (level = 4)
    def encode_node (self, c_and_p, t):
        c, p = c_and_p
        return int (t * 1e7 + int (p) * 1e4 + c)

    @debugging .trace (level = 4)
    def decode_node (self, n):
        t = int (n / 1e7)
        n = int (n % 1e7)
        p = int (n / 1e4)
        c = int (n % 1e4)
        return (t, c, p)

    @debugging .trace (level = 2)
    def construct_graph_from (self, timed_meas_data):
        G = nx .DiGraph()
        weighted_edges = []
        time_sequence = sorted (timed_meas_data .keys ())

        for tA, tB in zip (time_sequence, time_sequence [1:]):
            for x, y in it .product (timed_meas_data [tA], timed_meas_data [tB]):
                edge_weight = 1
                if x [0] == y [0]:
                    edge_weight = 0
                weighted_edges .append ((self .encode_node (x, tA), self .encode_node (y, tB), edge_weight))

        G .add_weighted_edges_from (weighted_edges)

        return (G, [self .encode_node (n, time_sequence [0]) for n in timed_meas_data [time_sequence [0]]], 
                        [self .encode_node (n, time_sequence [-1]) for n in timed_meas_data [time_sequence [-1]]])

    @debugging .trace (level = 2)
    def find_UEAS_from (self, G, src, dst):
        all_seq = []

        for s, d in it .product (src, dst):
            debugging .log ("finding path from", self .decode_node (s), "to", self .decode_node (d))
            path = nx .dijkstra_path (G, s, d)

            seq = []
            t, c, p = self .decode_node (path [0])
            seq .append ((t,c))
            for n1, n2 in zip (path, path[1:]):
                t1, c1, p1 = self .decode_node (n1)
                t2, c2, p2 = self .decode_node (n2)
                if c1 == c2 :
                    continue
                else : 
                    seq .append ((t2, c2))
            path_weight = nx .dijkstra_path_length (G, s, d)
            all_seq .append ((seq, path_weight))

        return [ueas for ueas in all_seq if ueas [1] == min (all_seq, key = lambda x: x[1]) [1]]

    @debugging .trace (level = 3)
    def check_LSRL_status (self, t_now, ue):
        if self .USSL == 'C':
            return True

        if self .uepp_module .get_ue_start_time (ue) > (t_now - self .lsrl_threshold + 1) or len (self .ue_LSRL_data [ue]) < self .lsrl_threshold:
            debugging .log ("LSRL check unnecessary for UE", ue, "at time", t_now)
            return True 

        elif any ([self .ue_LSRL_data [ue] [t + 1] >= self .lambda_threshold for t in range (t_now - self .lsrl_threshold, t_now, 1)]) :
            debugging .log ("LSRL length is shorter for UE", ue, "at time", t_now)
            return True
        
        else :
            debugging .log ("LSRL length exceeded for UE", ue, "at time", t_now)
            return False

    @debugging .trace (level = 2)
    def compute_next_handover_candidates (self, t_now, ue, src):
        meas_data = {}

        #mesurements at time t_now in ue_pos
        meas_data [t_now] = self .rsrpmp_module .measurement_report (t_now, ue, lambda_th = self .lambda_threshold)
        debugging .log ("Measurement report for UE", ue, "is", meas_data [t_now])

        if self .USSL == 'A':
            next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .predict_measurement_report (t_now + 1, ue, lambda_th = self .sst_threshold)]

        elif self .USSL == 'C':
            next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .measurement_report (t_now + 1, ue, lambda_th = self .lambda_threshold)]

        _, serving_signal_dBm = self .rsrpmp_module .get_reading_for (ue, t_now, src)

        self .ue_LSRL_data [ue] [t_now] = serving_signal_dBm

        if (src in next_meas_report and self .check_LSRL_status (t_now, ue)) or not bool (meas_data [t_now]):
            debugging .log ("No handover required, as serving eNB is having signal strength above required")
            return [src]

        #future measurements
        for t in range (t_now + 1, self .uepp_module .get_journey_end_time (ue) + 1, 1):
            if self .USSL == 'A':
                meas_data [t] = self .rsrpmp_module .predict_measurement_report (t, ue, lambda_th = self .lambda_threshold) 
                #print ('p', sorted(set ([c for c, _ in meas_data [t]])))
                #print ('a', sorted(set ([c for c, _ in self .rsrpmp_module .measurement_report (t, ue, lambda_th = self .lambda_threshold)])))
            elif self .USSL == 'C':
                meas_data [t] = self .rsrpmp_module .measurement_report (t, ue, lambda_th = self .lambda_threshold) 

            #delete empty measurement time instances
            if meas_data [t] == []:
                del meas_data [t]

        if len (meas_data) == 1:
            return [src]

        #create the graph
        G, src_set, dst_set = self .construct_graph_from (meas_data)

        #identify the possible ueas 
        possible_ueas = self .find_UEAS_from (G, src_set, dst_set)

        #identify the candidates
        candidates = [seq [0] [1] for seq, w in possible_ueas]

        return candidates

    @debugging .trace (level = 3)
    def dummy_load_score (self, type):
        if type == "random":
            score = random .uniform (0, 1)
        elif type == "simple":
            score = 1
        else : 
            score = float ('nan')
        return score

    @debugging .trace (level = 3)
    def choose_target (self, candidates):
        load_scores = {}
        debugging .log ("Choosing target from", candidates)
        for c in candidates:
            load_scores [c] = self .dummy_load_score ("random") #options: simple, random
        
        dst = min (load_scores, key = load_scores .get)
        return dst

    @debugging .trace (level = 1)
    def run (self, t_now, ue, serving):
        debugging .log ("Serving eNB for UE", ue, "is", serving, "and the ue position is", 
                                                                self .uepp_module .get_ue_position (ue, t_now), 
                                                                self .uepp_module .get_ue_position_XY (ue, t_now))

        candidates = self .compute_next_handover_candidates (t_now, ue, serving)
        target = self .choose_target (candidates)

        if target != serving :
            _, target_signal_dBm = self .rsrpmp_module .get_reading_for (ue, t_now, target)
            self .ue_LSRL_data [ue] .clear ()
            self .ue_LSRL_data [ue] [t_now] = target_signal_dBm

        return (t_now, ue, serving, target)



class AttachUEModule:
    def __init__ (self, ho_config, common_config, uepp_obj, rsrpmp_obj):
        debugging .log ("Initializing object", ho_config ['full_name'], "for class AttachUEModule")
        self .name = ho_config ['name']

        self .lambda_threshold = common_config ['lambda']

        self .uepp_module = uepp_obj
        self .rsrpmp_module = rsrpmp_obj

    @debugging .trace (level = 1)
    def run (self, time, ue, serving):
        debugging .log ("Serving eNB for UE", ue, "is", serving, "and the ue position is", 
                                                                self .uepp_module .get_ue_position (ue, time), 
                                                                self .uepp_module .get_ue_position_XY (ue, time))
        meas_report = self .rsrpmp_module .measurement_report(time, ue, lambda_th = self .lambda_threshold) 
        debugging .log ("Measurement report for UE", ue, "is", meas_report)
        
        if (not bool (meas_report)) or (serving != -1) :
            debugging .log ("Staying under serving eNB", serving)
            return (time, ue, serving, serving)

        if serving == -1 :
            target, rsrp =  max (meas_report, key = lambda x: x [1]) 
            debugging .log ("First-time-attach, to eNB", target, "with power", rsrp - 141, "dBm")
            return (time, ue, serving, target)



class A3HandoverModule :
    def __init__ (self, ho_config, common_config, uepp_obj, rsrpmp_obj):
        debugging .log ("Initializing object", ho_config ['full_name'], "for class A3HandoverModule")
        self .name = ho_config ['name']
        self .hom = ho_config ['hom']

        self .lambda_threshold = common_config ['lambda']

        self .uepp_module = uepp_obj
        self .rsrpmp_module = rsrpmp_obj

    @debugging .trace (level = 1)
    def run (self, time, ue, serving):
        debugging .log ("Serving eNB for UE", ue, "is", serving, "and the ue position is", 
                                                                self .uepp_module .get_ue_position (ue, time), 
                                                                self .uepp_module .get_ue_position_XY (ue, time))
        meas_report = self .rsrpmp_module .measurement_report(time, ue, lambda_th = self .lambda_threshold) 
        debugging .log ("Measurement report for UE", ue, "is", meas_report)
        
        if not bool (meas_report):
            debugging .log ("Measurment report is null, staying under serving eNB", serving)
            return (time, ue, serving, serving)

        if serving == -1 or serving not in [e for e, rsrp in meas_report] :
            target, rsrp =  max (meas_report, key = lambda x: x [1]) 
            debugging .log ("Inadequate signal strength from serving or first-time-attach, doing handover to eNB", target, "with power", rsrp - 141, "dBm")
            return (time, ue, serving, target)

        serving_rsrp = max ([rsrp for e, rsrp in meas_report if e == serving])
        debugging .log ("Signal strength of serving eNB", serving, "is", serving_rsrp)

        for candidate, rsrp in meas_report:
            if candidate == serving :
                continue

            if rsrp - serving_rsrp >= self .hom :
                debugging .log("Higher signal strength of", rsrp - 141, "dBm found for eNB", candidate)
                return (time, ue, serving, candidate)

        debugging .log ("No eNB with higher signal strength found, staying under serving")
        return (time, ue, serving, serving)



class A2A4HandoverModule:
    def __init__ (self, ho_config, common_config, uepp_obj, rsrqmp_obj):
        debugging .log ("Initializing object", ho_config ['full_name'], "for class A3HandoverModule")
        self .name = ho_config ['name']
        self .serving_cell_threshold = ho_config ['serving_th']

        self .lambda_threshold = common_config ['lambda']

        self .uepp_module = uepp_obj
        self .rsrqmp_module = rsrqmp_obj

        self .set_of_ues = self .uepp_module .get_set_of_ues ()
        self .ue_a4_candidates = {ue : {} for ue in self .set_of_ues}

    @debugging .trace (level = 1)
    def run (self, time, ue, serving):
        debugging .log ("Serving eNB for UE", ue, "is", serving, "and the ue position is", 
                                                                self .uepp_module .get_ue_position (ue, time), 
                                                                self .uepp_module .get_ue_position_XY (ue, time))

        meas_report = self .rsrqmp_module .measurement_report(time, ue, lambda_th = self .lambda_threshold) 
        debugging .log ("Measurement report for UE", ue, "is", meas_report)
        for enb, rsrq in meas_report:
            if enb == serving :
                continue
            if enb not in self .ue_a4_candidates [ue]:
                self .ue_a4_candidates [ue] [enb] = rsrq
            elif rsrq > self .ue_a4_candidates [ue] [enb] :
                self .ue_a4_candidates [ue] [enb] = rsrq
        
        if not bool (meas_report):
            debugging .log ("Measurment report is null, staying under serving eNB", serving)
            return (time, ue, serving, serving)

        if serving == -1 :
            target, rsrq =  max (meas_report, key = lambda x: x [1]) 
            debugging .log ("First-time-attach, doing handover to eNB", target, "with power", rsrq, "rsrq")
            return (time, ue, serving, target)

        handover_needed = False
        if  serving not in [e for e, rsrp in meas_report] :
            handover_needed = True
        else :
            serving_rsrq = max ([rsrq for e, rsrq in meas_report if e == serving])
            debugging .log ("Signal strength of serving eNB", serving, "is", serving_rsrq)

        if (handover_needed or serving_rsrq <= self .serving_cell_threshold) and bool (self .ue_a4_candidates [ue]):
            target = max (self .ue_a4_candidates [ue], key = lambda x : self .ue_a4_candidates [ue] [x])
            debugging .log ("Choosing handover target as eNB ", target, "with current power", rsrq, "rsrq")
            self .ue_a4_candidates [ue] .clear ()
            return (time, ue, serving, target)
        else :
            debugging .log ("No eNB with higher signal strength found, staying under serving")
            return (time, ue, serving, serving)



class UBBHOHandoverModule :
    def __init__ (self, ho_config, common_config, uepp_obj, enbpp_obj, rsrpmp_obj):
        debugging .log ("Initializing object", ho_config ['full_name'], "for class A3HandoverModule")
        self .name = ho_config ['name']

        self .lambda_threshold = common_config ['lambda']
        self .hom_incr = ho_config ["inc"]
        self .hom_decr = ho_config ["dec"]
        self .pp_window = ho_config ["pp_window"]

        self .uepp_module = uepp_obj
        self .enbpp_module = enbpp_obj
        self .rsrpmp_module = rsrpmp_obj

        self .set_of_enbs = self .enbpp_module .get_set_of_enbs ()
        self .hom = {e : ho_config ['hom'] for e in self .set_of_enbs}

        self .enb_handover_count = {e : 0 for e in self .set_of_enbs}
        self .enb_rlf_count = {e : 1 for e in self .set_of_enbs}
        self .enb_pp_count = {e : 0 for e in self .set_of_enbs}
        self .handover_history = {e : {} for e in self .set_of_enbs}

    @debugging .trace (level = 1)
    def check_and_adjust_pp (self, enb, ue, time) :
        for i in range (self .pp_window):
            if time - i - 1 in self .handover_history [enb] :
                if self .handover_history [enb] [time - i - 1]:
                    self .enb_pp_count [enb] += 1
                    break

        if time in self .handover_history [enb]:
            self .handover_history [enb] [time] += [ue]
        else :
            self .handover_history [enb] [time] = [ue]

    @debugging .trace (level = 1)
    def adjust_hom (self, enb) :
        num_rlf = self .enb_rlf_count [enb]
        num_ho = self .enb_handover_count [enb]
        num_pp = self .enb_pp_count [enb]
        
        rlfr = 0
        if num_ho + num_rlf != 0:
            rlfr = num_rlf / (num_ho + num_rlf)
        ppr = 0
        if num_ho != 0:
            ppr = num_pp / num_ho

        debugging .log ("eNB", enb, "rlfr", rlfr, "ppr", ppr)
        if rlfr > ppr :
            self .hom [enb] -= self .hom_decr
            debugging .log ("Decreasing HOM to", self .hom [enb])
        elif rlfr < ppr :
            self .hom [enb] += self .hom_incr
            debugging .log ("Increasing HOM to", self .hom [enb])

        if self .hom [enb] < 0 :
            self .hom [enb] = 0
        elif self .hom [enb] > 5 :
            self .hom [enb] = 5

    @debugging .trace (level = 1)
    def run (self, time, ue, serving):
        debugging .log ("Serving eNB for UE", ue, "is", serving, "and the ue position is", 
                                                                self .uepp_module .get_ue_position (ue, time), 
                                                                self .uepp_module .get_ue_position_XY (ue, time))

        meas_report = self .rsrpmp_module .measurement_report(time, ue, lambda_th = self .lambda_threshold) 
        debugging .log ("Measurement report for UE", ue, "is", meas_report)

        if serving != -1 and self .rsrpmp_module .get_reading_for (ue, time, serving) [1] < self .lambda_threshold :
            self .enb_rlf_count [serving] += 1
        
        if not bool (meas_report):
            debugging .log ("Measurment report is null, staying under serving eNB", serving)
            return (time, ue, serving, serving)

        if serving == -1 or serving not in [e for e, rsrp in meas_report] :
            target, rsrp =  max (meas_report, key = lambda x: x [1]) 
            debugging .log ("Inadequate signal strength from serving or first-time-attach, doing handover to eNB", 
                                            target, "with power", rsrp - 141, "dBm")
            if serving != -1 :
                self .enb_handover_count [serving] += 1
                self .check_and_adjust_pp (serving, ue, time)
                self .adjust_hom (serving)
            return (time, ue, serving, target)

        serving_rsrp = max ([rsrp for e, rsrp in meas_report if e == serving])
        debugging .log ("Signal strength of serving eNB", serving, "is", serving_rsrp)

        for candidate, rsrp in meas_report:
            if candidate == serving :
                continue

            if rsrp - serving_rsrp >= self .hom [serving] :
                debugging .log("Higher signal strength of", rsrp - 141, "dBm found for eNB", candidate)
                self .enb_handover_count [serving] += 1
                self .check_and_adjust_pp (serving, ue, time)
                self .adjust_hom (serving)
                return (time, ue, serving, candidate)

        debugging .log ("No eNB with higher signal strength found, staying under serving")
        return (time, ue, serving, serving)



class OMBFRAHandoverModule:
    def __init__ (self, ho_config, common_config, uepp_obj, enbpp_obj, rsrpmp_obj, enbcs_obj):
        debugging .log ("Initializing object", ho_config ['full_name'], "for class A3HandoverModule")
        self .name = ho_config ['name']
        self .hom = ho_config ['hom']
        self .w_om = ho_config ['weight_om']
        self .w_cl = ho_config ['weight_cl']
        self .w_rss = ho_config ['weight_rss']

        self .lambda_threshold = common_config ['lambda']

        self .uepp_module = uepp_obj
        self .enbpp_module = enbpp_obj
        self .rsrpmp_module = rsrpmp_obj
        self .enbcs_module = enbcs_obj

        self .set_of_enbs = self .enbpp_module .get_set_of_enbs ()
        self .enb_handover_count = {e : 1 for e in self .set_of_enbs}

    @debugging .trace (level = 1)
    def rad_adjust (self, aamm, to_adjust):
        rad_ref = 180
        val = abs (aamm + 180 - to_adjust)
        return abs (rad_ref - val)

    @debugging .trace (level = 1)
    def calc_score (self, om_score, cl_score, rss_score):
        return (om_score * self .w_om) + (cl_score * self .w_cl) + (rss_score * self .w_rss)

    @debugging .trace (level = 1)
    def r (self, x, y):
        return math .sqrt (x**2 + y**2)

    @debugging .trace (level = 1)
    def th (self, x, y):
        if x != 0:
            return math .atan (y / x) 
        else :
            return math .atan (float ('inf'))

    @debugging .trace (level = 1)
    def run (self, time, ue, serving):
        debugging .log ("Serving eNB for UE", ue, "is", serving, "and the ue position is", 
                                                                self .uepp_module .get_ue_position (ue, time), 
                                                                self .uepp_module .get_ue_position_XY (ue, time))

        measurement_report = self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold) 
        debugging .log ("Measurement report for UE", ue, "is", measurement_report)

        serving_rsrp = 0
        for e, rsrp in measurement_report :
            if e == serving :
                serving_rsrp = rsrp
        if serving_rsrp :
            meas_report = [(serving, serving_rsrp)]
        else :
            meas_report = []

        for e, rsrp in measurement_report :
            if rsrp >= serving_rsrp + self .hom:
                meas_report .append ((e, rsrp))
        
        if not bool (meas_report):
            debugging .log ("Measurment report is null, staying under serving eNB", serving)
            return (time, ue, serving, serving)

        if serving == -1 :
            target, rsrp =  max (meas_report, key = lambda x: x [1]) 
            debugging .log ("First-time-attach, doing handover to eNB", 
                                target, "with power", rsrp - 141, "dBm")
            return (time, ue, serving, target)

        if all ([serving == e for e, _ in meas_report]) :
            return (time, ue, serving, serving)

        serving_x, serving_y = self .enbpp_module .get_enb_position_XY (serving)
        total_rsrp = sum ([rsrp for e, rsrp in meas_report])
        total_r = 0
        total_rtheta = 0
        for enb, _ in meas_report :
            enb_x, enb_y = self .enbpp_module .get_enb_position_XY (enb)
            enb_r = self .r (serving_x - enb_x, serving_y - enb_y)
            enb_th = self .th (serving_x - enb_x, serving_y - enb_y)
            total_r += enb_r
            total_rtheta +=  enb_r * enb_th

        aamm = total_rtheta / total_r
        rad_sum = 0
        cl_set = []
        serving_cl = 0
        for enb, _ in meas_report :
            enb_x, enb_y = self .enbpp_module .get_enb_position_XY (enb)
            rad_sum += self .rad_adjust (aamm, self .th (serving_x - enb_x, serving_y - enb_y))
            cl = 0.89 - (len (self .enbcs_module .get_ues_under_enb (enb, time)) / 100)
            if cl == serving:
                serving_cl = cl
            cl_set .append (cl)

        target = serving
        best_score_seen = 0
        for candidate, rsrp in meas_report:
            candidate_x, candidate_y = self .enbpp_module. get_enb_position_XY (candidate)
            s_rss = rsrp / total_rsrp
            s_om = self .rad_adjust (aamm, self .th (serving_x - candidate_x, serving_y - candidate_y))
            s_cl = serving_cl / sum (cl_set)
            debugging .log ("scores rss om cl", s_rss, s_om, s_cl)
            candidate_score = self .calc_score (s_om, s_cl, s_rss)
            if candidate_score > best_score_seen:
                target = candidate

        if target == serving:
            debugging .log ("No eNB with better score found, staying under serving")
        else :
            self .enb_handover_count [serving] += 1
        return (time, ue, serving, target)


class NoHandoverModule:
    def __init__ (self, ho_config, common_config) :
        debugging .log (' ' .join (["Initializing object", ho_config ['full_name'], "for class NoHandoverModule"]))

    def run (self, *args, **kwargs) :
        return None


if __name__ == '__main__':
    debugging .log ("HandoverModule")
