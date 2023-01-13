#!/usr/bin/python
import sys
import pickle
import random
import copy
import networkx as nx
import itertools as it
import my_modules.my_tracing as debugging
debugging .trace (level = 2) .min_level = 1
debugging .log .DEBUG = False


@debugging .trace (level = 2)
def update_journal (journal, time, value):
    journal [time] = copy .deepcopy (value)
    return True 

@debugging .trace (level = 2)
def encode_node (c_and_p, t):
    c, p = c_and_p
    return int (t * 1e6 + p * 1e3 + c)

@debugging .trace (level = 2)
def decode_node (n):
    t = int (n / 1e6)
    n = int (n % 1e6)
    p = int (n / 1e3)
    c = int (n % 1e3)
    return (t, c, p)

@debugging .trace (level = 2)
def construct_graph_from (timed_meas_data):
    G = nx .DiGraph()
    weighted_edges = []
    time_sequence = sorted (timed_meas_data .keys ())

    for tA, tB in zip (time_sequence, time_sequence [1:]):
        for x, y in it .product (timed_meas_data [tA], timed_meas_data [tB]):
            edge_weight = 1
            if x [0] == y [0]:
                edge_weight = 0
            weighted_edges .append ((encode_node (x, tA), encode_node (y, tB), edge_weight))

    G .add_weighted_edges_from (weighted_edges)

    return G, [encode_node (n, time_sequence [0]) for n in timed_meas_data [time_sequence [0]]], [encode_node (n, time_sequence [-1]) for n in timed_meas_data [time_sequence [-1]]]

@debugging .trace (level = 2)
def find_UEAS_from (G, src, dst):
    all_seq = []

    for s, d in it .product (src, dst):
        debugging .log ("finding path from", s, "to", d)
        path = nx .dijkstra_path (G, s, d)

        seq = []
        t, c, p = decode_node (path [0])
        seq .append ((t,c))
        for n1, n2 in zip (path, path[1:]):
            t1, c1, p1 = decode_node (n1)
            t2, c2, p2 = decode_node (n2)
            if c1 == c2 :
                continue
            else : 
                seq .append ((t2, c2))
        path_weight = nx .dijkstra_path_length (G, s, d)
        all_seq .append ((seq, path_weight))

    return [ueas for ueas in all_seq if ueas [1] == min (all_seq, key = lambda x: x[1]) [1]]

@debugging .trace (level = 2)
def compute_next_handover_candidates (t_now, ue, src, meas_dict, journey_length, lambda_threshold = -85):
    ue_pos = t_now - ue [1] + 1
    journey_end_time = ue [1] + journey_length
    meas_data = {}

    #mesurements at time t_now in ue_pos
    meas_data [t_now] = [(cell, strength) for cell, strength, strength_real in meas_dict [ue_pos] [t_now] 
                                            if strength_real >= lambda_threshold]

    if src in [c for c, p in meas_data [t_now]] or meas_data [t_now] == []:
        return [src]

    #future measurements
    for t in range (t_now + 1, journey_end_time + 1, 1):
        meas_data [t] = [(cell, strength) for cell, strength, strength_real in meas_dict [ue_pos + t - t_now] [t] 
                                            if strength_real >= lambda_threshold]
        #delete empty measurement time instances
        if meas_data [t] == []:
            del meas_data [t]

    if len (meas_data) == 1:
        return [src]

    #create the graph
    G, src_set, dst_set = construct_graph_from (meas_data)
    #for t in meas_data:
    #    debugging .log (t, ':', meas_data [t])

    #identify the possible ueas 
    #debugging .log ("UEAS for", ue)
    possible_ueas = find_UEAS_from (G, src_set, dst_set)
    #debugging .log ("ueas_all", possible_ueas)

    #identify the candidates
    candidates = [seq [0] [1] for seq, w in possible_ueas]

    return candidates

@debugging .trace (level = 2)
def calculate_load_score (t, e, ue_conn_data, A_e_overlap, A_e, meas_data, lambda_threshold):
    """This function calculates the load scores for a 
    particuar eNB e at time t based on the set of vehicles (V_e_t) 
    under that eNB at that time"""
    V_e_t = [ue for ue in ue_conn_data if ue_conn_data [ue] == e]
    B_e_t = {}
    for v in V_e_t:
        v_pos = t - v [1] + 1
        B_e_t [v] = [e_i for e_i, _, dbm in meas_data [v_pos] [t] if dbm >= lambda_threshold]

    total = 0
    for v in V_e_t:
        if len (B_e_t [v]) > 1:
            total += float (len (B_e_t [v])) / len (A_e_overlap)
    if len (V_e_t) == 0:
        return 0
    return float (total) / len (V_e_t)

@debugging .trace (level = 2) 
def dummy_load_score (type):
    if type == "random":
        score = random .uniform (0, 1)
    elif type == "simple":
        score = 1
    else : 
        score = float ('nan')

    return score

