#!/usr/bin/python
import sys
import random
import networkx as nx
import itertools as it
import my_modules .my_tracing as debugging
import my_modules .my_io as io
import my_modules .max_flow_algorithms as mfa_mod


class GreedyLoadModule:
    def __init__ (self, lb_config, common_config, ues, enbs, start_times, meas_data):
        #debugging .log (' ' .join (["Initializing object", lb_config ['full_name'], "for class GreedyLoadModule"]))
        debugging .log (' ' .join (["Initializing object", lb_config ['full_name'], "for class", type (self) .__name__]))

        self .lambda_threshold = common_config ['lambda']

        self .name = lb_config ['name']
        self .alpha = lb_config ['alpha']
        self .beta = lb_config ['beta']
        #self .base_number_of_eNBs = common_config ['enb_percentage_base']

        self .set_of_ues = ues
        self .set_of_enbs = enbs 
        self .ue_start_times = start_times
        self .dict_of_measurements = meas_data #[pos] [time] =[set([(enb, rsrp, power)...])]

        self .Load = {e:-1 for e in self .set_of_enbs}
        self .Lsp = {e:-1 for e in self .set_of_enbs}
        self .enb_connection_status = None

    @debugging .trace (level = 1)
    def is_system_unbalanced (self, t_now, enb_connection_status):
        self .enb_connection_status = enb_connection_status
        system_load_score = self .P_beta_t (t_now)
        debugging .log ("System load score is", system_load_score, "at time", t_now)
        return system_load_score > self .alpha

    @debugging .trace (level = 4) 
    def S (self, u, e, t):
        readings = [(rsrp, dbm) for (enb, rsrp, dbm) in self .M_u_t (u, t) if enb == e]
        if len (readings):
            return readings [0]
        else :
            return (-1, float ('-inf'))

    @debugging .trace (level = 4)
    def Load_e_t (self, e, t):
        return len (self .enb_connection_status [e])

    @debugging .trace (level = 4)
    def M_u_t (self, u, t):
        position = t - self .ue_start_times [u] + 1
        debugging .log ("Position", position, "Time", t, "ue", u, "ue_start_time", self .ue_start_times [u])
        Mut = list (set ([enb for enb, rsrp, power_dbm in self .dict_of_measurements [position] [t] 
                                if power_dbm >= self .lambda_threshold]))
        debugging .log ("M_u_t", Mut, "for ue", u)
        return Mut

    @debugging .trace (level = 4)
    def U_e_t (self, e, t):
        return self .enb_connection_status [e]

    @debugging .trace (level = 4)
    def LSP_e_t (self, e, t):
        Uet = self .U_e_t (e, t)
        if len (Uet) :
            debugging .log ("eNB", e, "U_e_t", Uet)
            M = [len (self .M_u_t (u, t)) - 1 for u in Uet]
            if len (M) and max (M):
                debugging .log ("M_u_t lengths", M, "Time", t, "eNB", e)
                return float (sum (M)) / (max (M) * len (self .U_e_t (e, t)))
            else :
                return -1
        else :
            return -1

    @debugging .trace (level = 3)
    def P_beta_t (self, t):
        for e in self .set_of_enbs:
            self .Load [e] = self .Load_e_t (e, t)

        #L_all_loaded = [e for e in self .set_of_enbs if self .L [e] != -1]
        Load_above_beta = [e for e in self .set_of_enbs if self .Load [e] > self .beta]
        Load_above_zero = [e for e in self .set_of_enbs if self .Load [e] > 0]
        #debugging .log ("All loaded", L_all_loaded)
        debugging .log ("All enbs above beta", Load_above_beta)
        #return len (Load_above_beta) / len (self .set_of_enbs)
        #return len (Load_above_beta) / self .base_number_of_eNBs
        return len (Load_above_beta) / len (Load_above_zero)

    @debugging .trace
    def run (self, t, enb_connection_status):
        set_of_handover_adjustments = [] #[(time, ue, src, dst), ... ]
        if self .is_system_unbalanced (t, enb_connection_status):
            debugging .log ("System is unbalanced -- Applying load balancing algorithm")
            for e in self .set_of_enbs:
                self .Lsp [e] = self .LSP_e_t (e, t)

            sorted_enbs_according_to_Lsp = list (filter (lambda x: x [1] != -1, 
                                                        sorted (self .Lsp .items (), key = lambda x : x [1], reverse = True)))
            debugging .log ("eNBs sorted (reverse) according to Lsp values", sorted_enbs_according_to_Lsp)

            for e, lsp_e in sorted_enbs_according_to_Lsp:
                if self .Load [e] > self .beta:
                    U_e_t = enb_connection_status [e]
                    Mut = {}
                    for u in U_e_t:
                        Mut [u] = self .M_u_t (u, t)
                    debugging .log ("All M_u_t values", Mut)
                    for u, candidates in [(u, Mut [u]) for u in Mut 
                                                        if len (Mut [u]) == len (max (Mut .values(), key = lambda x: len (x)))]:
                        if e in candidates:
                            candidates .remove (e)

                        debugging .log ("Set of candidates for UE", u, "is", candidates, "and serving eNB is", e)
                        if candidates :
                            d = random .choice (candidates)
                            debugging .log ("Randomly chosen target for UE", u, "is", d)
                            set_of_handover_adjustments .append ((t, u, e, d))

            debugging .log ("Load balancing adjustments are", set_of_handover_adjustments)
        else :
            debugging .log ("System is balanced")

        return set_of_handover_adjustments



