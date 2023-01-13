#!/usr/bin/python

import sys
import networkx as nx
import itertools as it
import numpy as np
from sklearn.preprocessing import normalize
import pickle
import random

def parse_ranges (fname):
    with open (fname) as f:
        fl = f .readlines ()

    ue_pos_dict = {} #UE-id as key to ue position
    enb_pos_dict = {} #enb-id as key to enb position
    measurement_rsrp_dict = {} #ue-id as key to a dictionary on time
    measurement_rsrq_dict = {} #ue-id as key to a dictionary on time 

    for l in fl:
        if l .find (" imsi=") != -1:
            d = l .split ()
            time = int (float (d [0]))
            ue = int (d [1] .split ('=') [1])
            enb = int (d [2] .split ('=') [1])
            rsrp = int (d [4] .split ('=') [1])
            rsrp_dbm = int (d [5] [1:])
            rsrq = int (d[7] .split ('=') [1])
            rsrq_db = float (d [8] [1:])

            if ue not in measurement_rsrp_dict:
                measurement_rsrp_dict [ue] = {}
                measurement_rsrq_dict [ue] = {}
            if time not in measurement_rsrp_dict [ue]:
                measurement_rsrp_dict [ue] [time] = set ([])
                measurement_rsrq_dict [ue] [time] = set ([])
            measurement_rsrp_dict [ue] [time] .add ((enb, rsrp, rsrp_dbm))
            measurement_rsrq_dict [ue] [time] .add ((enb, rsrq, rsrq_db))
            
            if enb not in enb_pos_dict:
                enb_x, enb_y = [float (v) for v in d [3].split ('=') [1] [1:-1].split (',')]
                enb_pos_dict [enb] = (enb_x, enb_y)

        elif l .find ("0:: C") != -1:
            d = l .split ()
            ue_x = float (d [3] .split ('=') [1] [:-1])
            ue_y = float (d [4] .split ('=') [1])
            ue = int (d [5] .split (':') [1])
            
            ue_pos_dict [ue] = (ue_x, ue_y)

    return ue_pos_dict, enb_pos_dict, measurement_rsrp_dict, measurement_rsrq_dict


def write_to_file (case, data_dict, context):
    with open (context + '/' + context + '_' + case, 'w') as f, open (context + '/' + context + '_' + case + '_' + 'pickle_dump', 'w') as fp:
        if (case == 'ue_pos') or (case == 'enb_pos'):
            for k in sorted (data_dict .keys ()):
                print >> f, k, data_dict [k]

        if (case == 'rsrp') or (case == 'rsrq'):
            for k in sorted (data_dict .keys ()):
                ue_time_data = data_dict [k]
                for t in sorted (ue_time_data .keys ()):
                    print >> f, k, t, ue_time_data [t]
        pickle .dump (data_dict, fp)
    return True


def read_from_file (case, context):
    with open (context + '/' + context + '_' + case + '_' + 'pickle_dump') as f:
        return pickle .load (f)


def calculate_timed_meas_from (meas_data_dict, start_time, lambda_thrshld):
    timed_meas_data = {}
    t = start_time

    for ue in sorted (meas_data_dict):
        timed_meas_data [t] = [(cell, strength) for cell, strength, strength_real in meas_data_dict [ue] [t] if strength_real >= lambda_thrshld]
        if len(timed_meas_data [t]) == 0:
            del timed_meas_data [t]
        t += 1

    return timed_meas_data


def encode_node ((c ,p), t):
    return int (t * 1e6 + p * 1e3 + c)


def decode_node (n):
    t = int (n / 1e6)
    n = int (n % 1e6)
    p = int (n / 1e3)
    c = int (n % 1e3)
    return (t, c, p)


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


def find_UEAS_from (G, src, dst):
    all_seq = []

    for s, d in it .product (src, dst):
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


