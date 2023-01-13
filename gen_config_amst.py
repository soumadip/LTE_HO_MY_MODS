import sys
import json
import os

if __name__ == "__main__" :
    with open (sys.argv [1]) as f:
        config = json .load (f)
        index = 0
        ret = ''

        algos = ["jula"]
        beta = int (sys .argv [2])

        for expt, case in [(x, y) for x in [int (sys .argv [3])] for y in [sys .argv [4]]] :
            for num_ue, beta in zip ([250], [beta]):
                for algo in algos:
                    part = int (sys .argv [5])
                    if part not in range (5) :
                        print ("part out of range")
                        exit ()
                    for no in range ((part-1) * 5, part * 5):
                    #for no in range (20):
                        config ['common_configs'] ['number_ue'] = num_ue
                        config ['common_configs'] ['lb_algo'] = algo #if alpha else "none"
                        config ['common_configs'] ['ho_algo'] = "none"
                        config ['ue_start_times_set_no'] = no
                        config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['beta'] = beta
                        config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['expt'] = expt
                        config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['type'] = case

                        prefix = '_' .join ([str (v) for v in ['amst', num_ue, beta, str(expt) + case, no]])
                        fname = 'tmp/' + prefix + '_tmp' + str (index) + '.json'
                        with open (fname, "w") as f:
                            json .dump (config, f)

                        ret += fname + ' ' + prefix + '\n'
                        index += 1
        print (ret[:-1])