class NetworkFlowBasedLoadModule:
    def __init__ (self, lb_config, common_config, rsrpmp_obj, uecs_obj, enbcs_obj):
        #debugging .log ("Initializing Network Flow Based Load Balancing Algorithm")
        debugging .log (' ' .join (["Initializing object", lb_config ['full_name'], "for class", type (self) .__name__]))
        self .alpha = lb_config ['alpha']
        self .beta = lb_config ['beta']
        self .lambda_threshold = common_config ['lambda']

        self .uecs_module = uecs_obj
        self .enbcs_module = enbcs_obj
        self .rsrpmp_module = rsrpmp_obj
    
    @debugging .trace (level = 3)
    def find_ordered_list_of_enbs (self, time):
        score = {}
        for e in self .high_load_enbs :
            if self .load (e) > self .beta :
                max_val = 0
                for ue in self .enbcs_module .get_ues_under_enb (e, time):
                    total_lba_candidates = len (self .find_lba_options (time, ue))
                    if total_lba_candidates > max_val :
                        max_val = total_lba_candidates
                score [e] = max_val
        return [max (score, key = lambda x : score[x])]
    
    @debugging .trace (level =4)
    def encode_ue (self, ue) :
        return ue
    
    @debugging .trace (level =4)
    def encode_enb (self, enb) :
        return enb * 10000 
    
    @debugging .trace (level =4)
    def decode_ue (self, ue) :
        return ue
    
    @debugging .trace (level =4)
    def decode_enb (self, enb) :
        return int (enb / 10000)

    @debugging .trace (level = 3)
    def construct_vertex_set (self, time, enb) :
        V_ue = set ([])
        for ue in self .enbcs_module .get_ues_under_enb (enb, time) :
            V_ue .add (self .encode_ue (ue))

        V_lba = set ([])
        for ue in self .enbcs_module .get_ues_under_enb (enb, time) :
            for lba_option in self .find_lba_options (time, ue) :
                if lba_option != enb :
                    V_lba .add (self .encode_enb (lba_option))

        return self .encode_enb (enb), V_ue, V_lba, 'S', 'T'

    @debugging .trace (level = 3)
    def construct_edge_set (self, time, v_e, V_ue, V_lba, s, t) :
        E = set ([])
        E .add ((s, v_e, self .load (self .decode_enb (v_e)) - self .beta))

        for ue in V_ue :
            E .add ((v_e, ue, 1))
            for lba_option in self .find_lba_options (time,  ue) :
                if lba_option != self .decode_enb (v_e) :
                    E .add ((ue, self .encode_enb (lba_option), 1))

        for enb in V_lba :
            E .add ((enb, t, self .beta - self .load (self .decode_enb (enb))))

        return E

    @debugging .trace (level = 2)
    def extract_lba_assignment (self, v_e, V_ue, V_lba, s, t, mf_graph) :
        edges = list (mf_graph .keys ())
        ret = []
        for e1 in edges:
            for e2 in edges:
                debugging .log ("Inspecting", e1, "and", e2)
                if e1[0] == v_e  and e1 [1] == e2 [0] and e2 [1] in V_lba :
                    ret .append ((self .decode_ue (e2 [0]), self .decode_enb (e2 [1])))
                    debugging .log ("Adding", (self .decode_ue (e2 [0]), self .decode_enb (e2 [1])), "to LBA assignment")

        return ret

    @debugging .trace (level = 3)
    def find_suitable_subset (self, time, enb):
        target_mf_val = self .load (enb) - self .beta
        debugging .log ("Target Max Flow", target_mf_val)

        v_e, V_ue, V_lba, s, t = self .construct_vertex_set (time, enb)
        V = set ([v_e, s, t]) .union (V_lba) .union (V_ue)
        
        E = self .construct_edge_set (time, v_e, V_ue, V_lba, s, t)
        
        debugging .log ("Vertex set", V)
        debugging .log ("Edge set", E)

        f = mfa_mod .FordFulkersonAlgorithm (V, E)
        mf_val, mf_graph = f .run ()
    
        if mf_val < target_mf_val :
            return []
        else :
            return self .extract_lba_assignment (v_e, V_ue, V_lba, s, t, mf_graph)

    @debugging .trace (level = 3)
    def load (self, e) :
        if e in self .enbs_in_use:
            return self .enbs_in_use [e]
        else :
            return 0

    @debugging .trace (level = 3)
    def find_lba_options (self, time, ue):
        ret = []
        for e, _ in self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold) :
            if self .load (e) < self .beta :
                ret .append (e)

        return ret

    @debugging .trace (level = 3)
    def get_high_load_enbs (self, time):
        ret = {}    
        for e in self .enbcs_module .get_set_of_enbs (): 
            load_e = len (self .enbcs_module .get_ues_under_enb (e, time))
            if load_e > self .beta :
                ret [e] = load_e
        return ret

    @debugging .trace (level = 3)
    def get_all_enbs_in_use (self, time):
        ret = {}    
        for e in self .enbcs_module .get_set_of_enbs (): 
            load_e = len (self .enbcs_module .get_ues_under_enb (e, time))
            if load_e :
                ret [e] = load_e
        return ret

    @debugging .trace (level = 2)
    def run (self, time):
        set_of_handover_adjustments = [] #[(t, ue, src, dst), ... ]

        self .high_load_enbs = self .get_high_load_enbs (time)
        self .enbs_in_use = self .get_all_enbs_in_use (time)

        while True :
            debugging .log ("High Load eNBs", self .high_load_enbs)
            debugging .log ("All eNBs in use", self .enbs_in_use)
            system_load_level = len (self .high_load_enbs) / len (self .enbs_in_use) if self .enbs_in_use else 0
            if system_load_level  > self.alpha :
                ordered_enbs = self .find_ordered_list_of_enbs (time)
                debugging .log ("Ordered list of eNBs", ordered_enbs)
                if not bool (ordered_enbs) :
                    break

                for enb in ordered_enbs :
                    lba_assignment = self .find_suitable_subset (time, enb)
                    debugging .log ("LBA assignment", lba_assignment)

                    for ue, target in lba_assignment :
                        set_of_handover_adjustments .append ((time, ue, enb, target))
                        
                        self .high_load_enbs [enb] -= 1
                        self .enbs_in_use [enb] -= 1
                        if target not in self .enbs_in_use :
                            self .enbs_in_use [target] = 1
                        else :
                            self .enbs_in_use [target] += 1
                    del self .high_load_enbs [enb]
            else :
                break

        return set_of_handover_adjustments



