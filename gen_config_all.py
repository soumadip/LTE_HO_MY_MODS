import sys
import json
import os

if __name__ == "__main__" :
    with open (sys.argv [1]) as f:
        config = json .load (f)
        index = 0
        ret = ''

        #if len (sys .argv) == 3:
        #    algos = [sys.argv [-1]]
        #else :
            #algos = ['a3', 'a2a4', 'ubbho', 'ombfra', 'ussl-a']
        algos = ["jula"]

        for expt, case in [(x, y) for x in [int (sys .argv [2])] for y in ["a", "b", "c"]] :
            for num_ue, beta in zip ([250], [10]):
                for algo in algos:
                    for no in range (20) :
                        config ['common_configs'] ['number_ue'] = num_ue
                        config ['common_configs'] ['lb_algo'] = algo #if alpha else "none"
                        config ['common_configs'] ['ho_algo'] = "none"
                        config ['ue_start_times_set_no'] = no
                        config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['beta'] = beta
                        config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['expt'] = expt
                        config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['case'] = case

                        fname = 'tmp/_tmp' + str (index) + '.json'
                        prefix = '_' .join ([str (v) for v in [str(expt) + case, no]])
                        with open (fname, "w") as f:
                            json .dump (config, f)

                        ret += fname + ' ' + prefix + '\n'
                        index += 1
        print (ret)


