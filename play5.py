#!/usr/bin/python

import sys
import pickle
import numpy as np


n_ue = 250
beta = 15
gamma = 0.9

ues = [i for i in range (1, n_ue + 1, 1)]

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

    #print (fairness)
    #print (high_load)
    #print (total)

    #print ("Avg. HO", sum_ho / n_ue)
    #print ("Avg. PP", sum_pp / n_ue)
    #print ("Avg. WR", sum_wr / n_ue)
    return sum_ho / n_ue, fairness, high_load, total, all_enbs, ls

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
f_avg_ho = {e:0 for e in expt}
f_percentage = {e:{t:0 for t in times} for e in expt}
f_avg_load = {e:{} for e in expt}
f_avg_lsrl = {e:0 for e in expt}
f_avg_enbs = {e:0 for e in expt}
f_avg_hsys = {e:0 for e in expt}
f_avg_used = {e:{} for e in expt}

all_enbs_used = set ([])

used_ind = {}
with open ("indexed_used_enbs_LB", "rb") as f:
    used_ind = pickle .load (f)


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

        #f = open (dname + fname_debug)
        f = subprocess. Popen (['tail', '-F', dname + fname_debug, '-n', '13'], stdout = subprocess .PIPE)
        #f = subprocess .Popen (['head', '-F', f .stdout, '-n', '1'], stdout = subprocess .PIPE)
        lsrl = float (f .stdout .readline () .split () [-1] .strip ())
        f_avg_lsrl [exp] += lsrl

        p_u, h_system = foo (c)
        avg_ho, fairness_per_time, high_load_per_time, total_enbs_per_time, all_distinct_enbs, enb_load_per_time = bar (p_u)

        f_avg_ho [exp] += avg_ho
        for t in sorted (total_enbs_per_time .keys ()) :
            f_percentage [exp] [t] += 100 * high_load_per_time [t] / total_enbs_per_time [t]

        for e in enb_load_per_time :
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

    #plt .plot (times, [f_percentage [exp] [t] for t in times], label = names [exp])
    #plt .bar ([e + shift [exp] for e in sorted (f_avg_load [exp] .keys ())], [f_avg_load [exp] [e] for e in sorted (f_avg_load [exp] .keys ())], label = names [exp], width=.5)
    plt .bar ([used_ind [e] + shift [exp] for e in sorted (f_avg_load [exp] .keys ())], [f_avg_load [exp] [e] for e in sorted (f_avg_load [exp] .keys ())], label = names [exp], width=wid)
    #plt .bar ([t*4 + shift [exp] for t in sorted (f_avg_used [exp] .keys ())], [f_avg_used [exp] [t] for t in sorted (f_avg_used [exp] .keys ())], label = names [exp], width=.25)
    #plt .plot (sorted (f_avg_used [exp]), [f_avg_used [exp] [t] for t in sorted (f_avg_used [exp])], label = names [exp])

fig .legend (ncol = 4)
plt .xlabel ("Enb ids")
plt .ylabel ("Time with non-zero Load (sec)")
#plt .xlabel ("Time")
#plt .ylabel ("Percentage")
plt .ylim ([0,60])

#with open ("all_enbs", "w") as f:
#    print (list (all_enbs_used), file = f)

if len (sys .argv) == 2 :
    #fig .savefig (dname + str(len (ues)) + sys .argv [1] + ".eps")
    fig .savefig ("/home/external/Python-Data-Processing/" + str(len (ues)) + sys .argv [1] + ".pdf")
    fig .savefig ("/home/external/Python-Data-Processing/" + str(len (ues)) + sys .argv [1] + ".eps")

else :
    print (len (sys .argv), sys .argv)
    plt .show ()

'''
avg_high_load = {}
avg_total = {}
exp = set([])
count = {}
avg_h_sys = {}
avg_ho = {}
avg_all_enbs = {}
for c, i in zip (c_vals, index) : # col, l in zip(["red", "blue", "green"], ['-', '--', '-.']) :
    if name [:2] in avg_all_enbs :
        avg_all_enbs [i] += len (all_enbs)
    else :
        avg_all_enbs [name [:2]] = len (all_enbs)

    if name [:2] in avg_h_sys :
        avg_h_sys [name [:2]] += h_system
    else :
        avg_h_sys [name [:2]] = h_system

    if name [:2] in avg_ho :
        avg_ho [name [:2]] += ho
    else :
        avg_ho [name [:2]] = ho

    if name [:2] not in avg_total:
        avg_total [name [:2]] = {}
        count [name [:2]] = 1
    else :
        count [name [:2]] += 1
    for t in fairness .keys () :
        if t in avg_total [name [:2]]:
            avg_total [name [:2]] [t] += total [t]
        else : 
            avg_total [name [:2]] [t] = total [t]

    if name [:2] not in avg_high_load:
        avg_high_load [name [:2]] = {}
    for t in fairness .keys () :
        if t in avg_high_load [name [:2]]:
            avg_high_load [name [:2]] [t] += high_load [t] /total [t] * 100
        else : 
            avg_high_load [name [:2]] [t] = high_load [t] /total [t] * 100
    exp .add (name [:2])

for ex, col, l in zip (exp, ["red", "blue", "green"], ['-', '--', '-.']):
    fig = plt .figure (1)
    plt .plot (fairness .keys(), [avg_high_load [ex] [t] /count [ex] for t in fairness .keys ()], ls = '-', label = ex + '_high%', color=col)
    plt .plot (fairness .keys(), [avg_total [ex] [t] /count [ex]  for t in fairness .keys ()], ls = '--', label = ex + '_total', color=col)

    print ("Expt", ex, "Avg_H_system", avg_h_sys [ex]/ count [ex], "Avg ho", avg_ho [ex] / count [ex], "Avg all eNBs", avg_all_enbs [ex] /count [ex])

fig = plt .figure (1)
plt. xlabel ("Time (seconds)")
plt. ylabel ("")

fig .legend (ncol = 3)
'''