class jointueasloadmodule:
    def __init__ (self, lb_config, common_config, uepp_obj, rsrpmp_obj, uecs_obj, enbcs_obj):
        #debugging .log ("initializing joint ueas and load optimization algorithm")
        debugging .log (' ' .join (["initializing object", lb_config ['full_name'], "for class", type (self) .__name__]))
        self .name = lb_config ['name']
        self .alpha = lb_config ['alpha']
        self .beta = lb_config ['beta']
        self .eta = lb_config ['eta']
        self .gamma = lb_config ['gamma']
        self .ussl = lb_config ['USSL']
        self .lsrl_threshold = lb_config ['lsrl']
        self .expt = lb_config ["expt"]
        self .case = lb_config ["type"]
        self .lambda_threshold = common_config ['lambda']
        self .sst_threshold = common_config ['sst_th']

        self .uecs_module = uecs_obj
        self .enbcs_module = enbcs_obj
        self .rsrpmp_module = rsrpmp_obj
        self .uepp_module = uepp_obj

        self .p_u = {ue : None for ue in self .uepp_module .get_set_of_ues ()}
        self .temp_p_u = None
        self .ue_lsrl_data = {ue:{} for ue in self .uepp_module .get_set_of_ues ()}

        self .new_joins = set ([])
        self .all_ue_entered = []

        if self .case == "a" :
            debugging .log ("doing fully dynamic")
        elif self .case == "b" :
            debugging .log ("doing fully static")
        elif self .case == "c" :
            debugging .log ("doing semi dynamic")
            
    @debugging .trace (level = 4)
    def calculate_current_load (self, time, enb) :
        load = []
        for ue in self .temp_p_u :
            #if bool (self .temp_p_u [ue]) and time not in self .temp_p_u [ue] :
            #    print (self .temp_p_u [ue], ue)
            if bool (self .temp_p_u [ue]) and self .temp_p_u [ue] [time] == enb :
                load .append (ue)
        return load

    @debugging .trace (level = 3)
    def o_rc (self, time, ue):
        ret = []
        meas = self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold) 
        debugging .log ("time", time, "ue", ue, "rsrp_candidates", [e for e, _ in meas])
        for e, _ in meas :
            #if len (self .enbcs_module .get_ues_under_enb (e, time)) < self .beta :
            load = self .calculate_current_load (time, e)
            debugging .log ("ues under enb", e, "at time", time, "is", load, "load =", len (load), )
            if len (load) < self .beta :
                ret .append (e)

        debugging .log ("time", time, "ue", ue, "reassociation_candidates", ret)
        return ret

    @debugging .trace (level = 3)
    def sort_enbs (self, p_u, time):
        score = {}
        for e in self .enbcs_module .get_set_of_enbs ():
            ues = self .enbcs_module .get_ues_under_enb (e, time)
            union_rc = set ([])
            avg_case_total_rc = 0
            avg_case_total_ue = 0
            for ue in ues:
                debugging .log ("checking for ue", ue)
                if self .ussl == 'A':
                    next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .predict_measurement_report (time + 1, ue, lambda_th = self .sst_threshold)]

                elif self .ussl == 'C':
                    next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .measurement_report (time + 1, ue, lambda_th = self .lambda_threshold)]

                meas = self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold)
                if (e in next_meas_report and self .check_lsrl_status (time, ue)) or not bool (meas) :
                    continue    #no handover required at this time
                else :
                    avg_case_total_ue += 1
                    for cand in self .o_rc (time, ue):
                        union_rc .add (cand)
                        avg_case_total_rc += 1
            if self .expt in [1, 2] :
                score [e] = len (union_rc)
            elif self .expt in [3, 4] :
                score [e] = avg_case_total_rc / avg_case_total_ue if avg_case_total_ue != 0 else 0
        
        if self .expt in [1, 3] :
            return sorted (score, key = lambda x: score [x], reverse = True)
        elif self .expt in [2, 4] :
            return sorted (score, key = lambda x: score [x])

    @debugging .trace (level = 3)
    def sort_ues (self, time, serving):
        score = {}
        for ue in self .enbcs_module .get_ues_under_enb (serving, time) :
            debugging .log ("checking for ue", ue)
            if self .ussl == 'A':
                next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .predict_measurement_report (time + 1, ue, lambda_th = self .sst_threshold)]

            elif self .ussl == 'C':
                next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .measurement_report (time + 1, ue, lambda_th = self .lambda_threshold)]

            meas = self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold)
            if (serving in next_meas_report and self .check_lsrl_status (time, ue)) or not bool (meas) :
                continue    #no handover required at this time
            else :
                score [ue] = len (self .o_rc (time, ue))

        return sorted (score, key = lambda x: score [x])

    @debugging .trace (level = 3)
    def get_current_p_u (self):
        return io .deep_copy (self .p_u)

    @debugging .trace (level = 3)
    def set_current_p_u (self, p_u):
        self .p_u = io .deep_copy (p_u)

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
        g = nx .digraph()
        weighted_edges = []
        time_sequence = sorted (timed_meas_data .keys ())

        for ta, tb in zip (time_sequence, time_sequence [1:]):
            for x, y in it .product (timed_meas_data [ta], timed_meas_data [tb]):
                edge_weight = 1
                if x [0] == y [0]:
                    edge_weight = 0
                weighted_edges .append ((self .encode_node (x, ta), self .encode_node (y, tb), edge_weight))

        g .add_weighted_edges_from (weighted_edges)

        return (g, [self .encode_node (n, time_sequence [0]) for n in timed_meas_data [time_sequence [0]]], 
                        [self .encode_node (n, time_sequence [-1]) for n in timed_meas_data [time_sequence [-1]]])

    @debugging .trace (level = 2)
    def find_ueas_from (self, g, src, dst, ue):
        all_seq = []

        for s, d in it .product (src, dst):
            debugging .log ("finding path from", self .decode_node (s), "to", self .decode_node (d))
            path = nx .dijkstra_path (g, s, d)

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
            path_weight = nx .dijkstra_path_length (g, s, d)
            all_seq .append ((seq, path_weight))

        return [self .make_ueas_dict (ueas [0], ue) for ueas in all_seq if ueas [1] == min (all_seq, key = lambda x: x[1]) [1]]

    @debugging .trace (level = 4)
    def make_ueas_dict (self, ueas, ue):
        ret = {}
        if len (ueas) == 1:
            ret [ueas [0] [0]] = ueas [0] [1]
        else :
            for (t1, e1), (t2, e2) in zip (ueas, ueas [1:]) :
                for t in range (t1, t2):
                    ret [t] = e1
                ret [t2] = e2
            for t in range (t2, self .uepp_module .get_ue_end_time (ue) + 1) :
                ret [t] = e2

        return ret

    @debugging .trace (level = 3)
    def check_lsrl_status (self, t_now, ue):
        if self .ussl == 'C':
            return True

        if self .uepp_module .get_ue_start_time (ue) > (t_now - self .lsrl_threshold + 1) or len (self .ue_lsrl_data [ue]) < self .lsrl_threshold:
            debugging .log ("lsrl check unnecessary for ue", ue, "at time", t_now)
            return True 

        elif any ([self .ue_lsrl_data [ue] [t] >= self .lambda_threshold for t in range (t_now - self .lsrl_threshold + 1, t_now + 1, 1)]) :
            debugging .log ("lsrl length is shorter for ue", ue, "at time", t_now)
            return True
        
        else :
            debugging .log ("lsrl length exceeded for ue", ue, "at time", t_now)
            return False

    @debugging .trace (level = 3)
    def find_possible_ueas (self, t_now, ue, src):
        meas_data = {}

        #mesurements at time t_now in ue_pos
        meas_data [t_now] = [(enb, rsrp) for enb, rsrp in self .rsrpmp_module .measurement_report (t_now, ue, lambda_th = self .lambda_threshold) if enb != src]
        debugging .log ("measurement report for ue", ue, "is", meas_data [t_now])

        if self .ussl == 'A':
            next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .predict_measurement_report (t_now + 1, ue, lambda_th = self .sst_threshold)]

        elif self .ussl == 'c':
            next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .measurement_report (t_now + 1, ue, lambda_th = self .lambda_threshold)]

        _, serving_signal_dbm = self .rsrpmp_module .get_reading_for (ue, t_now, src)

        self .ue_lsrl_data [ue] [t_now] = serving_signal_dbm

        if (src in next_meas_report and self .check_lsrl_status (t_now, ue)) or not bool (meas_data [t_now]):
            debugging .log ("no handover required, as serving enb is having signal strength above required")
            return []

        #future measurements
        for t in range (t_now + 1, self .uepp_module .get_journey_end_time (ue) + 1, 1):
            if self .ussl == 'a':
                meas_data [t] = self .rsrpmp_module .predict_measurement_report (t, ue, lambda_th = self .lambda_threshold) 
                #print ('p', sorted(set ([c for c, _ in meas_data [t]])))
                #print ('a', sorted(set ([c for c, _ in self .rsrpmp_module .measurement_report (t, ue, lambda_th = self .lambda_threshold)])))
            elif self .ussl == 'c':
                meas_data [t] = self .rsrpmp_module .measurement_report (t, ue, lambda_th = self .lambda_threshold) 

            #delete empty measurement time instances
            if meas_data [t] == []:
                del meas_data [t]

        if len (meas_data) == 1:
            return []

        #create the graph
        g, src_set, dst_set = self .construct_graph_from (meas_data)

        #identify the possible ueas 
        possible_ueas = self .find_ueas_from (g, src_set, dst_set, ue)
        
        return possible_ueas

    @debugging .trace (level = 3)
    def next_target (self, ueas, time):
        ret = -1 if ueas is None else ueas [time]
        #ret = ueas [time]
        debugging .log ("finding next target from ueas", ueas, "as", ret)
        return ret

    @debugging .trace (level = 3)
    def i_gamma (self, ls):
        high = 0
        for t in ls :
            if ls [t] > self .beta :
                high += 1
        score = high / len (ls)
        debugging .log ("load sequence", ls, "score", score)
        return 1 if score <= self .gamma else 0

    @debugging .trace (level = 3)
    def calculate_system_health_status (self, p_u) :
        ls = {e:{} for e in self .enbcs_module .get_set_of_enbs ()}
        for ue in p_u :
            if p_u [ue] == None :
                continue
            #debugging .log ("current ueas for ue", ue, "is", p_u [ue])
            for t in p_u [ue] :
                c = p_u [ue] [t]
                if t not in ls [c] :
                    ls [c] [t] = 1
                else :
                    ls [c] [t] += 1
        health = 0
        for e in ls :
            if len (ls [e]):
                debugging .log ("evaluating gamma score for enb", e)
                health += self .i_gamma (ls [e])
        debugging .log ("system health status calculated as", health)
        return health

    @debugging .trace (level = 3)
    def evaluate_impact (self, ue, ueas, p_u) :
        temp = io .deep_copy (p_u)
        temp [ue] = ueas
        objective = self .calculate_system_health_status (temp)
        return objective

    @debugging .trace (level = 3)
    def greedy_choice (self, time, ue, serving, p_u):
        choices = self .find_possible_ueas (time, ue, serving) #
        debugging .log (len (choices), "possible ueas for ue", ue, "with serving enb", serving, "at time", time, ":", choices)
        if not len (choices):
            return p_u [ue]
        candidates = self .o_rc (time, ue)
        target = []
        ueas_rc = []
        for ueas in choices :
            candidate = self .next_target (ueas, time)
            if candidate in candidates :
                target .append (ueas)
                ueas_rc .append (candidate)
        debugging .log ("time", time, "ue", ue, "ueas_rc", ueas_rc)

        if not len (target):
            max_score = 0
            for ueas in choices :
                impact = self .evaluate_impact (ue, ueas, p_u)
                debugging .log ("time", time, "ue", ue,  "potential_target", self .next_target (ueas, time), "impact", impact)
                if impact >= max_score:
                    if impact > max_score :
                        max_score = impact
                        target .clear ()
                    target .append (ueas)
            #target = [min (score, key = lambda x : score [x])]

        ret = random .choice (target)
        #ret = min (target, key = lambda x : self . calculate_current_load (time, self .next_target (x, time)))

        debugging .log ("time", time, "ue", ue,  "selected_target", self .next_target (ret, time))
        p_u [ue] = ret
        return ret

    @debugging .trace (level = 3)
    def new_join (self, ue) :
        self .new_joins .add (ue)

    @debugging .trace (level = 2)
    def run (self, time):
        set_of_handover_adjustments = [] #[(t, ue, src, dst), ... ]
        to_remove = []
        for ue in self .all_ue_entered :
            _, serving_signal_dbm = self .rsrpmp_module .get_reading_for (ue, time, self .uecs_module .get_serving_enb_of (ue, time))
            self .ue_lsrl_data [ue] [time] = serving_signal_dbm
            debugging .log ("current lsrl status of ue", ue, "is", self .ue_lsrl_data [ue])

            if not self .uepp_module .ue_still_in_system (ue, time + 1) :
                to_remove .append (ue)

        self .temp_p_u = self .get_current_p_u ()
        flag = True
        adjusted_enbs = []
        adjusted_ues = []
        for ue in self .new_joins :
            debugging .log ("first time entry of ue", ue)
            ueas = self .greedy_choice (time, ue, -1, self .temp_p_u)
            set_of_handover_adjustments .append ((time, ue, -1, self .next_target (ueas, time)))
            self .temp_p_u [ue] = ueas
            self .all_ue_entered .append (ue)
        self .new_joins .clear()
        if self .case == "a" :
            #fully dynamic
            while flag :
                flag = False
                b_sorted = self .sort_enbs (self .temp_p_u, time)
                debugging .log ("time", time, "b_sorted", b_sorted)
                for e_i in b_sorted:
                    if e_i not in adjusted_enbs:
                        u_sorted = self .sort_ues (time, e_i)
                        debugging .log ("time", time, "u_sorted", u_sorted)
                        for u_j in u_sorted:
                            if u_j not in adjusted_ues:
                                ueas = self .greedy_choice (time, u_j, e_i, self .temp_p_u)
                                set_of_handover_adjustments .append ((time, u_j, e_i, self .next_target (ueas, time)))
                                debugging .log ("replacing ueas", self .temp_p_u [u_j], "with", ueas, "for ue", u_j)
                                self .temp_p_u [u_j] = ueas
                                flag = True
                                adjusted_ues .append (u_j)
                                break
                        if flag :
                            break
                        adjusted_enbs .append (e_i)
        elif self .case == "b" :
            #fully static
            while flag :
                flag = False
                b_sorted = self .sort_enbs (self .temp_p_u, time)
                debugging .log ("time", time, "b_sorted", b_sorted)
                for e_i in b_sorted:
                    u_sorted = self .sort_ues (time, e_i)
                    debugging .log ("time", time, "u_sorted", u_sorted)
                    for u_j in u_sorted:
                        ueas = self .greedy_choice (time, u_j, e_i, self .temp_p_u)
                        set_of_handover_adjustments .append ((time, u_j, e_i, self .next_target (ueas, time)))
                        self .temp_p_u [u_j] = ueas
        elif self .case == "c" :
            #semi dynamic
            while flag :
                flag = False
                b_sorted = self .sort_enbs (self .temp_p_u, time)
                debugging .log ("time", time, "b_sorted", b_sorted)
                for e_i in b_sorted:
                    if e_i not in adjusted_enbs:
                        u_sorted = self .sort_ues (time, e_i)
                        debugging .log ("time", time, "u_sorted", u_sorted)
                        for u_j in u_sorted:
                            ueas = self .greedy_choice (time, u_j, e_i, self .temp_p_u)
                            set_of_handover_adjustments .append ((time, u_j, e_i, self .next_target (ueas, time)))
                            self .temp_p_u [u_j] = ueas
                        adjusted_enbs .append (e_i)
                        flag = True
                        break

        debugging .log ("all ues in system", sorted (self .all_ue_entered), "total", len (self .all_ue_entered), "to remove", to_remove)
        for ue in to_remove:
            debugging .log ("removing ue", ue)
            set_of_handover_adjustments .append ((time, ue, self .uecs_module .get_serving_enb_of (ue, time), -1))
            self .temp_p_u [ue] = None
            self .all_ue_entered .remove (ue)

        debugging .log ("set of handover adjustments", set_of_handover_adjustments)
        self .set_current_p_u (self .temp_p_u)

        return set_of_handover_adjustments



