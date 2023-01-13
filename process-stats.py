import sys
import my_modules .process_stats_modules as ps_mod

if __name__ == '__main__' :
    '''
    fname = sys .argv [1] .strip ('.debug')
    with ps_mod .ProcessStatsModule (fname) as psm :
        #psm .display ()
        import matplotlib .pyplot as plt
        x_vals, y_vals = psm. get_high_load_percentages (beta = 20)
        plt .plot (x_vals, y_vals)
        plt .show ()
    '''

    with open (sys .argv [1]) as f:
        fl = f .readlines()
        import matplotlib .pyplot as plt
        plt .gcf () .set_size_inches (14, 4) 
        font = {'size' : 16}
        plt .rc ('font', **font)
        index = 1
        legends = ()
        for line in fl:
            fname = line .strip ('.debug\n')
            with ps_mod .ProcessStatsModule (fname) as psm :
                x_vals, y_vals = psm. get_high_load_percentages (beta = 20)
                name = fname .split ('/') [1] .split ('_') [0] .upper ()
                plt .plot (x_vals, y_vals, label = name)
        plt .legend (ncol = 5, loc = 'lower center')
        plt .xlabel ("Time (Seconds)")
        #plt .xticks (rotation="vertical")
        plt .ylabel ("System Load Level")
        plt .tight_layout ()
        plt .show ()
        #plt .savefig ("load-dist3.eps", dpi = 400)
        """
    with open (sys .argv [1]) as f:
        fl = f .readlines()
        import matplotlib .pyplot as plt
        plt .gcf () .set_size_inches (14, 4) 
        font = {'size' : 16}
        plt .rc ('font', **font)
        index = 1
        legends = ()
        for line in fl:
            fname = line .strip ('.debug\n')
            with ps_mod .ProcessStatsModule (fname) as psm :
                #psm .display ()
                x_vals, y_vals = psm. get_high_load_percentages (beta = 20)
                name = fname .split ('/') [1] .split ('_') [0] .upper ()
                #plt .plot (x_vals, y_vals, label = name)
                ax = plt .subplot (1, 5, index)

                pie_vals = [100 * len ([v for v in y_vals if v > i and v <= j]) / len (x_vals) for i, j in zip (range (0, 91, 20), range (20, 101, 20))]
                legends = ax .pie (pie_vals, shadow = True)#, autopct = '%1.0f%%'
                ax .set_title (name)
                index += 1
        #plt .xlabel ("Time")
        #plt .ylabel ("System Load Imbalance")
        labels = [str (i) + '-' + str (j) + '%' for i, j in zip (range (0, 91, 20), range (20, 101, 20))]
        print (legends)
        plt .figlegend (legends [0], labels, ncol = 5, loc = "lower center")
        plt .tight_layout ()
        #plt .show ()
        plt .savefig ("load-dist-pie.eps", dpi = 400)
        
        """