def calculate_load (ue_pos_data, enb_pos_data, meas_data, journey_start_times = [0], lambda_val = -85, random_selection = True):
    ues = sorted (ue_pos_data .keys())
    enbs = sorted (enb_pos_data .keys())
    
    ueas_dict = {}
    for index, journey_start_time in enumerate (journey_start_times):
        timed_meas = calculate_timed_meas_from (meas_data, journey_start_time, lambda_val)
        G, src_set, dst_set = construct_graph_from (timed_meas)
        possible_ueas = find_UEAS_from (G, src_set, dst_set)
        if random_selection:
            ueas_dict [(index, journey_start_time)] = random .sample (set ([(tuple(v[0]), v[1]) for v in possible_ueas]), 1) [0]
        else :
            ueas_dict [(index, journey_start_time)] =  possible_ueas [0]

    load_matrix = {}
    vehicle_matrix = {}
    for enb in enbs:
        load_matrix [enb] = [0] * (max (journey_start_times) + len (ues))
        vehicle_matrix [enb] = {}

    for index, st in ueas_dict:
        ueas = ueas_dict [(index, st)] [0]
        for i, j in zip (ueas, ueas [1:]):
            for x in range (i [0], j [0], 1):
                load_matrix [i [1]] [x] += 1
                if x in vehicle_matrix [i [1]]:
                    vehicle_matrix [i [1]] [x] .append ((index, st))
                else :
                    vehicle_matrix [i [1]] [x] = [(index, st)]

    for enb in load_matrix:
        non_zero_list = [v for v in load_matrix [enb] if v != 0]
        if len (non_zero_list) != 0:
            print enb, round (np .mean (non_zero_list), 2), max (non_zero_list), min (non_zero_list), round (np .std (non_zero_list), 2)

            print 'eNB', enb
            for k in sorted (vehicle_matrix [enb]):
                print k, vehicle_matrix [enb] [k]
            print ''

    return load_matrix, vehicle_matrix, [(vehicle_index, start_time) for vehicle_index, start_time in enumerate (journey_start_times)]


def find_area_of_influence (enb_list, meas_dict, start_time = 0, lambda_val = -85):
    AoI = {}
    for enb in enb_list:
        AoI [enb] = []
        time = start_time
        for ue in sorted (meas_dict .keys ()):
            ue_meas_data = meas_dict [ue]
            enbs = {e : pow_real for e, _, pow_real in ue_meas_data [time] if pow_real >= lambda_val}
            if enb in enbs:
                AoI [enb] .append (time)
            time += 1
        if AoI [enb] == []:
            del AoI [enb]
        else :
            print enb, AoI [enb]
    return AoI


def find_overlapping_AoI (enb_AoI_data):
    overlapping_AoI_dict = {}
    enbs = sorted (enb_AoI_data .keys())
    for enb in enbs:
        overlapping_AoI_dict [enb] = {}
        enb_AoI_times = enb_AoI_data [enb]
        for time in enb_AoI_times:
            overlaps = set ([])
            for e in enbs:
                if time in enb_AoI_data [e]:
                    overlaps .add (e)
            overlapping_AoI_dict [enb] [time] = set (filter (lambda x: x != enb, overlaps))
    return overlapping_AoI_dict


def find_overlapping_eNBs (enb_AoI_data, alpha_val = 50):
    overlapping_AoI_eNB_dict = {}
    enbs = sorted (enb_AoI_data .keys())
    for enb in enbs:
        tmp_set = set ([])
        for e_i in enbs:
            if e_i != enb:
                percentage_coverage = (len (set (enb_AoI_data [enb]) .intersection (set(enb_AoI_data [e_i]))) / float (len (set (enb_AoI_data [enb])))) * 100
                if percentage_coverage != 0 and percentage_coverage >= alpha_val:
                    tmp_set .add (e_i)
        overlapping_AoI_eNB_dict [enb] = tmp_set

    return overlapping_AoI_eNB_dict


