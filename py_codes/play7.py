#!/usr/bin/python

import sys
import pickle
import numpy as np


n_ue = 250
beta = 15
gamma = 0.9

ues = [i for i in range (1, n_ue + 1, 1)]
with open ("indexed_used_enbs_LB", "rb") as f:
    used_enb_index = pickle .load (f)


expt = ["1a", "2a"]
names = {"1a":"INCR", "2a":"DECR"}
shift = {"1a":-.4, "2a":0}
wid = .4
'''
expt = ["1a", "2a", "uara", "dlba"]
names = {"1a":"INCR", "2a":"DECR", "uara":"M0", "dlba":"M1"}
shift = {"1a":-.5, "2a":-.25, "uara":0, "dlba":.25}
wid = .25
'''

def foo (c) :
    ueas_ind = {ue : {} for ue in ues}
    enb_loads = {}
    for t in c:
        for ue in c [t]:
            if c [t] [ue] == -1:
                continue
            else :
                s, d, rsrp, dbm = c [t] [ue]
                if d == -1 :
                    if s in enb_loads :
                        if t in enb_loads [s] :
                            enb_loads [s] [t] -= 1
                        elif t - 1 in enb_loads [s] :
                            enb_loads [s] [t] = enb_loads [s] [t - 1] - 1
                else :
                    ueas_ind [ue] [t] = d
                    if s != -1 :
                        if s in enb_loads :
                            if t in enb_loads [s] :
                                enb_loads [s] [t] -= 1
                            elif t - 1 in enb_loads [s] :
                                enb_loads [s] [t] = enb_loads [s] [t - 1] - 1
                    if d in enb_loads :
                        if t in enb_loads [d]:
                            enb_loads [d] [t] += 1
                        elif t - 1 in enb_loads [d] :
                            enb_loads [d] [t] = enb_loads [d] [t -1] + 1
                        else :
                            enb_loads [d] [t] = 1
                    else :
                        enb_loads [d] = {}
                        enb_loads [d] [t] = 1

    p_u = {ue:{} for ue in ues}
    for ue in ueas_ind :
        ind = sorted (ueas_ind [ue] .keys()) 
        for t1, t2 in zip (ind, ind [1:]) :
            for t in range (t1, t2, 1) :
                p_u [ue] [t] = ueas_ind [ue] [t1]
        #p_u [ue] [t2] = ueas_ind [ue] [t2]
    h_system = 0
    for enb in enb_loads :
        below_beta = len ([t for t in enb_loads [enb] if enb_loads [enb] [t] <= beta])
        total_used = len (enb_loads [enb])
        if (150 - total_used + below_beta) / 150>=gamma:# len (enb_loads [enb]) >= gamma :
            h_system += 1

    return p_u, h_system

def count_ho(ueas):
    count = 0
    for i in range (len (ueas) - 1) :
        if ueas [i] != ueas [i + 1] :
            count += 1
    return count

def count_pp(ueas, win = 4):
    count = 0
    skip = 0
    for i in range (len (ueas) - win) :
        if skip:
            skip -= 1
            continue
        wind = ueas [i : i + win]
        for e in range (len (wind) - 2) :
            if wind [e] in wind [e + 2 : ] and wind [e] != wind [e + 1]:
                count += 1
                #print (wind)
                skip = win
                break
    return count

def count_wr(ueas, win = 4):
    count = 0
    skip = 0
    for i in range (len (ueas) - win) :
        if skip :
            skip -= 1
            continue
        wind = ueas [i : i + win]
        if len (set (wind)) > 2 :
            count += 1
            skip = win
    return count

def bar (p_u) :
    ls = {}
    times = set()
    sum_pp, sum_wr, sum_ho = 0, 0, 0

    for ue in p_u :
        ueas = [p_u [ue] [t] for t in sorted (p_u [ue] .keys ())]
        #print ("UE", ue, "UEAS", ueas)
        sum_pp += count_pp (ueas)
        sum_wr += count_wr (ueas)
        sum_ho += count_ho (ueas)

        for t in p_u [ue] :
            times .add (t)
            if p_u [ue] [t] not in ls:
                ls [p_u [ue] [t]] = {}
                ls [p_u [ue] [t]] [t] = 1
            else :
                if t in ls [p_u [ue] [t]] :
                    ls [p_u [ue] [t]] [t] += 1
                else :
                    ls [p_u [ue] [t]] [t] = 1

    fairness = {t : 0 for t in sorted (times)}
    high_load = {t : 0 for t in sorted (times)}
    total = {t : 0 for t in sorted (times)}

    all_enbs = set ([])
    for t in sorted (times):
        sl = 0
        su = 0
        for e in ls :        
            if t in ls [e] :
                l = ls [e] [t]
                if l > beta :
                    high_load [t] += 1
                    total [t] += 1
                elif l > 0 :
                    total [t] += 1
                    all_enbs .add (e)
                su += l
                sl += l * l
        if sl != 0:
            fairness [t] = round ((su * su) / (sl * total [t]), 3)

    return sum_ho / n_ue, fairness, high_load, total, all_enbs, ls

