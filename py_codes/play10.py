#!/usr/bin/python

import sys
import pickle
import numpy as np

n_ue = 250
beta = 20
gamma = 0.2
gamma_val = 0.2


ues = [i for i in range (1, n_ue + 1, 1)]
with open ("indexed_used_enbs_LB", "rb") as f:
    used_enb_index = pickle .load (f)

with open ("enb_ranges_positions", "rb") as f:
    ranges = pickle .load (f)

with open ("enb_anysignal_range", "rb") as f :
    ranges_any = pickle .load (f)

expt = ["1a"]
#expt = ["uara"]
#expt = ["dlba"]
#expt = ["ussl-a"]
names = {"1a":"INCR", "2a":"DECR", "uara":"M1", "dlba":"M2", "ussl-a":"USSL-A"}
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
        for enb in enb_loads :
            if t not in enb_loads [enb]:
                if t - 1 in enb_loads [enb] :
                    enb_loads [enb] [t] = enb_loads [enb] [t-1]

    p_u = {ue:{} for ue in ues}
    for ue in ueas_ind :
        ind = sorted (ueas_ind [ue] .keys()) 
        for t1, t2 in zip (ind, ind [1:]) :
            for t in range (t1, t2, 1) :
                p_u [ue] [t] = ueas_ind [ue] [t1]
        #p_u [ue] [t2] = ueas_ind [ue] [t2]

    h_system = 0
    for enb in enb_loads :
        above_beta = len ([t for t in enb_loads [enb] if enb_loads [enb] [t] > beta])
        #total_used = len (enb_loads [enb])
        #if (150 - total_used + below_beta) / 150 >=gamma:# len (enb_loads [enb]) >= gamma :
        #if enb not in ranges :
        #if enb not in ranges_any :
        #    continue
        #if (above_beta) / (ranges [enb] [1] - ranges [enb] [0] + 39) < gamma_val :
        #if (above_beta) / (len (ranges_any [enb]) + 39) < gamma_val :
        if (above_beta) / 150 < gamma_val :
            h_system += 1
        '''
        else : 
            if np .average (list (enb_loads [enb] .values ())) < beta and len ([t for t in enb_loads [enb] if enb_loads [enb] [t] > beta]) / (ranges [enb] [1] - ranges [enb] [0] + 39) >= .1:
                print (enb, "(", used_enb_index [enb], ")",
                    "-- HL", len ([t for t in enb_loads [enb] if enb_loads [enb] [t] > beta]), 
                    "LS", len (enb_loads [enb]), 
                    "Range", ranges [enb] [1] - ranges [enb] [0] + 39, 
                    "AVG-L", np .average (list (enb_loads [enb] .values ())), 
                    "Percentage", (above_beta) / (ranges [enb] [1] - ranges [enb] [0] + 39), above_beta) 
        '''
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

    ue_time, range_time, used_time = {e:0 for e in used_enb_index}, {e:None for e in used_enb_index}, {e:(float("inf"), 0) for e in used_enb_index}
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
            used_time [e] = (f_min, l_max)

    for e in ue_count :
        if ue_count [e] == 0:
            ue_count [e] = 1

    return {e : (ue_time [e] / ue_count [e]) for e in ue_time}, {e : (used_time [e] [1] - used_time [e] [0] + 1) for e in used_time}, {}

import os
import subprocess
import matplotlib .pyplot as plt
plt.rcParams.update({'font.size': 16})
#fig = plt .figure (1)

index = [str (i) for i in range (20)]
#c_vals = {}
bt = str (beta)
ues_str = str (n_ue)
times = [t for t in range (150)]

f_avg_used_time = {e:{} for e in expt}
f_avg_ue_time = {e:{} for e in expt}
f_avg_range_time = {e:{} for e in expt}
f_avg_ho = {e:0 for e in expt}
f_percentage = {e:{t:0 for t in times} for e in expt}
f_avg_load = {e:{} for e in expt}
f_avg_lsrl = {e:0 for e in expt}
f_avg_enbs = {e:0 for e in expt}
f_avg_hsys = {e:0 for e in expt}
f_avg_high = {e:{} for e in expt}
f_avg_used = {e:{} for e in expt}

