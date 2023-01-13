import sys
import pickle
import numpy as np

from my_tracing import *
trace .min_level = 1
log .DEBUG = True
from my_io import *
from load_balance_modules import *
import handover_load_calc as hlc


def evaluate(args):
    context = args [-1]

    with open (context + "/current_load_journal_pickle_dump", "rb") as f_cl, open (context + "/handover_journal_pickle_dump", "rb") as f_cc:
        current_load_j = pickle .load (f_cl)
        handover_j = pickle .load (f_cc)

    lambda_value = -85
    times = handover_j .keys()
    enb_pos, rsrp_meas = [hlc .read_from_file (case, context) for case in ['enb_pos', 'rsrp']]
    set_of_enbs = set (enb_pos .keys ())
    A_e_dict = hlc .calculate_aoi (set_of_enbs, rsrp_meas, lambda_val = lambda_value)
    A_e_overlap_dict = hlc .calculate_overlaps (A_e_dict)

    std_dict = {}
    for t in sorted (times):
        clj = current_load_j [t]
        for e in clj:
            if e in A_e_overlap_dict .keys():
                overlaps = set .union (*[A_e_overlap_dict [e] [t] for t in A_e_overlap_dict [e]])
                if e not in std_dict:
                    std_dict [e] = [round (np .std ([clj [e_i] for e_i in overlaps]), 3)]
                else :
                    std_dict [e] .append (round (np .std ([clj [e_i] for e_i in overlaps]), 3))
    
    for e in std_dict:
        print (e, len (A_e_overlap_dict [e]), round (np .std (std_dict [e]), 3), round (np .mean (std_dict [e]), 3))

    print ("Max max(std):", max ([max (std_dict [e]) for e in std_dict]))
    print ("Mean max(std):", np .mean ([max (std_dict [e]) for e in std_dict]))
    print ("Min max(std):", min ([max (std_dict [e]) for e in std_dict]))
    print ("Std max(std):", np .std ([max (std_dict [e]) for e in std_dict]))


if __name__ == "__main__":
    evaluate(sys.argv [1:])