class Cmp1LoadModule:
    def __init__ (self, lb_config, common_config, uepp_obj, rsrpmp_obj, uecs_obj, enbcs_obj):
        #debugging .log ("Initializing Distributed Load Balancing Algorithm")
        debugging .log (' ' .join (["Initializing object", lb_config ['full_name'], "for class", type (self) .__name__]))
        self .name = lb_config ['name']
        self .lambda_threshold = common_config ['lambda']
        self .beta = lb_config ['beta']

        self .uecs_module = uecs_obj
        self .enbcs_module = enbcs_obj
        self .rsrpmp_module = rsrpmp_obj
        self .uepp_module = uepp_obj

        self .P_U = {ue : None for ue in self .uepp_module .get_set_of_ues ()}
        self .ue_LSRL_data = {ue : {} for ue in self .uepp_module .get_set_of_ues ()}

        self .new_joins = set ([])
        self .all_ue_entered = []

    @debugging .trace (level = 3)
    def candidates (self, ue, time) :
        candidates = []
        for e, _ in self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold) :
            if len (self .enbcs_module .get_ues_under_enb (e, time)) < self .beta :
                candidates .append (e)
        return candidates

    @debugging .trace (level = 2)
    def run (self, time) :
        set_of_handover_adjustments = []
        for e_i in self .enbcs_module .get_set_of_enbs ():
            ues = self .enbcs_module .get_ues_under_enb (e_i, time)
            debugging .log ("Value of ues", ues)
            
            T = []
            if len (ues) > self .beta :
                for _ in range (len (ues) - self .beta) :
                    u = random .choice (ues)
                    debugging .log ("Remaining UEs", ues, "under eNB", e_i)
                    ues .remove (u)
                    T .append (u)
            debugging .log ("Value of T", T)

            for ue in T :
                candidates = self .candidates (ue, time)
                if len (candidates) :
                    set_of_handover_adjustments .append ((time, ue, e_i, random .choice (candidates)))
        return set_of_handover_adjustments