all_enbs_used = set ([])

used_ind = {}
with open ("indexed_used_enbs_LB", "rb") as f:
    used_ind = pickle .load (f)

for exp in expt :
    count = 0
    for i in index :
        if exp in ["1a", "2a"] :
            fname = "amst_" + ues_str + "_" + bt + "_" + exp + "_" + i + "_none_jula_a10.0_b" + bt + "_g" + str (gamma) + "_p1_u" + ues_str + ".connection"
            fname_debug = "amst_" + ues_str + "_" + bt + "_" + exp + "_" + i + "_none_jula_a10.0_b" + bt + "_g" + str (gamma) + "_p1_u" + ues_str + ".debug"
            dname = "/home/external/Python-Data-Processing/amst-t1-randSel/" + "amst_" + ues_str +"_" + bt + "_" + exp + "_" + i + "_none_jula_a10.0_b" + bt + "_g" + str (gamma) + "_p1_u" + ues_str +"/" + "V4/"
        elif exp in ["uara", "dlba"]:
            fname = "amst_" + ues_str + "_" + exp + "_" + bt + "_" + i + "_a3_" + exp + "_a0_b" + bt + "_g0_p1_u" + ues_str + ".connection"
            fname_debug = "amst_" + ues_str + "_" + exp + "_" + bt + "_" + i + "_a3_" + exp + "_a0_b" + bt + "_g0_p1_u" + ues_str + ".debug"
            dname = "/home/external/Python-Data-Processing/amst-t1-randSel/" + "amst_" + ues_str + "_" + exp + "_" + bt + "_" + i + "_a3_" + exp + "_a0_b" + bt + "_g0_p1_u" + ues_str + "/" + "V4/"
        elif exp in ["ussl-a"]:
            fname = "amst_" + ues_str + "_" + exp + "_" + bt + "_" + i + "_" + exp + "_none_a0.0_b" + bt + "_g0_p1_u" + ues_str + ".connection"
            fname_debug = "amst_" + ues_str + "_" + exp + "_" + bt + "_" + i + "_" + exp + "_none_a0.0_b" + bt + "_g0_p1_u" + ues_str + ".debug"
            dname = "/home/external/Python-Data-Processing/amst-t1-randSel/" + "amst_" + ues_str + "_" + exp + "_" + bt + "_" + i + "_" + exp + "_none_a0.0_b" + bt + "_g0_p1_u" + ues_str + "/" + "V4/"

        if os .path .exists (dname + fname) :
            print (True, dname + fname)
            count += 1
        else :
            print (False, dname + fname)
            continue

        f = open (dname + fname,  "rb")
        c = pickle .load (f)
        f .close ()

        #f = open (dname + fname_debug)
        f = subprocess. Popen (['tail', '-F', dname + fname_debug, '-n', '13'], stdout = subprocess .PIPE)
        #f = subprocess .Popen (['head', '-F', f .stdout, '-n', '1'], stdout = subprocess .PIPE)
        lsrl = float (f .stdout .readline () .split () [-1] .strip ())
        f_avg_lsrl [exp] += lsrl

        p_u, h_system = foo (c)
        avg_ho, fairness_per_time, high_load_per_time, total_enbs_per_time, all_distinct_enbs, enb_load_per_time = bar (p_u)

        '''
        e_ins = [11, 14, 17, 19, 20]
        ins_time = [t for t in range (64, 76)]
        conn = {e:{t:[] for t in ins_time} for e in e_ins}
        for ue in p_u:
            for t in ins_time:
                e = used_enb_index [p_u [ue] [t]]
                if e in e_ins:
                    conn [e] [t] .append (ue)
        for e in conn :
            print (e)
            for t in ins_time : #sorted (conn [e]) :
                if t in conn [e]:
                    print (conn [e] [t])
            input ()
        quit ()
        '''
        '''
        print ("Experiment", expt, "count", i)
        fig = plt .figure (figsize = (21,14))
        for enb in enb_load_per_time :
            ls = [enb_load_per_time [enb] [t] for t in sorted (enb_load_per_time [enb])]
            hl = [v for v in ls if v > beta]
            inspect = [11, 14, 17, 19, 20]
            #inspect = [27, 29]
            if used_enb_index [enb] in inspect:
                ls_ins = enb_load_per_time [enb]
                for t in range (min (ls_ins), max (ls_ins)) :
                    if t not in ls_ins :
                        ls_ins [t] = 0
                plt .plot (sorted (ls_ins .keys ()), [ls_ins [k] for k in sorted (ls_ins)], label = str (used_enb_index [enb]))
                #print ("eNB", enb, "index", used_enb_index [enb], "Max load", max (enb_load_per_time [enb] .values ()), "Avg load", np .average (list (enb_load_per_time [enb] .values ())))
                #print (ls, len (ls))
                #print ("HL", hl, "size", len (hl), "percentage", len (hl)/len (ls))
        print ("H_system", h_system)
        plt .legend (ncol = 2)
        plt .xlabel ("Time")
        plt .ylabel ("Load")
        #plt .show ()
        fig .savefig ("_" .join ([str (v) for v in inspect] + ["g" + str (gamma), "b" + str (beta)]) + ".pdf", dpi = 300)
        quit ()
        '''

        f_avg_ho [exp] += avg_ho
        for t in sorted (total_enbs_per_time .keys ()) :
            f_percentage [exp] [t] += 100 * high_load_per_time [t] / total_enbs_per_time [t]

        for e in enb_load_per_time :
            if e not in f_avg_high [exp] :
                f_avg_high [exp] [e] = 0
            for t in enb_load_per_time [e] :
                if enb_load_per_time [e] [t] > beta :
                    f_avg_high [exp] [e] += 1
            if e not in f_avg_load [exp] :
                all_enbs_used .add (e)
                f_avg_load [exp] [e] = 0
            #f_avg_load [exp] [e] += sum ([enb_load_per_time [e] [t] for t in enb_load_per_time [e]]) / len (enb_load_per_time [e])
            f_avg_load [exp] [e] += len (enb_load_per_time [e])

        for t in total_enbs_per_time :
            if t not in f_avg_used [exp]:
                f_avg_used [exp] [t] = 0
            f_avg_used [exp] [t] += total_enbs_per_time [t]

        f_avg_hsys [exp] += h_system
        f_avg_enbs [exp] += len (f_avg_load [exp])

        avg_ue_time, avg_used_time, avg_range_time = ue_times (c)

        for e in avg_ue_time :
            if e not in f_avg_ue_time [exp] :
                f_avg_ue_time [exp] [e] = 0
            f_avg_ue_time [exp] [e] += avg_ue_time [e]

        for e in avg_used_time :
            if e not in f_avg_used_time [exp] :
                f_avg_used_time [exp] [e] = 0
            f_avg_used_time [exp] [e] += avg_used_time [e]

        for e in avg_range_time :
            if e not in f_avg_range_time [exp] :
                f_avg_range_time [exp] [e] = 0
            f_avg_range_time [exp] [e] += avg_range_time [e]

    print (exp, names [exp], count)
    f_avg_lsrl [exp] /= count
    f_avg_ho [exp] /= count
    f_avg_hsys [exp] /= count
    f_avg_enbs [exp] /= count

    print ("Avg-HO", f_avg_ho [exp], "Avg-LSRL", f_avg_lsrl [exp], "h_system", f_avg_hsys [exp], "distinct_enbs", f_avg_enbs [exp])

    for t in times :
        f_percentage [exp] [t] /= count

    for e in f_avg_load [exp] :
        f_avg_load [exp] [e] /= count

    for t in f_avg_used [exp] :
        f_avg_used [exp] [t] /= count
    for e in f_avg_ue_time [exp] :
        f_avg_ue_time [exp] [e] /= count

    for e in f_avg_used_time [exp] :
        f_avg_used_time [exp] [e] /= count

    for e in f_avg_high [exp] :
        f_avg_high [exp] [e] /= count

    #plt .bar ([used_enb_index [e] + shift [exp] for e in sorted (f_avg_ue_time [exp] .keys ())], [f_avg_ue_time [exp] [e] for e in sorted (f_avg_ue_time [exp] .keys ())], label = names [exp], width=wid)
    #plt .bar ([used_enb_index [e] + shift [exp] for e in sorted (f_avg_used_time [exp] .keys ())], [f_avg_used_time [exp] [e] for e in sorted (f_avg_used_time [exp] .keys ())], label = names [exp], width=wid)