def ue_times (c) :
    ueas_ind = {ue : {} for ue in ues}
    enb_loads = {}
    for t in c:
        for ue in c [t]:
            if c [t] [ue] != -1:
                s, d, rsrp, dbm = c [t] [ue]
                ueas_ind [ue] [t] = d

    p_u = {ue:{} for ue in ues}
    for ue in ueas_ind :
        ind = sorted (ueas_ind [ue] .keys()) 
        for t1, t2 in zip (ind, ind [1:]) :
            for t in range (t1, t2, 1) :
                p_u [ue] [t] = ueas_ind [ue] [t1]
        #print ("UEAS of UE", ue, " == ", [p_u [ue] [t] for t in sorted (p_u [ue])], ", size = ", len (p_u [ue]), "\n")
        #input()

    ue_time, range_time, used_time = {e:0 for e in used_enb_index}, {e:None for e in used_enb_index}, {e:[float("inf"), 0] for e in used_enb_index}
    ue_count, range_count = {e:0 for e in used_enb_index}, {e:0 for e in used_enb_index}

    for ue in p_u :
        distinct_enbs = set (p_u [ue] .values ())
        ueas = list (p_u [ue] .values ())
        ue_start_time = min (p_u [ue])
        for e in distinct_enbs :
            if e not in used_enb_index:
                continue
            ue_time [e] += ueas .count (e)
            ue_count [e] += 1

            f, l = None , 0
            for i, c in enumerate (ueas) :
                t = i + ue_start_time
                if c == e :
                    if not bool (f) : f = t
                    if t > l : l = t
            f_min, l_max = used_time [e]
            if f < f_min : f_min = f
            if l > l_max : l_max = l
            used_time [e] = [f_min, l_max]

    for e in ue_count :
        if ue_count [e] == 0:
            ue_count [e] = 1

    for e in used_time :
        if used_time [e] [0] == float ("inf") :
            used_time [e] [0] = 0
    
    return used_time, {e : (ue_time [e] / ue_count [e]) for e in ue_time}, {e : (used_time [e] [1] - used_time [e] [0] + 1) for e in used_time}, {}

import os
import subprocess
import matplotlib .pyplot as plt
plt.rcParams.update({'font.size': 16})
fig = plt .figure (1)

index = [str (i) for i in range (20)]
#c_vals = {}
bt = str (beta)
ues_str = str (n_ue)
times = [t for t in range (150)]

f_avg_used_time2 = {e:{} for e in expt}
f_avg_used_time = {e:{} for e in expt}
f_avg_ue_time = {e:{} for e in expt}
f_avg_range_time = {e:{} for e in expt}


