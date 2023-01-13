import sys

with open (sys.argv [1]) as f:
    enbs_eligible = set([])
    enbs_handover = set([])
    fl = f .readlines ()
    for l in fl:
        if l .find ("Measurement") != -1:
            ue = int (l .split () [5])
            tmp = l .strip() .split ("is") [1]
            if (tmp != ' []'):
                for s in tmp .strip ("[] ") .split ('), ('):
                    e, p = [int(i) for i in s .strip ("() ") .split(',')]
                    enbs_eligible .add (e)

        if l .find ("Handover from") != -1:
            tok = l .strip() .split ()
            enbs_handover .add (int (tok [4]))
            enbs_handover .add (int (tok [7]))
    
    print ("All Eligible eNBs", enbs_eligible, len (enbs_eligible))
    print ("All Handover eNBs", enbs_handover, len (enbs_handover))

    