#plt .bar ([used_enb_index [e] for e in ranges .keys ()], [ranges [e] [1] - ranges [e] [0] + 39 for e in ranges])

#fig .legend (ncol = 4)
#plt .xlabel ("Enb ids")
#plt .ylabel ("Avg time eNB RSRP >= -85 dBm")
#plt .ylim ([0,60])


fig = plt .figure (figsize = (21,14))

#Curve 1: x-axis = time, y-axis=no. of eNBs used (at least one UE connected in some timestep)
ax1 = plt .subplot (321)
ax1 .set_xlabel ("Time")
ax1 .set_ylabel ("Avg. No. \nof eNB used")
ax1 .bar ([t for t in sorted (f_avg_used [exp] .keys ())], [f_avg_used [exp] [t] for t in sorted (f_avg_used [exp] .keys ())], label = names [exp], width=.8)
ax1 .set_ylim ([0, 25])

#Curv2 2: x-axis=time, y-axis=% of highly loaded eNBs
ax2 = plt .subplot (322)
ax2 .set_xlabel ("Time")
ax2 .set_ylabel ("Avg. % of \nhighly loaded eNBs")
ax2 .plot (times, [f_percentage [exp] [t] for t in times], label = names [exp])
ax2 .set_ylim ([0, 105])

'''
#Curve 3: x-axis=eNB id, y-axis = Avg load per eNB
ax3 = plt .subplot (323)
ax3 .set_xlabel ("eNB ID")
ax3 .set_ylabel ("Avg. Load \nper eNB")
ax3 .bar ([used_enb_index [e] for e in sorted (f_avg_load [exp] .keys ())], [f_avg_load [exp] [e] for e in sorted (f_avg_load [exp] .keys ())], label = names [exp], width=.8)
ax3 .set_ylim ([0, 65])

#Curve 4: x-axis=eNB id, y-axis = Avg time of signal (time duration from first UE getting > lambda till last UE with > lambda)
ax4 = plt .subplot (324)
ax4 .set_xlabel ("eNB ID")
ax4 .set_ylabel ("Avg. time \nof signal")
ax4 .bar ([used_enb_index [e] for e in ranges .keys ()], [ranges [e] [1] - ranges [e] [0] + 39 for e in ranges])
ax4 .set_ylim ([0, 65])

#Curve 5: x-axis=eNB id, y-axis = Avg time actually used (at least one eNB connected)
ax5 = plt .subplot (325)
ax5 .set_xlabel ("eNB ID")
ax5 .set_ylabel ("Avg. time \nactually used")
plt .bar ([used_enb_index [e] for e in sorted (f_avg_used_time [exp] .keys ())], [f_avg_used_time [exp] [e] for e in sorted (f_avg_used_time [exp] .keys ())], label = names [exp], width=.8)
ax5 .set_ylim ([0, 65])

#Curve 6: x-axis=eNB id, y-axis = Avg time the eNB was highly loaded
ax6 = plt .subplot (326)
ax6 .set_xlabel ("eNB ID")
ax6 .set_ylabel ("Avg. time \nhighly loaded")
plt .bar ([used_enb_index [e] for e in sorted (f_avg_high [exp] .keys ())], [f_avg_high [exp] [e] for e in sorted (f_avg_high [exp] .keys ())], label = names [exp], width=.8)
ax6 .set_ylim ([0, 65])
'''

plt.tight_layout()

if len (sys .argv) == 2 :
    fig .savefig ("/home/external/Python-Data-Processing/u" + str(len (ues)) + "_b" + bt + "_g" + str (gamma) + "_" + sys .argv [1] + ".pdf")
    fig .savefig ("/home/external/Python-Data-Processing/u" + str(len (ues)) + "_b" + bt + "_" + sys .argv [1] + ".eps")

else :
    print (len (sys .argv), sys .argv)
    #plt .show ()