def calculate_B_e_v (vehicles_data, AoI_data, alpha = 50):
    B_e_v = {}
    overlap_data = find_overlapping_eNBs (Aoi_data, alpha_val = alpha)
    enbs = overlap_data .keys()

    for vehicle, st in vehicles_data:
        for enb in enbs:
            tmp_set = set ([])
            for e_i in overlap_data [enb]:
                if (t - st)  in AoI_data [e_i]:
                    tmp_set .add (e_i)
            if tmp_set:
                B_e_v [(enb, vehicle)] = tmp_set
                print (enb, vehicle)
    return B_e_v


def calculate_load_score (load_vals, method = 'min-max', context = ''):
    #normalized_load_vals = list (normalize (np .array(load_vals) [:, np.newaxis], axis=0) .ravel ())
    if method == 'min-max':
        if max (load_vals) == min (load_vals):
            normalized_load_vals = [1.0 if load_vals [0] else 0.0] * len (load_vals)
        else :
            normalized_load_vals = [(v - min (load_vals))/ (max (load_vals) - min (load_vals)) for v in load_vals]
    elif method == 'average':
        if sum (load_vals) == 0:
            normalized_load_vals = [0.0] * len (load_vals)
        else :
            normalized_load_vals = [float(l) / sum (load_vals) for l in load_vals]

    #own_norm_val, min_norm_val, max_norm_val, mean_norm_val, sd_norm_val
    score = [round (v, 3) for v in [normalized_load_vals [0], min (normalized_load_vals), max (normalized_load_vals), np .mean (normalized_load_vals), np .std (normalized_load_vals)]]
    return score


def calculate_load_scores (load_data, overlap_data, overlap_percentage_threshold = 50, norm_method = 'min-max'):
    load_scores_dict = {}
    load_scores_partial_dict = {}
    enbs = overlap_data .keys()
    for enb in enbs:
        load_scores_dict [enb] = {}
        times = overlap_data [enb] .keys()
        enb_presence_count_dict = {enb:len (times)}
        for t in times:
            for e in overlap_data [enb] [t]:
                if e in enb_presence_count_dict:
                    enb_presence_count_dict [e] += 1
                else :
                    enb_presence_count_dict [e] = 1

            load_vals = [load_data [enb] [t]]
            for e in overlap_data [enb] [t]:
                load_vals .append (load_data [e] [t])
            load_scores_dict [enb] [t] = (load_vals, calculate_load_score (load_vals, context = str (enb) + '-' + str (t) + ' - all-enb case', method = norm_method))
            #print enb, t, load_vals [0], len (load_vals), load_scores_dict [enb] [t]

        enb_percentage_vals = [(e, enb_presence_count_dict [e] * 100 / enb_presence_count_dict [enb]) for e in enb_presence_count_dict]
        load_scores_partial_dict [enb] = {}
        for t in times:
            load_vals = [load_data [enb] [t]]
            for e, p in enb_percentage_vals:
                if e in overlap_data [enb] [t] and p >= overlap_percentage_threshold:
                    load_vals .append (load_data [e] [t])
            load_scores_partial_dict [enb] [t] = (load_vals, calculate_load_score (load_vals, context = str (enb) + '-' + str (t) + ' - percent case', method = norm_method))
            #print enb, t, load_vals [0], len (load_vals), load_scores_partial_dict [enb] [t]
    return load_scores_dict, load_scores_partial_dict


def partition (arr, n):
    l = len (arr)
    i = 0
    while i < l:
        if i + n < l:
            yield arr [i : i + n]
        else :
            yield arr [i:]
        i += n


