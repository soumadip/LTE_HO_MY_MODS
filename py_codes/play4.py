#!/usr/bin/python

import sys
import pickle
import numpy as np


n_ue = 250
beta = 10
gamma = 0.9

ues = [i for i in range (1, n_ue + 1, 1)]

def foo (c) :
    ueas_ind = {ue : {} for ue in ues}
    enb_loads = {}
    for t in c:
        for ue in c [t]:
            if c [t] [ue] == -1:
                continue
            else :
                s, d, _, _ = c [t] [ue]
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
        if len ([t for t in enb_loads [enb] if enb_loads [enb] [t] <= beta]) / len (enb_loads [enb]) >= gamma :
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
    return sum_ho / n_ue, fairness, high_load, total, all_enbs

import matplotlib .pyplot as plt
plt.rcParams.update({'font.size': 16})

expt = "4"
pre_vals = [expt + case + '_' + str (i) for i in range (10) for case in ["a", "b", "c"]]
c_vals = []
for pre in pre_vals :
    dname = "/home/external/Python-Data-Processing/paris-t1-randSel/" + pre + "_none_jula_a10.0_b10_g0.1_p1_u250/"
    
    fname = pre + "_none_jula_a10.0_b10_g0.1_p1_u250.connection"

    f = open (dname + fname,  "rb")
    c_vals .append (pickle .load (f))
    f .close ()


avg_high_load = {}
avg_total = {}
exp = set([])
count = {}
avg_h_sys = {}
avg_ho = {}
avg_all_enbs = {}
for c, name in zip (c_vals, pre_vals) : # col, l in zip(["red", "blue", "green"], ['-', '--', '-.']) :
    p_u, h_system = foo (c)
    ho, fairness, high_load, total, all_enbs = bar (p_u)
    if name [:2] in avg_all_enbs :
        avg_all_enbs [name [:2]] += len (all_enbs)
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

if len (sys .argv) == 2 :
    #fig .savefig (dname + str(len (ues)) + sys .argv [1] + ".eps")
    fig .savefig ("/home/external/Python-Data-Processing/" + str(len (ues)) + sys .argv [1] + ".png")

else :
    print (len (sys .argv), sys .argv)
    plt .show ()


