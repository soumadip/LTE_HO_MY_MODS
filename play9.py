import sys
import pickle

n_ue = 250
beta = 20
gamma = 0.1
ues = [i for i in range (1, n_ue + 1, 1)]

with open ("indexed_used_enbs_LB", "rb") as f:
    used_enb_index = pickle .load (f)
    
with open ("enb_ranges_positions", "rb") as f:
    ranges = pickle .load (f)

def calculate_PU (c) : #c == connections_dict
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

    return p_u

def calculate_eNB_LS (p_u) :
    ls = {}
    for ue in p_u :
        #ueas = [p_u [ue] [t] for t in sorted (p_u [ue] .keys ())]
        for t in p_u [ue] :
            if p_u [ue] [t] not in ls:
                ls [p_u [ue] [t]] = {}
                ls [p_u [ue] [t]] [t] = 1
            else :
                if t in ls [p_u [ue] [t]] :
                    ls [p_u [ue] [t]] [t] += 1
                else :
                    ls [p_u [ue] [t]] [t] = 1
    return ls


def compute_L_System (ls) :
    l_system = 0
    for enb in ls :
        above_beta = len ([t for t in ls [enb] if ls [enb] [t] > beta])
        #total_used = len (ls [enb])
        #if (150 - total_used + below_beta) / 150 >=gamma:# len (ls [enb]) >= gamma :
        if enb not in ranges :
            continue
        if (above_beta) / (ranges [enb] [1] - ranges [enb] [0] + 39) < gamma:
            l_system += 1
    return l_system


if __name__ == '__main__' :
    with open (sys .argv [1], "rb") as f :
        connections = pickle .load (f)

    p_u = calculate_PU (connections)
    for ue in p_u :
        print (ue, p_u [ue])
        print (len (p_u [ue]))

    ls = calculate_eNB_LS (p_u)
    nl = []
    for enb in ls :
        if enb in used_enb_index :
            print (enb, used_enb_index [enb])
        else :
            nl .append (enb)
        print (ls [enb], len (ls [enb]))
    print ("Not indexed count", len (nl), "List", nl)

    print ("L_system", compute_L_System (ls), "Total eNBs Used", len (ls))