class Cmp2LoadModule:
    def __init__ (self, lb_config, common_config, uepp_obj, rsrpmp_obj, uecs_obj, enbcs_obj):
        #debugging .log ("Initializing User Association and Resource Allocation Optimization Algorithm")
        debugging .log (' ' .join (["Initializing object", lb_config ['full_name'], "for class", type (self) .__name__]))
        self .name = lb_config ['name']
        self .lambda_threshold = common_config ['lambda']
        self .beta = lb_config ['beta']

        self .uecs_module = uecs_obj
        self .enbcs_module = enbcs_obj
        self .rsrpmp_module = rsrpmp_obj
        self .uepp_module = uepp_obj

        self .P_U = {ue : None for ue in self .uepp_module .get_set_of_ues ()}
        self .ue_LSRL_data = {ue : {} for ue in self .uepp_module .get_set_of_ues ()}

        self .new_joins = set ([])
        self .all_ue_entered = []
        self .CIO_values = {enb : {}  for enb in self .enbcs_module .get_set_of_enbs ()}

    @debugging .trace (level = 3)
    def calculate_virtual_handovers (self, time, enb, u_enb, neigh, params) :
        debugging . log ("Checking for sample", params)
        vstate = {enb : u_enb}
        for n in neigh :
            vstate [n] = self .enbcs_module .get_ues_under_enb (n, time)
        for u in u_enb :
            meas = self .rsrpmp_module .measurement_report (time, u, lambda_th = self .lambda_threshold)
            if len (meas) :
                targ = max ([(c, p + params [c]) for c, p in meas], key = lambda x : x [1]) [0]
            else :
                targ = enb
            if targ != enb :
                vstate [enb] .remove (u)
                vstate [targ] .append (u)

        return -1 * len ([e for e in vstate if len (vstate [e]) > self .beta])

    @debugging .trace (level = 3)
    def calculate_samples (self, enb, neigh) :
        CIO = [0, 1, 2, 3]
        samples = []
        for c in [p for p in it .product (CIO, repeat = len (neigh))]:
            config = {}
            for i, n in enumerate (neigh) :
                config [n] = c [i]
            samples .append (io .deep_copy (config))
        debugging .log ("Returning samples for", neigh)
        return samples

    @debugging .trace (level = 3)
    def calculate_adjustments (self, time, enb, u_enb, params) :
        adjustments = []
        for u in u_enb :
            meas = self .rsrpmp_module .measurement_report (time, u, lambda_th = self .lambda_threshold)
            if len (meas) :
                targ = max ([(c, p + params [c]) for c, p in meas], key = lambda x : x [1]) [0]
            else :
                targ = enb 
            if targ != enb :
                adjustments .append ((time, u, enb, targ))
        return adjustments

    @debugging .trace (level = 2)
    def run (self, time) :
        set_of_handover_adjustments = []
        #step 1: data collection
        #step 2: optimization
        #      .1: choose a cell 
        c = random .choice (list (self .enbcs_module .get_set_of_enbs ()))
        #      .2: store initial state and utility
        u_c = self .enbcs_module .get_ues_under_enb (c, time)
        neigh = set ([])
        for u in u_c :
            cand = [e for e, _ in self .rsrpmp_module .measurement_report (time, u, lambda_th = self .lambda_threshold)]
            for e in cand :
                neigh .add (e)
        debugging .log ("Neighbours set of enb", c, "is", neigh)
        #      .3: sampling
        samples = self .calculate_samples (c, neigh)
        #      .4: virtual handover
        #      .5: virtual scheduling & utility computation
        max_utility = float ("-inf") 
        for sample in samples :
            utility = self .calculate_virtual_handovers (time, c, u_c, neigh, sample)
        #      .6: choosing optimal sample -- find sample with maximum utility
            if utility > max_utility :
                max_utility = utility
                optimal = sample
        #step 3: distribution & execution
        set_of_handover_adjustments = self .calculate_adjustments (time, c, u_c, optimal)
        return set_of_handover_adjustments



class NoLoadModule:
    def __init__ (self, lb_config, common_config) :
        debugging .log (' ' .join (["Initializing object", lb_config ['full_name'], "for class", type (self) .__name__]))
        self .name = lb_config ['name']

    def run (self, *args, **kwargs) :
        set_of_handover_adjustments = []
        return set_of_handover_adjustments



