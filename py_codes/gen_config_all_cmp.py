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
        #algos = ["dlba", "uara"]
        algo = sys .argv [2]

        for num_ue, beta in zip ([250], [20]):
        #for algo in algos:
            #print (sys .argv)
            #part = int (sys .argv [2]) # can attain values in [0,1,2,3]
            #if part not in range (8) :
            #    print ("invalid part no", sys .argv)
            #    exit (0)
            #start = int (part * 2.5)
            #end = int ((part + 1) * 2.5)
            #for no in range (start, end) :
            for no in range (20) :
                config ['common_configs'] ['number_ue'] = num_ue
                config ['common_configs'] ['lb_algo'] = algo if algo != "ussl-a" else "none"
                config ['common_configs'] ['ho_algo'] = algo if algo == "ussl-a" else "a3"
                config ['ue_start_times_set_no'] = no
                config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['beta'] = beta

                prefix = '_' .join ([str (v) for v in [num_ue, algo, beta, no]])
                fname = 'tmp/' + prefix + '_tmp' + str (index) + '.json'
                with open (fname, "w") as f:
                    json .dump (config, f)

                ret += fname + ' ' + prefix + '\n'
                index += 1
        print (ret[:-1])


