#!/usr/bin/python

import sys
import pickle
import numpy as np

n_ue = 250
beta = 10
gamma = 1

#f = open ("/home/external/Python-Data-Processing/paris-t1-randSel/none_jula_a10.0_b" + str (beta) + "_p1_u" + str (n_ue) + "/none_jula_a10.0_b" + str (beta) + "_p1_u" + str (n_ue) + ".connection", "rb")
d_m0 = "/home/external/Python-Data-Processing/paris-t1-randSel/none_jula_a10.0_b" + str (beta) + "_g" + str (gamma) + "_p1_u" + str (n_ue) + "/"
f_m0 = "none_jula_a10.0_b" + str (beta) + "_g" + str (gamma) + "_p1_u" + str (n_ue) + ".connection"
d_m1 = "/home/external/Python-Data-Processing/paris-t1-randSel/a3_uara_a0_b" + str (beta) + "_g0" + "_p1_u" + str (n_ue) + "/"
f_m1 = "a3_uara_a0_b" + str (beta) + "_g0" + "_p1_u" + str (n_ue) + ".connection"
d_m2 = "/home/external/Python-Data-Processing/paris-t1-randSel/a3_dlba_a0_b" + str (beta) + "_g0" + "_p1_u" + str (n_ue) + "/"
f_m2 = "a3_dlba_a0_b" + str (beta) + "_g0" + "_p1_u" + str (n_ue) + ".connection"
#dname = "/home/external/Python-Data-Processing/paris-t1-randSel/a3_uara_a0_b4_g0_p1_u100/"
#fname = "a3_uara_a0_b4_g0_p1_u100.connection"
f_m0 = open (d_m0 + f_m0,  "rb")
f_m1 = open (d_m1 + f_m1,  "rb")
f_m2 = open (d_m2 + f_m2,  "rb")

c_m0 = pickle .load (f_m0)
c_m1 = pickle .load (f_m1)
c_m2 = pickle .load (f_m2)

f_m0 .close ()
f_m1 .close ()
f_m2 .close ()

ues = [i for i in range (1, n_ue + 1, 1)]

def foo (c) :
    ueas_ind = {ue : {} for ue in ues}
    for t in c:
        for ue in c [t]:
            if c [t] [ue] == -1:
                continue
            else :
                s, d, _, _ = c [t] [ue]
                if d == -1 :
                    continue
                else :
                    ueas_ind [ue] [t] = d

    p_u = {ue:{} for ue in ues}
    for ue in ueas_ind :
        ind = sorted (ueas_ind [ue] .keys()) 
        for t1, t2 in zip (ind, ind [1:]) :
            for t in range (t1, t2, 1) :
                p_u [ue] [t] = ueas_ind [ue] [t1]
        #p_u [ue] [t2] = ueas_ind [ue] [t2]

    return p_u

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
                print (wind)
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
        print ("UE", ue, "UEAS", ueas)
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
                su += l
                sl += l * l
        if sl != 0:
            fairness [t] = round ((su * su) / (sl * total [t]), 3)

    print (fairness)
    print (high_load)
    print (total)

    print ("Avg. HO", sum_ho / n_ue)
    print ("Avg. PP", sum_pp / n_ue)
    print ("Avg. WR", sum_wr / n_ue)
    return fairness, high_load, total

import matplotlib .pyplot as plt
plt.rcParams.update({'font.size': 16})

for c, name, col, l in zip ([c_m0, c_m1, c_m2], ["M0", "M1", "M2"], ["red", "blue", "green"], ['-', '--', '-.']) :
    p_u = foo (c)
    fairness, high_load, total = bar (p_u)

    fig1 = plt .figure (0)
    plt .plot (fairness .keys(), fairness .values (), ls = l, label = name, color=col)

    fig2 = plt .figure (1)
    plt .plot (fairness .keys(), [high_load [t] /total [t] * 100 for t in fairness .keys ()], ls = l, label = name, color=col)

    fig3 = plt .figure (2)
    plt .plot (high_load .keys(), high_load .values (), ls= "--", label = "$\\rho_{e_i}^t>\\beta$" + ", " + name, color = col)
    plt .plot (total .keys(), total .values (), ls= "-", label = "$\\rho_{e_i}^t>0$" + ", " + name, color=col)

    fig4 = plt .figure (3)
    X = [v for v in high_load .keys()]
    Y = [v for v in high_load .values ()]
    nX = []
    nY = []
    tmp = []
    for y in Y :
        tmp .append ((y, Y .count (y) / len (X)))
    for x, y in sorted (tmp, key = lambda x : x[0]) :
        nX .append (x)
        nY .append (y)
    plt .plot (nX, nY, ls= "--", label = "$\\rho_{e_i}^t>\\beta$" + ", " + name, color = col)
    #plt .plot (total .keys(), total .values (), ls= "-", label = "$\\rho_{e_i}^t>0$" + ", " + name, color=col)
    

    fig1 = plt .figure (0)
    plt. xlabel ("Time (seconds)")
    plt. ylabel ("Fairness")
    fig2 = plt .figure (1)
    plt. xlabel ("Time (seconds)")
    plt. ylabel ("Percentage")
    fig3 = plt .figure (2)
    plt. xlabel ("Time (seconds)")
    plt. ylabel ("Number of eNBs")
    plt .ylim ((0,30))

    fig1 .legend (ncol = 3)
    fig2 .legend (ncol = 3)
    fig3 .legend (ncol = 3)

if len (sys .argv) == 2 :
    fig1 .savefig (str(len (ues)) + sys .argv [1] + "a.eps")
    fig2 .savefig (str(len (ues)) + sys .argv [1] + "b.eps")
    fig3 .savefig (str(len (ues)) + sys .argv [1] + "c.eps")
    print ("saved as", str(len (ues)) + sys .argv [1] + "a/b/c.eps")
else :
    print (len (sys .argv), sys .argv)
    plt .show ()