for exp in expt :
    count = 0
    for i in index :
        if exp in ["1a", "2a"] :
            fname = ues_str + "_" + bt + "_" + exp + "_" + i + "_none_jula_a10.0_b" + bt + "_g0.1_p1_u" + ues_str + ".connection"
            fname_debug = ues_str + "_" + bt + "_" + exp + "_" + i + "_none_jula_a10.0_b" + bt + "_g0.1_p1_u" + ues_str + ".debug"
            dname = "/home/external/Python-Data-Processing/paris-t1-randSel/" + ues_str +"_" + bt + "_" + exp + "_" + i + "_none_jula_a10.0_b" + bt + "_g0.1_p1_u" + ues_str +"/"
        elif exp in ["uara", "dlba"]:
            fname = ues_str + "_" + exp + "_" + bt + "_" + i + "_a3_" + exp + "_a0_b" + bt + "_g0_p1_u" + ues_str + ".connection"
            fname_debug = ues_str + "_" + exp + "_" + bt + "_" + i + "_a3_" + exp + "_a0_b" + bt + "_g0_p1_u" + ues_str + ".debug"
            dname = "/home/external/Python-Data-Processing/paris-t1-randSel/" + ues_str + "_" + exp + "_" + bt + "_" + i + "_a3_" + exp + "_a0_b" + bt + "_g0_p1_u" + ues_str + "/"

        if os .path .exists (dname + fname) :
            print (True, dname + fname)
            count += 1
        else :
            print (False, dname + fname)
            continue

        f = open (dname + fname,  "rb")
        c = pickle .load (f)
        f .close ()

        used_time, avg_ue_time, avg_used_time, avg_range_time = ue_times (c)

        for e in avg_ue_time :
            if e not in f_avg_ue_time [exp] :
                f_avg_ue_time [exp] [e] = 0
            f_avg_ue_time [exp] [e] += avg_ue_time [e]

        for e in avg_used_time :
            if e not in f_avg_used_time [exp] :
                f_avg_used_time [exp] [e] = 0
                f_avg_used_time2 [exp] [e] = [0,0]
            f_avg_used_time [exp] [e] += avg_used_time [e]

        for e in used_time :
            if e not in f_avg_used_time2 [exp] :
                f_avg_used_time2 [exp] [e] = [0,0]
            f_avg_used_time2 [exp] [e] [0] += used_time [e] [0]
            f_avg_used_time2 [exp] [e] [1] += used_time [e] [1]

        for e in avg_range_time :
            if e not in f_avg_range_time [exp] :
                f_avg_range_time [exp] [e] = 0
            f_avg_range_time [exp] [e] += avg_range_time [e]

    for e in f_avg_ue_time [exp] :
        f_avg_ue_time [exp] [e] /= count

    for e in f_avg_used_time [exp] :
        f_avg_used_time [exp] [e] /= count
        f_avg_used_time2 [exp] [e] [0] /= count
        f_avg_used_time2 [exp] [e] [1] /= count

    
    col = {"1a":"black", "2a":"blue"}
    flag = True
    
    sh = {"1a": .25, "2a":-.25}
    for e in f_avg_used_time2 [exp]:
        if flag : 
            plt .plot (f_avg_used_time2 [exp] [e], [used_enb_index [e] + sh [exp] , used_enb_index [e] + sh [exp]], color = col [exp], lw= 2, label = names [exp])
            flag = False
        if not flag : plt .plot (f_avg_used_time2 [exp] [e], [used_enb_index [e] + sh [exp] , used_enb_index [e] + sh [exp]], color = col [exp], lw= 2)
        if exp == '1a' : plt .annotate (str (int (f_avg_used_time [exp] [e] + 0.5)) + ' / ' + str (int (f_avg_ue_time [exp] [e] + 0.5)), (6, used_enb_index [e]), color = col [exp])
        if exp == '2a' : plt .annotate (str (int (f_avg_used_time [exp] [e] + 0.5)) + ' / ' + str (int (f_avg_ue_time [exp] [e] + 0.5)), (15, used_enb_index [e]), color = col [exp])
        if exp == '1a' : plt .annotate ('e' + str (used_enb_index [e]), (0, used_enb_index [e]))
    #plt .bar ([used_enb_index [e] + shift [exp] for e in sorted (f_avg_ue_time [exp] .keys ())], [f_avg_ue_time [exp] [e] for e in sorted (f_avg_ue_time [exp] .keys ())], label = names [exp], width=wid)
    #plt .bar ([used_enb_index [e] + shift [exp] for e in sorted (f_avg_used_time [exp] .keys ())], [f_avg_used_time [exp] [e] for e in sorted (f_avg_used_time [exp] .keys ())], label = names [exp], width=wid)
    
with open ("enb_ranges_positions", "rb") as f:
    ranges = pickle .load (f)

flag = True
for e in ranges :
    if flag : 
        plt .plot ([ranges [e] [0], ranges [e] [1] + 39], [used_enb_index [e], used_enb_index [e]], color ='red', lw=1, label = "eNB range")
        flag = False
    else : 
        plt .plot ([ranges [e] [0], ranges [e] [1] + 39], [used_enb_index [e], used_enb_index [e]], color ='red', lw=1)

plt .annotate ("<<-- Values: eNB-id  used-time / dwell-time   used-time / dwell-time", (70, 5))
fig .legend (ncol = 4)
plt .ylabel ("Enb ids")
plt .xlabel ("Avg eNB Used-Time")
#plt .ylim ([0,60])


if len (sys .argv) == 2 :
    fig .savefig ("/home/external/Python-Data-Processing/" + str(len (ues)) + sys .argv [1] + ".pdf")
    fig .savefig ("/home/external/Python-Data-Processing/" + str(len (ues)) + sys .argv [1] + ".eps")

else :
    print (len (sys .argv), sys .argv)
    plt .show ()

