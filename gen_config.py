import sys
import json

if __name__ == "__main__" :
    with open (sys.argv [1]) as f:
        config = json .load (f)
        index = 0
        ret = ''

        for alpha in [0.0] :
            for num_ue, beta in zip ([250], [20]):
                config ['common_configs'] ['number_ue'] = num_ue
                config ['common_configs'] ['lb_algo'] = "maxflow" if alpha else "none"
                config ['common_configs'] ['ho_algo'] = "ussl-a"
                config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['alpha'] = alpha
                config [config ['common_configs'] ['lb_algo'] + config ['lb_conf']] ['beta'] = beta

                fname = 'tmp/_tmp' + str (index) + '.json'
                with open (fname, "w") as f:
                    json .dump (config, f)

                ret += fname + ' '
                index += 1
        print (ret)