class LB_USSL_DUAL_Module:
    def __init__ (self, lb_config, common_config, uepp_obj, uepp_6kmph_obj, rsrpmp_obj, rsrpmp_6kmph_obj, uecs_obj, enbcs_obj, preprocessed_data, preprocessed_data_6kmph):
        #debugging .log ("initializing joint ueas and load optimization algorithm")
        debugging .log (' ' .join (["initializing object", lb_config ['full_name'], "for class", type (self) .__name__]))
        self .name = lb_config ['name']
        self .alpha = lb_config ['alpha']
        self .beta = lb_config ['beta']
        self .eta = lb_config ['eta']
        self .gamma = lb_config ['gamma']
        self .ussl = lb_config ['USSL']
        self .lsrl_threshold = lb_config ['lsrl']
        self .expt = lb_config ["expt"]
        self .case = lb_config ["type"]
        self .lambda_threshold = common_config ['lambda']
        self .sst_threshold = common_config ['sst_th']
        self .duration = common_config ['duration']

        self .uecs_module = uecs_obj
        self .enbcs_module = enbcs_obj
        self .rsrpmp_module = rsrpmp_obj
        self .rsrpmp_6kmph_module = rsrpmp_6kmph_obj
        self .uepp_module = uepp_obj
        self .uepp_6kmph_module = uepp_6kmph_obj
        self .preprocessed_data = preprocessed_data
        self .preprocessed_data_6kmph = preprocessed_data_6kmph

        self .p_u = {ue : None for ue in self .uepp_module .get_set_of_ues () .union (self .uepp_6kmph_module .get_set_of_ues ())}
        self .temp_p_u = None
        self .ue_lsrl_data = {ue:{} for ue in self .uepp_module .get_set_of_ues () .union (self .uepp_6kmph_module .get_set_of_ues ())}

        self .new_joins = set ([])
        self .all_ue_entered = []

        if self .case == "a" :
            debugging .log ("doing fully dynamic")
        elif self .case == "b" :
            debugging .log ("doing fully static")
        elif self .case == "c" :
            debugging .log ("doing semi dynamic")
            
    @debugging .trace (level = 4)
    def calculate_current_load (self, time, enb) :
        load = []
        for ue in self .temp_p_u :
            #if bool (self .temp_p_u [ue]) and time not in self .temp_p_u [ue] :
            #    print (self .temp_p_u [ue], ue)
            if bool (self .temp_p_u [ue]) and self .temp_p_u [ue] [time] == enb :
                load .append (ue)
        return load

    @debugging .trace (level = 3)
    def o_rc (self, time, ue):
        ret = []
        if ue in self .uepp_module .get_set_of_ues ():
            meas = self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold) 
        elif ue in self .uepp_6kmph_module .get_set_of_ues ():
            meas = self .rsrpmp_6kmph_module .measurement_report (time, ue, lambda_th = self .lambda_threshold)
        else :
            debugging .log ("ue does not belong to any class. please debug")
            exit (0)
        debugging .log ("time", time, "ue", ue, "rsrp_candidates", [e for e, _ in meas])
        for e, _ in meas :
            #if len (self .enbcs_module .get_ues_under_enb (e, time)) < self .beta :
            load = self .calculate_current_load (time, e)
            debugging .log ("ues under enb", e, "at time", time, "is", load, "load =", len (load), )
            if len (load) < self .beta :
                ret .append (e)

        debugging .log ("time", time, "ue", ue, "reassociation_candidates", ret)
        return ret

    @debugging .trace (level = 3)
    def sort_enbs (self, p_u, time):
        score = {}
        for e in self .enbcs_module .get_set_of_enbs ():
            ues = self .enbcs_module .get_ues_under_enb (e, time)
            union_rc = set ([])
            avg_case_total_rc = 0
            avg_case_total_ue = 0
            for ue in ues:
                debugging .log ("checking for ue", ue)
                if ue in self .uepp_module .get_set_of_ues () :
                    if self .ussl == 'A':
                        next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .predict_measurement_report (time + 1, ue, lambda_th = self .sst_threshold)]

                    elif self .ussl == 'C':
                        next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .measurement_report (time + 1, ue, lambda_th = self .lambda_threshold)]

                    meas = self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold)
                elif ue in self .uepp_6kmph_module .get_set_of_ues () :
                    if self .ussl == 'A':
                        next_meas_report = [cell for cell, rsrp in self .rsrpmp_6kmph_module .predict_measurement_report (time + 1, ue, lambda_th = self .sst_threshold)]

                    elif self .ussl == 'C':
                        next_meas_report = [cell for cell, rsrp in self .rsrpmp_6kmph_module .measurement_report (time + 1, ue, lambda_th = self .lambda_threshold)]

                    meas = self .rsrpmp_6kmph_module .measurement_report (time, ue, lambda_th = self .lambda_threshold)
                else :
                    debugging .log ("ue do not belong to either class. please debug")
                    exit (0)
                if (e in next_meas_report and self .check_lsrl_status (time, ue)) or not bool (meas) :
                    continue    #no handover required at this time
                else :
                    avg_case_total_ue += 1
                    for cand in self .o_rc (time, ue):
                        union_rc .add (cand)
                        avg_case_total_rc += 1
            if self .expt in [1, 2] :
                score [e] = len (union_rc)
            elif self .expt in [3, 4] :
                score [e] = avg_case_total_rc / avg_case_total_ue if avg_case_total_ue != 0 else 0
        
        if self .expt in [1, 3] :
            return sorted (score, key = lambda x: score [x], reverse = True)
        elif self .expt in [2, 4] :
            return sorted (score, key = lambda x: score [x])

    @debugging .trace (level = 3)
    def sort_ues (self, time, serving):
        score = {}
        for ue in self .enbcs_module .get_ues_under_enb (serving, time) :
            debugging .log ("checking for ue", ue)
            if ue in self .uepp_module .get_set_of_ues () :
                if self .ussl == 'A':
                    next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .predict_measurement_report (time + 1, ue, lambda_th = self .sst_threshold)]

                elif self .ussl == 'C':
                    next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .measurement_report (time + 1, ue, lambda_th = self .lambda_threshold)]

                meas = self .rsrpmp_module .measurement_report (time, ue, lambda_th = self .lambda_threshold)
            elif ue in self .uepp_6kmph_module .get_set_of_ues () :
                if self .ussl == 'A':
                    next_meas_report = [cell for cell, rsrp in self .rsrpmp_6kmph_module .predict_measurement_report (time + 1, ue, lambda_th = self .sst_threshold)]

                elif self .ussl == 'C':
                    next_meas_report = [cell for cell, rsrp in self .rsrpmp_6kmph_module .measurement_report (time + 1, ue, lambda_th = self .lambda_threshold)]

                meas = self .rsrpmp_6kmph_module .measurement_report (time, ue, lambda_th = self .lambda_threshold)
            else :
                debugging .log ("ue do not belong to either class. please debug")
                exit (0)
            if (serving in next_meas_report and self .check_lsrl_status (time, ue)) or not bool (meas) :
                continue    #no handover required at this time
            else :
                score [ue] = len (self .o_rc (time, ue))

        return sorted (score, key = lambda x: score [x])

    @debugging .trace (level = 3)
    def get_current_p_u (self):
        return io .deep_copy (self .p_u)

    @debugging .trace (level = 3)
    def set_current_p_u (self, p_u):
        self .p_u = io .deep_copy (p_u)

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
        g = nx .digraph()
        weighted_edges = []
        time_sequence = sorted (timed_meas_data .keys ())

        for ta, tb in zip (time_sequence, time_sequence [1:]):
            for x, y in it .product (timed_meas_data [ta], timed_meas_data [tb]):
                edge_weight = 1
                if x [0] == y [0]:
                    edge_weight = 0
                weighted_edges .append ((self .encode_node (x, ta), self .encode_node (y, tb), edge_weight))

        g .add_weighted_edges_from (weighted_edges)

        return (g, [self .encode_node (n, time_sequence [0]) for n in timed_meas_data [time_sequence [0]]], 
                        [self .encode_node (n, time_sequence [-1]) for n in timed_meas_data [time_sequence [-1]]])

    @debugging .trace (level = 2)
    def find_ueas_from (self, g, src, dst, ue):
        all_seq = []

        for s, d in it .product (src, dst):
            debugging .log ("finding path from", self .decode_node (s), "to", self .decode_node (d))
            path = nx .dijkstra_path (g, s, d)

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
            path_weight = nx .dijkstra_path_length (g, s, d)
            all_seq .append ((seq, path_weight))

        return [self .make_ueas_dict (ueas [0], ue) for ueas in all_seq if ueas [1] == min (all_seq, key = lambda x: x[1]) [1]]

    @debugging .trace (level = 4)
    def make_ueas_dict (self, ueas, ue):
        ret = {}
        if len (ueas) == 1:
            ret [ueas [0] [0]] = ueas [0] [1]
        else :
            for (t1, e1), (t2, e2) in zip (ueas, ueas [1:]) :
                for t in range (t1, t2):
                    ret [t] = e1
                ret [t2] = e2
            if ue in self .uepp_module .get_set_of_ues () :
                for t in range (t2, self .uepp_module .get_ue_end_time (ue) + 1) :
                    ret [t] = e2
            elif ue in self .uepp_6kmph_module .get_set_of_ues () :
                for t in range (t2, self .uepp_module .get_ue_end_time (ue) + 1) :
                    ret [t] = e2
            else :
                debugging .log ("ue not in either class. please debug")
                exit (0)

        return ret

    @debugging .trace (level = 3)
    def check_lsrl_status (self, t_now, ue):
        if self .ussl == 'C':
            return True

        if ue in self .uepp_module .get_set_of_ues () and (self .uepp_module .get_ue_start_time (ue) > (t_now - self .lsrl_threshold + 1) or len (self .ue_lsrl_data [ue]) < self .lsrl_threshold):
            debugging .log ("lsrl check unnecessary for ue", ue, "at time", t_now)
            return True 
        elif ue in self .uepp_6kmph_module .get_set_of_ues () and (self .uepp_6kmph_module .get_ue_start_time (ue) > (t_now - self .lsrl_threshold + 1) or len (self .ue_lsrl_data [ue]) < self .lsrl_threshold):
            debugging .log ("lsrl check unnecessary for ue", ue, "at time", t_now)
            return True 

        elif any ([self .ue_lsrl_data [ue] [t] >= self .lambda_threshold for t in range (t_now - self .lsrl_threshold + 1, t_now + 1, 1)]) :
            debugging .log ("lsrl length is shorter for ue", ue, "at time", t_now)
            return True
        
        else :
            debugging .log ("lsrl length exceeded for ue", ue, "at time", t_now)
            return False

    @debugging .trace (level = 4)
    def calc_ueas (self, ue, e, t) :
        ueas = {t:e}
        i = 1
        if ue in self .uepp_module .get_set_of_ues () :
            ue_pos = self .uepp_module .get_ue_position (ue, t)
            for pos in sorted (self .preprocessed_data .keys()):
                if pos > ue_pos :
                    #debugging .log ("Pos", pos, "time", t + i)
                    ueas [t + i] = self .preprocessed_data [pos] [ueas [t + i - 1]]
                    if t + i > self .duration :
                        break
                    i += 1
        elif ue in self .uepp_6kmph_module .get_set_of_ues () :
            ue_pos = self .uepp_6kmph_module .get_ue_position (ue, t)
            for pos in sorted (self .preprocessed_data_6kmph .keys()):
                if pos > ue_pos :
                    #debugging .log ("Pos", pos, "time", t + i, ueas,  ue_pos)
                    ueas [t + i] = self .preprocessed_data_6kmph [pos] [ueas [t + i - 1]]
                    if t + i > self .duration :
                        break
                    i += 1
        else :
            debugging .log ("UE not in either class. please debug")

        return ueas

    @debugging .trace (level = 4)
    def N_HO (self,  ueas) :
        n = 0
        seq = list (ueas .values ())
        for e1, e2 in zip (seq, seq [1:]):
            if e1 != e2 :
                n += 1
        return n

    @debugging .trace (level = 3)
    def find_possible_ueas (self, t_now, ue, src):
        meas_data = {}

        if ue in self .uepp_module .get_set_of_ues () :
            #mesurements at time t_now in ue_pos
            meas_data [t_now] = [(enb, rsrp) for enb, rsrp in self .rsrpmp_module .measurement_report (t_now, ue, lambda_th = self .lambda_threshold) if enb != src]
            debugging .log ("measurement report for ue", ue, "is", meas_data [t_now])

            if self .ussl == 'A':
                next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .predict_measurement_report (t_now + 1, ue, lambda_th = self .sst_threshold)]

            elif self .ussl == 'C':
                next_meas_report = [cell for cell, rsrp in self .rsrpmp_module .measurement_report (t_now + 1, ue, lambda_th = self .lambda_threshold)]

            else :
                debugging .log ("Undefined USSL", self .ussl)

            #Record Signal Strength of serving eNB, used for calculating LSRL when needed
            _, serving_signal_dbm = self .rsrpmp_module .get_reading_for (ue, t_now, src)

            self .ue_lsrl_data [ue] [t_now] = serving_signal_dbm

            if (src in next_meas_report and self .check_lsrl_status (t_now, ue)) or not bool (meas_data [t_now]):
                debugging .log ("no handover required, as serving enb is having signal strength above required")
                return []

            current = set ([e for e, _ in meas_data [t_now]])
            ppd_current = set (self .preprocessed_data [self .uepp_module .get_ue_position (ue, t_now)] .values ())

        elif ue in self .uepp_6kmph_module .get_set_of_ues () :
            #mesurements at time t_now in ue_pos
            meas_data [t_now] = [(enb, rsrp) for enb, rsrp in self .rsrpmp_6kmph_module .measurement_report (t_now, ue, lambda_th = self .lambda_threshold) if enb != src]
            debugging .log ("measurement report for ue", ue, "is", meas_data [t_now])

            if self .ussl == 'A':
                next_meas_report = [cell for cell, rsrp in self .rsrpmp_6kmph_module .predict_measurement_report (t_now + 1, ue, lambda_th = self .sst_threshold)]

            elif self .ussl == 'C':
                next_meas_report = [cell for cell, rsrp in self .rsrpmp_6kmph_module .measurement_report (t_now + 1, ue, lambda_th = self .lambda_threshold)]

            #Record Signal Strength of serving eNB, used for calculating LSRL when needed
            _, serving_signal_dbm = self .rsrpmp_6kmph_module .get_reading_for (ue, t_now, src)
            
            self .ue_lsrl_data [ue] [t_now] = serving_signal_dbm

            if (src in next_meas_report and self .check_lsrl_status (t_now, ue)) or not bool (meas_data [t_now]):
                debugging .log ("no handover required, as serving enb is having signal strength above required")
                return []

            current = set ([e for e, _ in meas_data [t_now]])
            ppd_current = set (self .preprocessed_data_6kmph [self .uepp_6kmph_module .get_ue_position (ue, t_now)] .values ())

        else :
            debugging .log ("ue does not belong to any class. please debug")
            exit (0)

        debugging .log ("[Real/Current]Measurement report", current)
        debugging .log ("[PPD] Precalculated Next Hops", ppd_current)
        possible_ueas = []
        for e in current :
            debugging .log ("Calculating UEAS for real measurement: eNB", e, "UE", ue, "Time", t_now)
            if e in ppd_current :
                debugging .log ("Calculating UEAS for ppd measurement: eNB", e, "UE", ue, "Time", t_now)
                ueas  = self .calc_ueas (ue, e, t_now)
                debugging .log ("Adding UEAS", ueas)
                possible_ueas .append (ueas)

        if not current .issubset (ppd_current):
            ueases = []
            min_n = float ("inf")
            for e in ppd_current:
                debugging .log ("[ALL] Calculating UEAS for ppd measurement: eNB", e, "UE", ue, "Time", t_now)
                ueas = self .calc_ueas (ue, e, t_now)
                debugging .log ("Found UEAS", ueas)
                n = self .N_HO (ueas)
                if n <= min_n :
                    if n < min_n:
                        ueases .clear ()
                        min_n = n
                    ueases .append (ueas)
            for e in current .difference (ppd_current) :
                debugging .log ("[Difference] Calculating UEAS for ppd measurement: eNB", e, "UE", ue, "Time", t_now)
                for ueas in ueases :
                    ueas [t_now] = e
                    debugging .log ("Adding UEAS", ueas)
                    possible_ueas .append (io .deep_copy (ueas))

        return possible_ueas

        '''
        #future measurements
        for t in range (t_now + 1, self .uepp_module .get_journey_end_time (ue) + 1, 1):
            if self .ussl == 'A':
                meas_data [t] = self .rsrpmp_module .predict_measurement_report (t, ue, lambda_th = self .lambda_threshold) 
                #print ('p', sorted(set ([c for c, _ in meas_data [t]])))
                #print ('a', sorted(set ([c for c, _ in self .rsrpmp_module .measurement_report (t, ue, lambda_th = self .lambda_threshold)])))
            elif self .ussl == 'C':
                meas_data [t] = self .rsrpmp_module .measurement_report (t, ue, lambda_th = self .lambda_threshold) 

            #delete empty measurement time instances
            if meas_data [t] == []:
                del meas_data [t]

        if len (meas_data) == 1:
            return []

        #create the graph
        g, src_set, dst_set = self .construct_graph_from (meas_data)

        #identify the possible ueas 
        possible_ueas = self .find_ueas_from (g, src_set, dst_set, ue)

        return possible_ueas
        '''

    @debugging .trace (level = 3)
    def next_target (self, ueas, time):
        ret = -1 if ueas is None else ueas [time]
        #ret = ueas [time]
        debugging .log ("finding next target from ueas", ueas, "as", ret)
        return ret

    @debugging .trace (level = 3)
    def i_gamma (self, ls):
        high = 0
        for t in ls :
            if ls [t] > self .beta :
                high += 1
        score = high / len (ls)
        debugging .log ("load sequence", ls, "score", score)
        return 1 if score <= self .gamma else 0

    @debugging .trace (level = 3)
    def calculate_system_health_status (self, p_u) :
        ls = {e:{} for e in self .enbcs_module .get_set_of_enbs ()}
        for ue in p_u:
            if p_u [ue] == None :
                continue
            #debugging .log ("current ueas for ue", ue, "is", p_u [ue])
            for t in p_u [ue] :
                c = p_u [ue] [t]
                if c == 0 :
                    continue
                if t not in ls [c] :
                    ls [c] [t] = 1
                else :
                    ls [c] [t] += 1
        health = 0
        for e in ls :
            if len (ls [e]):
                debugging .log ("evaluating gamma score for enb", e)
                health += self .i_gamma (ls [e])
        debugging .log ("system health status calculated as", health)
        return health

    @debugging .trace (level = 3)
    def evaluate_impact (self, ue, ueas, p_u) :
        temp = io .deep_copy (p_u)
        temp [ue] = ueas
        objective = self .calculate_system_health_status (temp)
        return objective

    @debugging .trace (level = 3)
    def greedy_choice (self, time, ue, serving, p_u):
        choices = self .find_possible_ueas (time, ue, serving) 
        debugging .log (len (choices), "possible ueas for ue", ue, "with serving enb", serving, "at time", time, ":", choices)
        if not len (choices):
            return p_u [ue]
        candidates = self .o_rc (time, ue)
        target = []
        ueas_rc = []
        for ueas in choices :
            candidate = self .next_target (ueas, time)
            if candidate in candidates :
                target .append (ueas)
                ueas_rc .append (candidate)
        debugging .log ("time", time, "ue", ue, "ueas_rc", ueas_rc)

        if not len (target):
            max_score = 0
            for ueas in choices :
                impact = self .evaluate_impact (ue, ueas, p_u)
                debugging .log ("time", time, "ue", ue,  "potential_target", self .next_target (ueas, time), "impact", impact)
                if impact >= max_score:
                    if impact > max_score :
                        max_score = impact
                        target .clear ()
                    target .append (ueas)
            #target = [min (score, key = lambda x : score [x])]

        ret = random .choice (target)
        #ret = min (target, key = lambda x : self .calculate_current_load (time, self .next_target (x, time)))

        debugging .log ("time", time, "ue", ue,  "selected_target", self .next_target (ret, time))
        p_u [ue] = ret
        return ret

    @debugging .trace (level = 3)
    def new_join (self, ue) :
        self .new_joins .add (ue)

    @debugging .trace (level = 2)
    def run (self, time):
        set_of_handover_adjustments = [] #[(t, ue, src, dst), ... ]
        to_remove = []
        for ue in self .all_ue_entered :
            if ue in self .uepp_module .get_set_of_ues () :
                _, serving_signal_dbm = self .rsrpmp_module .get_reading_for (ue, time, self .uecs_module .get_serving_enb_of (ue, time))

                self .ue_lsrl_data [ue] [time] = serving_signal_dbm
                debugging .log ("current lsrl status of ue", ue, "is", self .ue_lsrl_data [ue])

                if not self .uepp_module .ue_still_in_system (ue, time + 1) :
                    to_remove .append (ue)

            elif ue in self .uepp_6kmph_module .get_set_of_ues () :
                _, serving_signal_dbm = self .rsrpmp_6kmph_module .get_reading_for (ue, time, self .uecs_module .get_serving_enb_of (ue, time))
                
                self .ue_lsrl_data [ue] [time] = serving_signal_dbm
                debugging .log ("current lsrl status of ue", ue, "is", self .ue_lsrl_data [ue])

                if not self .uepp_6kmph_module .ue_still_in_system (ue, time + 1) :
                    to_remove .append (ue)

            else :
                debugging .log ("ue does not belong to any class. please debug")
                exit (0)

        self .temp_p_u = self .get_current_p_u ()
        flag = True
        adjusted_enbs = []
        adjusted_ues = []
        for ue in self .new_joins :
            debugging .log ("first time entry of ue", ue)
            ueas = self .greedy_choice (time, ue, -1, self .temp_p_u)
            set_of_handover_adjustments .append ((time, ue, -1, self .next_target (ueas, time)))
            self .temp_p_u [ue] = ueas
            self .all_ue_entered .append (ue)
        self .new_joins .clear()
        if self .case == "a" :
            #fully dynamic
            while flag :
                flag = False
                b_sorted = self .sort_enbs (self .temp_p_u, time)
                debugging .log ("time", time, "b_sorted", b_sorted)
                for e_i in b_sorted:
                    if e_i not in adjusted_enbs:
                        u_sorted = self .sort_ues (time, e_i)
                        debugging .log ("time", time, "u_sorted", u_sorted)
                        for u_j in u_sorted:
                            if u_j not in adjusted_ues:
                                ueas = self .greedy_choice (time, u_j, e_i, self .temp_p_u)
                                set_of_handover_adjustments .append ((time, u_j, e_i, self .next_target (ueas, time)))
                                debugging .log ("replacing ueas", self .temp_p_u [u_j], "with", ueas, "for ue", u_j)
                                self .temp_p_u [u_j] = ueas
                                flag = True
                                adjusted_ues .append (u_j)
                                break
                        if flag :
                            break
                        adjusted_enbs .append (e_i)
        elif self .case == "b" :
            #fully static
            while flag :
                flag = False
                b_sorted = self .sort_enbs (self .temp_p_u, time)
                debugging .log ("time", time, "b_sorted", b_sorted)
                for e_i in b_sorted:
                    u_sorted = self .sort_ues (time, e_i)
                    debugging .log ("time", time, "u_sorted", u_sorted)
                    for u_j in u_sorted:
                        ueas = self .greedy_choice (time, u_j, e_i, self .temp_p_u)
                        set_of_handover_adjustments .append ((time, u_j, e_i, self .next_target (ueas, time)))
                        self .temp_p_u [u_j] = ueas
        elif self .case == "c" :
            #semi dynamic
            while flag :
                flag = False
                b_sorted = self .sort_enbs (self .temp_p_u, time)
                debugging .log ("time", time, "b_sorted", b_sorted)
                for e_i in b_sorted:
                    if e_i not in adjusted_enbs:
                        u_sorted = self .sort_ues (time, e_i)
                        debugging .log ("time", time, "u_sorted", u_sorted)
                        for u_j in u_sorted:
                            ueas = self .greedy_choice (time, u_j, e_i, self .temp_p_u)
                            set_of_handover_adjustments .append ((time, u_j, e_i, self .next_target (ueas, time)))
                            self .temp_p_u [u_j] = ueas
                        adjusted_enbs .append (e_i)
                        flag = True
                        break

        debugging .log ("all ues in system", sorted (self .all_ue_entered), "total", len (self .all_ue_entered), "to remove", to_remove)
        for ue in to_remove:
            debugging .log ("removing ue", ue)
            set_of_handover_adjustments .append ((time, ue, self .uecs_module .get_serving_enb_of (ue, time), -1))
            self .temp_p_u [ue] = None
            self .all_ue_entered .remove (ue)

        debugging .log ("set of handover adjustments", set_of_handover_adjustments)
        self .set_current_p_u (self .temp_p_u)

        return set_of_handover_adjustments



if __name__ == '__main__':
    debugging .log ("LoadModule")
