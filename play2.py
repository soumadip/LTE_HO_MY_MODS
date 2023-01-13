#!/usr/bin/python

import pickle

n_ue = 100
beta = 4
gamma = 0

#f = open ("/home/external/Python-Data-Processing/paris-t1-randSel/none_jula_a10.0_b" + str (beta) + "_p1_u" + str (n_ue) + "/none_jula_a10.0_b" + str (beta) + "_p1_u" + str (n_ue) + ".connection", "rb")
#dname = "/home/external/Python-Data-Processing/paris-t1-randSel/none_jula_a10.0_b" + str (beta) + "_g" + str (gamma) + "_p1_u" + str (n_ue) + "/"
#fname = "none_jula_a10.0_b" + str (beta) + "_g" + str (gamma) + "_p1_u" + str (n_ue) + ".connection"
dname = "/home/external/Python-Data-Processing/paris-t1-randSel/a3_uara_a0_b" + str (beta) + "_g" + str (gamma) + "_p1_u" + str (n_ue) + "/"
fname = "a3_uara_a0_b" + str (beta) + "_g" + str (gamma) + "_p1_u" + str (n_ue) + ".connection"
#dname = "/home/external/Python-Data-Processing/paris-t1-randSel/a3_uara_a0_b4_g0_p1_u100/"
#fname = "a3_uara_a0_b4_g0_p1_u100.connection"
f = open (dname + fname,  "rb")

c = pickle .load (f)
f .close ()

ues = [i for i in range (1, n_ue + 1, 1)]

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


import matplotlib .pyplot as plt
plt.rcParams.update({'font.size': 16})

fig1 = plt .figure (0)
plt .plot (fairness .keys(), fairness .values (), ls = "-", label = "fairness (Jain)", color="red")
plt .plot (fairness .keys(), [high_load [t] /total [t] for t in fairness .keys ()], ls = "--", label = "high_load_percentage", color="blue")
plt. xlabel("time")

fig1 .legend (ncol = 2)

fig2 = plt .figure (1)
plt. xlabel ("time")
plt. ylabel ("number of eNBs")
plt .plot (high_load .keys(), high_load .values (), ls= "-.", label = "high_load", color = "red")
plt .plot (total .keys(), total .values (), ls= "-", label = "in_use", color="blue")
plt .ylim ((0,30))

fig2 .legend (ncol = 2)

fig1 .savefig (dname + str(len (ues)) + "a.png")
fig2 .savefig (dname + str(len (ues)) + "b.png")
print ("saved as", dname + str(len (ues)) + "a.png")

# plt .show ()


