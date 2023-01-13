import sys
import my_modules .my_tracing as debugging
debugging .trace .min_level = 3
debugging .log .DEBUG = False
import my_modules .preprocess_shortest_paths as psp
import my_modules .my_io as io

if __name__ == "__main__":
    ue_positions_fname, enb_positions_fname = sys .argv [1:3]
    pp = psp .Preprocessing (ue_positions_fname, enb_positions_fname)
    ret = pp .run ()
    for p in ret .keys ():
        print ("Position", p, "Keys:", list (ret [p] .keys ()))
        for e in ret [p] .keys () :
            print ("enb", e, "next hop", ret [p] [e])

    if len (sys .argv) == 4:
        io .pickle_dump (ret, sys.argv [3]) 

