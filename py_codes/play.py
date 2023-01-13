import sys
import my_modules .process_stats_modules as ps_mod

if __name__ == '__main__':
    debug_file_prefix = sys .argv [1] .rstrip ('.debug')
    with ps_mod .ProcessStatsModule (debug_file_prefix) as ps_module:
        ec, uc = ps_module .parse_connection ([0, 150])
        for t in ec:
            print ("time", t)
            for e in ec [t]:
                print ("enb", e, "connections [", len (ec [t] [e]), ']:', ec [t] [e])

        print (uc)