if __name__ == '__main__':
    sub_command = sys .argv [1]
    lambda_dbm_val = -85
    percentage_th = 0
    randomSelection = True

    if sub_command == 'write-file':
        ue_pos, enb_pos, rsrp_meas, rsrq_meas = parse_ranges (sys .argv [2])
        randomSelection = True if sys.argv [-2] == 'random' else False
        load_matrix_dict, vehicle_matrix_dict, vehicles_data = calculate_load (ue_pos, enb_pos, rsrp_meas, journey_start_times = sorted([int(round(random.uniform (0,41))) for _ in range(100)]), lambda_val = lambda_dbm_val, random_selection = randomSelection)
        enb_AoI_dict = find_area_of_influence (sorted (enb_pos .keys ()), rsrp_meas, start_time=0, lambda_val = lambda_dbm_val)
        overlapping_enb_AoI = find_overlapping_AoI (enb_AoI_dict)

        context = sys .argv [-1]
        if all ([write_to_file (case, var, context) for case, var in zip (['vehicles_data', 'ue_pos', 'enb_pos', 'rsrp', 'rsrq', 'load_matrix', 'vehicle_matrix', 'enb_AoI', 'enb_overlap'], [vehicles_data, ue_pos, enb_pos, rsrp_meas, rsrq_meas, load_matrix_dict, vehicle_matrix_dict, enb_AoI_dict, overlapping_enb_AoI])]):
            print "Write Complete."

        exit (0)

    if sub_command == 'graph':
        randomSelection = True if sys.argv [-1] == 'random' else False
        ue_pos, enb_pos, rsrp_meas, rsrq_meas = parse_ranges (sys .argv [2])
        load_matrix_dict, vehicle_matrix_dict, vehicles_data = calculate_load (ue_pos, enb_pos, rsrp_meas, journey_start_times = sorted([int(round(random.uniform (0,41))) for _ in range(100)]), lambda_val = lambda_dbm_val, random_selection = randomSelection)
        enb_AoI_dict = find_area_of_influence (sorted (enb_pos .keys ()), rsrp_meas, start_time=0, lambda_val = lambda_dbm_val)
        overlapping_enb_AoI = find_overlapping_AoI (enb_AoI_dict)
        load_scores_all, load_score_percentage = calculate_load_scores (load_matrix_dict, overlapping_enb_AoI, overlap_percentage_threshold = percentage_th)
        exit (0)

    if sub_command == 'graph-from-file':
        context = sys .argv [-1] 
        percentage_th = int (sys .argv [-2])
        vehicles_data, ue_pos, enb_pos, rsrp_meas, rsrq_meas, load_matrix_dict, vehicle_matrix_dict, enb_AoI_dict, overlapping_enb_AoI = [read_from_file (case, context) for case in ['vehicles_data', 'ue_pos', 'enb_pos', 'rsrp', 'rsrq', 'load_matrix', 'vehicle_matrix', 'enb_AoI', 'enb_overlap']]
        load_scores_all, load_scores_percentage = calculate_load_scores (load_matrix_dict, overlapping_enb_AoI, overlap_percentage_threshold = percentage_th)

        print "own_norm_val, min_norm_val, max_norm_val, mean_norm_val, sd_norm_val"
        print "percentage_threshold :", percentage_th
        _out_sd, _out_diff, _out_own, _enb = [], [], [], []
        for e in sorted (load_scores_percentage):
            _own, _sd, _mean = [], [], []
            for t in load_scores_percentage [e]:
                _sd .append (load_scores_percentage [e] [t] [1] [-1])
                _mean .append (load_scores_percentage [e] [t] [1] [-2])
                _own .append (load_scores_percentage [e] [t] [1] [0])
            '''
            print 'eNB:', e
            print load_scores_percentage [e]
            print load_scores_all [e]
            print len (load_scores_percentage [e]), len (load_scores_all [e])'''
            _enb .append (str (e) + '(' + str (len (load_scores_percentage [e] [load_scores_percentage [e] .keys () [0]] [0]) - 1) + ')')
            _out_sd .append (str (round (np .mean (_sd), 3)))
            _out_diff .append (str (round (np .mean ([u - v for u, v in zip (_own, _mean)]), 3)))
            _out_own .append (str (round (np .mean (_own), 3)))

        '''num_of_cols = 5
        print '\\begin{tabular}{|' + 'c|' * 2 * (1 + num_of_cols) + '} \hline'
        for _part_enb, _part_sd, _part_diff in zip (partition (_enb, num_of_cols), partition(_out_sd, num_of_cols), partition (_out_diff, num_of_cols)):
            print '\t\multicolumn{2}{|c|}{eNB-ID(\#options)} &', ' & ' .join (['\multicolumn{2}{c|}{' + v + '}' for v in _part_enb]), '\\\\ \hline'
            print '\tSD & Dist &', ' & ' .join ([u + ' & ' + v for u, v in zip (_part_sd, _part_diff)]), '\\\\ \hline'
            #print ' & ' .join (_out_diff)
        print "\end{tabular}"'''

        print "min_val, max_val, mean_val, sd_val"
        for d, name in zip ([[float (x) for x in dset] for dset in _out_own, _out_diff, _out_sd], ['own_val', 'difference_val', 'SD val']):
            print name, ':',
            print ' & ' .join ([str (round (v, 3)) for v in min (d), max (d), np .mean (d), np .std (d)])

        #calculate_B_e_v (vehicles_data, enb_AoI_dict, overlap_percentage_threshold = percentage_th)

        #for each e and for each t, do the following
        enbs = vehicle_matrix_dict. keys ()
        times = set.union(*[set(vehicle_matrix_dict [e] .keys ()) for e in enbs])
        overlap_data = find_overlapping_eNBs (enb_AoI_dict, alpha_val = 0)
        print enbs
        print times
        for e in enbs:
            for t in times:
                #print 'time', t,
                #calculate V_e_t - vehicles connected to e at time t
                if t not in vehicle_matrix_dict [e]:
                    #print 'skip',
                    continue
                V_e_t = vehicle_matrix_dict [e] [t]
                print 'vet', e, t, V_e_t

                #calculate B_v_e_t for all v from V_e_t - enbs (e_i) for which v is in the AoI of e_i including e itself
                B_v_e_t = {}
                for v, s in V_e_t:
                    if v not in overlapping_enb_AoI [e]:
                        #print 'skip2'
                        continue
                    print e,v,overlapping_enb_AoI [e] [v]
                    B_v_e_t [(v,s)] = overlapping_enb_AoI [e] [v] .union(set([e]))

                if B_v_e_t == {}:
                    print 'skip bvet', e,t
                    continue
                print 'bvet', B_v_e_t

                #load score (l_e_t) calculation for e at time t
                #sum all l_v_e_t for all v from V_e_t
                total = 0
                for v,s in B_v_e_t:
                    #if len (overlap_data [e]) == 0:
                    #    total += 0
                    #    continue
                    l_v_e_t = len (B_v_e_t [(v,s)]) / float (len (overlap_data [e]))
                    total += l_v_e_t
                #divide the sum by the len (V_e_t) maybe?
                score_e_t =  round (total / float (len (V_e_t)), 3) #maybe?

                print 'lscore', e, t, score_e_t

        exit (0)


'''
Example Commands

$mkdir paris-t1
-make sure the trace file "paris-range-output" exists
$ python parse-ranges.py write-file paris-range-output paris-t1 # writes parsed data to files (two files each, one text and one binary) for future use
$ python parse-ranges.py graph-from-file paris-t1 # loads parsed data from file and executes
$ python parse-ranges.py graph paris-range-output  # just does the calculations 
'''

'''
for enb1, enb2 in it .combinations (enbs, 2):
    enb1_aoi = set (enb_AoI_data [enb1])
    enb2_aoi = set (enb_AoI_data [enb2])

    overlap = list (enb1_aoi .intersection (enb2_aoi))
    if overlap:
        overlapping_AoI_dict [(enb1, enb2)] = overlap
        print enb1, enb2, overlap 
'''
