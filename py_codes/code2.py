# coding: utf-8
import sys
from collections import defaultdict

with open ("paris-t1-randSel/exp1.b10_s" + sys .argv [1] + "_none_jula-dual_a10.0_b10/V4/exp1.b10_s" + sys .argv [1] + "_none_jula-dual_a10.0_b10.debug", "r") as f:
    fl = f .readlines ()

ho_counter_ue = defaultdict (int)
ho_counter_src = defaultdict (lambda : defaultdict (int))
ho_counter_dst = defaultdict (lambda : defaultdict (int))
lsrl_ue = {}
ho_ue = {}
ueases = defaultdict (dict)
prev = 0 
for i, l in enumerate(fl):
    if l .find ('[LBA]') != -1 :
        d = l .split()
        t, ue, src, dst, sig = [int (v) for v in [d [2], d [4], d[7], d [9]]] + [float (d [11])]
        ho_counter_ue [ue] += 1
        ho_counter_src [src] [t] += 1
        ho_counter_dst [dst] [t] += 1
        ueases [ue] [t] = (src, dst, sig)
    elif l .find ('UE :') != -1 :
        d = l .split ()
        sig = [float (v) for v in fl [i - 1] .strip ('][\n') .split (', ')]
        count = 0
        for v in reversed (sig) :
            if int (v) == -115 :
                count += 1
            else :
                break
        ue, lsrl, ho = d [2], d [6], d [-1]
        ho_ue [int (ue)] = int (ho)
        lsrl_ue [int (ue)] = int (lsrl .strip ('])\n')) - count if lsrl != 'Handover' else 0

load_enb = defaultdict (lambda :defaultdict (int))
def make (ueas_dict):
    ret = {}
    keys = sorted (ueas_dict .keys ())
    for t1, t2 in zip (keys, keys [1:]) :
        for t in range (t1, t2 + 1) :
            ret [t] = ueas_dict [t1] [1]
    return ret
        
def select_ueas_range (s, e) :
    for ue in ueases :
        if ue < s or ue > e :
            continue
        ueas = make (ueases [ue])
        for t in ueas :
            if t > 540 and t < 790 :
                load_enb [ueas [t]] [t] += 1

select_ueas_range (155, 354)
        
import matplotlib .pyplot as plt

x, y1, y2, y3 = [], [], [], []
index = 1
for enb in sorted (load_enb .keys ()) :
    ls = load_enb [enb] .values ()
    x .append (index)
    index += 1
    y1 .append (max (ls))
    y2 .append (min (ls))
    y3 .append (round (sum (ls) / len (ls), 3))
    
plt .scatter (x, y1, label = "max")
plt .bar (x, y3, label="avg", color = "black")
#plt .plot (x, y2, label="min")
#plt .scatter (x, y1)
#plt .scatter (x, y3)
#plt .scatter (x, y2)
plt .legend ()
plt .ylim ([0,24])
plt .ylabel ("Avg eNB Load")
plt .xlabel ("eNB")
plt .tight_layout ()
plt .savefig ("figs/b10_s" + sys .argv [1] + ".png")

#L_system
beta = 10
alpha = .1
l_sys = 0
for e in load_enb :
    ls = load_enb [e]
    high = [ls [t] for t in sorted (ls .keys()) if ls [t] > beta]
    if len (high) / len (ls) < alpha :
        l_sys += 1
print ("L_system =", l_sys, "Total eNBs", len (load_enb))

def avg_lsrl (s, e):
    lsrl = 0
    count = 0
    for ue in lsrl_ue:
        if ue >= s and ue <= e :
            count += 1
            lsrl += lsrl_ue [ue]
    return round (lsrl/count, 3) if count != 0 else 0.0

def avg_ho_count (s, e):
    ho = 0
    count = 0
    for ue in ho_counter_ue:
        if ue >= s and ue <= e :
            count += 1
            ho += ho_counter_ue [ue]
    return round (ho/count, 3) if count != 0 else 0.0

print ("Average LSRL",
        "1-120>", avg_lsrl (1, 120), 
        "121-154>", avg_lsrl (121, 154),
        "1-154>", avg_lsrl (1, 154),
        "154-354>", avg_lsrl (154, 354),
        "1-354>", avg_lsrl (1, 354))

print ("Average HO",
        "1-120>", avg_ho_count (1, 120), 
        "121-154>", avg_ho_count (121, 154),
        "1-154>", avg_ho_count (1, 154),
        "154-354>", avg_ho_count (154, 354),
        "1-354>", avg_ho_count (1, 354))