@debugging .trace (level = 2)
def choose_target (t, candidates, ue_conn_data, overlap_data, aoi_data, meas_data, lambda_threshold):
    load_scores = {}
    for c in candidates:
        #load_scores [c] = dummy_load_score ("random")
        #load_scores [c] = dummy_load_score ("simple")
        load_scores [c] = calculate_load_score (t, c, ue_conn_data, overlap_data [c], aoi_data [c], meas_data, lambda_threshold)
    
    dst = min (load_scores, key = load_scores .get)

    return dst

@debugging .trace (level = 2)
def simulate_step_at (t_now, meas_dict, ue_connection_dict, enb_load_dict, journey_length, overlap_data, aoi_data, lambda_threshold):
    for ue in ue_connection_dict:
        if t_now < ue [1] or t_now > ue [1] + journey_length:
            continue
        elif t_now == ue [1] + journey_length:
            enb_load_dict [ue_connection_dict [ue]] -= 1
            ue_connection_dict [ue] = -1
            continue

        if ue_connection_dict [ue] != -1:
            debugging .log (t_now, ue, ue_connection_dict [ue], 
                        [(enb, pow_real) for enb, _, pow_real in meas_dict [t_now - ue [1] + 1] [t_now] 
                                            if enb == ue_connection_dict [ue]])

        debugging .log ("UE", ue)
        src = ue_connection_dict [ue]
        candidates = compute_next_handover_candidates (t_now, ue, src, meas_dict, journey_length)

        dst = choose_target (t_now, candidates, ue_connection_dict, overlap_data, aoi_data, meas_dict, lambda_threshold)
        
        if src != dst:
            debugging .log ("candidates", candidates)
            debugging .log ("Handover:", 'from', src, 'to', dst, "[time]",t_now)
            ue_connection_dict [ue] = dst
            if src != -1:
                enb_load_dict [src] -= 1
            enb_load_dict [dst] += 1
        else :
            debugging .log ("Skipping:", "connected at", dst, "[time]",t_now)

    debugging .log ('conn_status', ue_connection_dict)
    debugging .log ('load_status', enb_load_dict)
    return ue_connection_dict, enb_load_dict

@debugging .trace (level = 2)
def calculate_aoi (enbs, meas_dict, start_time = 0, lambda_val = -85):
    A_e_dict = {}
    for enb in enbs:
        tmp_aoi = []
        time = start_time
        for pos in sorted (meas_dict .keys ()):
            pos_meas_data = meas_dict [pos]
            enbs = {e : pow_real for e, _, pow_real in pos_meas_data [time] if pow_real >= lambda_val}
            if enb in enbs:
                tmp_aoi .append (pos)
            time += 1

        if tmp_aoi != []:
            A_e_dict [enb] = tmp_aoi

    return A_e_dict

@debugging .trace (level = 2)
def calculate_overlaps (A_e_dict):
    A_e_overlap_dict = {}
    enbs = sorted (A_e_dict .keys())
    for enb in enbs:
        A_e_overlap_dict [enb] = {}
        A_enb = A_e_dict [enb]
        for pos in A_enb:
            tmp_overlaps = set ([])
            for e in enbs:
                if pos in A_e_dict [e]:
                    tmp_overlaps .add (e)

            A_e_overlap_dict [enb] [pos] = tmp_overlaps

    return A_e_overlap_dict

@debugging .trace (level = 2)
def read_from_file (case, context):
    with open (context + '/' + context + '_' + case + '_' + 'pickle_dump', "rb") as f:
        return pickle .load (f)

@debugging .trace (level = 1)
def simulate (args):
    """This function simulates the system"""
    context = args [0]
    duration = 150
    journey_length = 108
    num_ues = 100
    lambda_value = -85
    enb_pos, rsrp_meas = [read_from_file (case, context) for case in ['enb_pos', 'rsrp']]
    time_instances = [t for t in range (duration)]
    set_of_enbs = set (enb_pos .keys ())
    set_of_ues = [(index + 1, st_time) for st_time, index in zip (sorted ([int(round (random.uniform (0,41))) for _ in range (num_ues)]), range (num_ues))]
    P = [i for i in range (108)]

    A_e_dict = calculate_aoi (set_of_enbs, rsrp_meas, lambda_val = lambda_value)
    A_e_overlap_dict = calculate_overlaps (A_e_dict)

    handover_journal = {t:{} for t in time_instances}
    current_load_journal = {t:{} for t in time_instances}
    write_flag = False

    current_loads = {enb:0 for enb in set_of_enbs}
    current_conn_dict = {ue:-1 for ue in set_of_ues}

    for t in time_instances:
        debugging .log ('Simulation time', t)
        current_conn_dict, current_loads = simulate_step_at (t, rsrp_meas, current_conn_dict, current_loads, 
                                                                journey_length, A_e_overlap_dict, A_e_dict, lambda_value)

        if write_flag :
            update_journal (handover_journal, t, current_conn_dict)
            update_journal (current_load_journal, t, current_loads)

    if write_flag :
        with open (context + "/current_load_journal_pickle_dump", "wb") as f_cl, 
                open (context + "/handover_journal_pickle_dump", "wb") as f_cc:
            pickle .dump (current_load_journal, f_cl, pickle .HIGHEST_PROTOCOL)
            pickle .dump (handover_journal, f_cc, pickle .HIGHEST_PROTOCOL)

