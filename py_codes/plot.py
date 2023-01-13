import sys
import json
import my_modules .my_tracing as debugging
debugging .trace .min_level = 0
debugging .log .DEBUG = True
import my_modules .plot_modules as pl_mod

if __name__ == '__main__' :
    with pl_mod .PlotModule (sys .argv [1]) as pm :
        if len (sys .argv) == 2:
            pm .plot_bar (sys .argv [1])
            pm .save_as ()
            pm .show ()
            pm .show_stats (sys .argv [1])
        elif len (sys .argv) == 3:
            #pm .plot_bar_with_noLBAcase (sys .argv [1], sys .argv [2])
            pm .plot_curve_with_noLBAcase (sys .argv [1], sys .argv [2])
            pm .save_as ()
            #pm .show ()
            #pm .show_stats (sys .argv [1])
        elif len (sys .argv) == 4:
            #pm .plot_bar_with_noLBAcase (sys .argv [1], sys .argv [2])
            pm .plot_curve_with_noLBAcase2 (sys .argv [1], sys .argv [2], sys .argv [3])
            pm .save_as (sys .argv [1] .strip (".debug") + '-both.eps')
            pm .show ()
            #pm .show_stats (sys .argv [1])
        else :
            print ("Options:\n"
                    "python % <LBA-file-debug>\n"
                    "python % <LBA-file-debug> <No-LBA-file-debug>")
