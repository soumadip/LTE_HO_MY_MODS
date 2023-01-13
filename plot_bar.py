import sys

def plot1():
    d_before = {}
    d_after = {}
    d_adjustments = {}
    times= []
    with open (sys .argv [2]) as f:
        fl = f .readlines()
        for l in fl:
            if l [:10] == "LOG: STAT:":
                tokens = l .split ()
                if tokens [2] == "Time":
                    t = int (tokens [3])
                    times .append (t)
                    if tokens [4] == "[Before]":
                        before = True
                        high_load_before = int (tokens [-4])
                        low_load_before = int (tokens [-1])
                        d_before [t] = (high_load_before, low_load_before)
                    elif tokens [4] == "[After]":
                        before = False
                        high_load_after = int (tokens [-4])
                        low_load_after = int (tokens [-1])
                        d_after [t] = (high_load_after, low_load_after)
                elif tokens [2] == "Total":
                    adjustments = int (tokens [-1])
                    d_adjustments [t] = adjustments
                elif tokens [2] == "No":
                    adjustments = 0
                    d_after [t] = (high_load_before, low_load_before)
                    d_adjustments [t] = adjustments

    x_pos = []
    y_pos_high_before = []
    y_pos_high_after = []
    y_pos_high_na = []
    for t in times:
        #print (t, d [t])
        x_pos .append (t)
        if d_adjustments [t] == 0:
            y_pos_high_before .append (d_before [t] [0])
            y_pos_high_after .append (0)
            y_pos_high_na .append (d_after [t] [0])
        else :
            y_pos_high_before .append (d_before [t] [0])
            y_pos_high_after .append (d_after [t] [0])
            y_pos_high_na .append (0)


    import matplotlib .pyplot as plt
    import numpy as np
    bar_width = 1.5
    plt .bar (np .array (x_pos), y_pos_high_before, bar_width, color = 'b', label = 'Before Load Balancing')
    plt .bar (np .array (x_pos) + bar_width, y_pos_high_after, bar_width, color = 'y', label = 'After Load Balancing')
    plt .bar (np .array (x_pos) + bar_width, y_pos_high_na, bar_width, color = 'grey', label = 'LBA Unused')
    plt .ylabel ("Number of eNBs (above beta)")
    plt .xlabel ("Time")
    plt .xticks (np .array (x_pos) +bar_width / 2, (str (i) for i in x_pos))
    plt .title ('/' .join (sys .argv [2] .split ('_') [1:]))
    plt .ylim ([0, 15])
    tok = sys .argv [2] .split ('_')
    percentage = float (tok [-4])
    alpha_val = float (tok [-2]) * percentage 
    p_val = '$\\alpha=$' + str (100* percentage) + '%'
    if tok [-4] != 'none':
        plt .plot (x_pos, [alpha_val for x in x_pos], color = 'r', ls = '-.')
        if percentage == 0.8 or percentage == 0.1 :
            plt .text (130, alpha_val - 1.2, p_val, {'color': 'r', 'fontsize': 18})
        else :
            plt .text (130, alpha_val + .2, p_val, {'color': 'r', 'fontsize': 18})
    plt .legend ()
    plt .tight_layout ()
    plt .gcf () .set_size_inches (14, 3)
    plt .savefig (sys.argv[2] .replace ('.', '-') + '.png', dpi = 400)
    print ("saved as ", sys.argv[2] .replace ('.', '-') + '.png')
    #plt .show ()


def plot2 ():
    d_before = {}
    d_after = {}
    d_adjustments = {}
    times= []
    with open (sys .argv [2]) as f:
        fl = f .readlines()
        for l in fl:
            if l [:10] == "LOG: STAT:":
                tokens = l .split ()
                if tokens [2] == "Time":
                    t = int (tokens [3])
                    times .append (t)
                    if tokens [4] == "[Before]":
                        before = True
                        high_load_before = int (tokens [-4])
                        low_load_before = int (tokens [-1])
                        d_before [t] = (high_load_before, low_load_before)
                    elif tokens [4] == "[After]":
                        before = False
                        high_load_after = int (tokens [-4])
                        low_load_after = int (tokens [-1])
                        d_after [t] = (high_load_after, low_load_after)
                elif tokens [2] == "Total":
                    adjustments = int (tokens [-1])
                    d_adjustments [t] = adjustments
                elif tokens [2] == "No":
                    adjustments = 0
                    d_after [t] = (high_load_before, low_load_before)
                    d_adjustments [t] = adjustments

    x_pos = []
    y_pos_high_before = []
    y_pos_high_after = []
    y_pos_high_na = []
    for t in times:
        #print (t, d [t])
        x_pos .append (t)
        if d_adjustments [t] == 0:
            y_pos_high_before .append (d_before [t] [0])
            y_pos_high_after .append (0)
            y_pos_high_na .append (d_after [t] [0])
        else :
            y_pos_high_before .append (d_before [t] [0])
            y_pos_high_after .append (d_after [t] [0])
            y_pos_high_na .append (0)


    import matplotlib .pyplot as plt
    import numpy as np
    bar_width = 1.5
    max_enb = int (sys .argv [3])
    y_pos = [100 * v / max_enb for v in y_pos_high_before]
    print (x_pos [7:22], y_pos [7:22], max (y_pos [7:22]), min (y_pos [7:22]), sum (y_pos [7:22]) / len (y_pos [7:22]))

    plt .bar (np .array (x_pos) +bar_width / 2, y_pos, bar_width, color = 'b', label = 'Before Load Balancing')
    #plt .bar (np .array (x_pos) + bar_width, y_pos_high_after, bar_width, color = 'y', label = 'After Load Balancing')
    #plt .bar (np .array (x_pos) + bar_width, y_pos_high_na, bar_width, color = 'grey', label = 'LBA Unused')
    plt .ylabel ("Percentage of eNBs (above beta)")
    plt .xlabel ("Time")
    plt .xticks (np .array (x_pos) +bar_width / 2, (str (i) for i in x_pos))
    plt .title ('/' .join (sys .argv [2] .split ('_') [1:]))
    plt .ylim ([0, 100])
    '''
    tok = sys .argv [2] .split ('_')
    percentage = float ( tok[-3])
    alpha_val = 93 * percentage 
    p_val = '$\\alpha=$' + str (100* percentage) + '%'
    if tok [-4] != 'none':
        plt .plot (x_pos, [alpha_val for x in x_pos], color = 'r', ls = '-.')
        if percentage == 0.8 or percentage == 0.1 :
            plt .text (130, alpha_val - 1.2, p_val, {'color': 'r', 'fontsize': 18})
        else :
            plt .text (130, alpha_val + .2, p_val, {'color': 'r', 'fontsize': 18})
    '''
    plt .legend ()
    plt .tight_layout ()
    plt .gcf () .set_size_inches (14, 3)
    plt .savefig (sys.argv[2] .replace ('.', '-') + '-alpha.png', dpi = 400)
    print ("saved as ", sys.argv[2] .replace ('.', '-') + '-alpha.png')
    #plt .show ()

def plot3():
    d_before = {}
    d_after = {}
    d_adjustments = {}
    times= []
    with open (sys .argv [2]) as f:
        fl = f .readlines()
        for l in fl:
            if l [:10] == "LOG: STAT:":
                tokens = l .split ()
                if tokens [2] == "Time":
                    t = int (tokens [3])
                    times .append (t)
                    if tokens [4] == "[Before]":
                        before = True
                        high_load_before = int (tokens [-4])
                        low_load_before = int (tokens [-1])
                        d_before [t] = (high_load_before, low_load_before)
                    elif tokens [4] == "[After]":
                        before = False
                        high_load_after = int (tokens [-4])
                        low_load_after = int (tokens [-1])
                        d_after [t] = (high_load_after, low_load_after)
                elif tokens [2] == "Total":
                    adjustments = int (tokens [-1])
                    d_adjustments [t] = adjustments
                elif tokens [2] == "No":
                    adjustments = 0
                    d_after [t] = (high_load_before, low_load_before)
                    d_adjustments [t] = adjustments

    x_pos = []
    y_pos_high_before = []
    y_pos_high_after = []
    y_pos_high_na = []
    for t in times:
        #print (t, d [t])
        x_pos .append (t)
        if d_adjustments [t] == 0:
            y_pos_high_before .append (d_before [t] [0])
            y_pos_high_after .append (0)
            y_pos_high_na .append (d_after [t] [0])
        else :
            y_pos_high_before .append (d_before [t] [0])
            y_pos_high_after .append (d_after [t] [0])
            y_pos_high_na .append (0)


    import matplotlib .pyplot as plt
    import numpy as np
    bar_width = 1
    plt .bar (np .array (x_pos) - bar_width * 3 / 2, y_pos_high_before, bar_width, color = 'b', label = 'Before Load Balancing')
    plt .bar (np .array (x_pos) - bar_width / 2, y_pos_high_after, bar_width, color = 'y', label = 'After Load Balancing')
    plt .bar (np .array (x_pos) - bar_width / 2, y_pos_high_na, bar_width, color = 'grey', label = 'LBA Unused')


    d_before = {}
    d_after = {}
    d_adjustments = {}
    times= []
    with open (sys .argv [3]) as f:
        fl = f .readlines()
        for l in fl:
            if l [:10] == "LOG: STAT:":
                tokens = l .split ()
                if tokens [2] == "Time":
                    t = int (tokens [3])
                    times .append (t)
                    if tokens [4] == "[Before]":
                        before = True
                        high_load_before = int (tokens [-4])
                        low_load_before = int (tokens [-1])
                        d_before [t] = (high_load_before, low_load_before)
                    elif tokens [4] == "[After]":
                        before = False
                        high_load_after = int (tokens [-4])
                        low_load_after = int (tokens [-1])
                        d_after [t] = (high_load_after, low_load_after)
                elif tokens [2] == "Total":
                    adjustments = int (tokens [-1])
                    d_adjustments [t] = adjustments
                elif tokens [2] == "No":
                    adjustments = 0
                    d_after [t] = (high_load_before, low_load_before)
                    d_adjustments [t] = adjustments

    x_pos = []
    y_pos_high_before = []
    y_pos_high_after = []
    y_pos_high_na = []
    for t in times:
        #print (t, d [t])
        x_pos .append (t)
        if d_adjustments [t] == 0:
            y_pos_high_before .append (d_before [t] [0])
            y_pos_high_after .append (0)
            y_pos_high_na .append (d_after [t] [0])
        else :
            y_pos_high_before .append (d_before [t] [0])
            y_pos_high_after .append (d_after [t] [0])
            y_pos_high_na .append (0)

    plt .bar (np .array (x_pos) + bar_width / 2, y_pos_high_before, bar_width, color = 'black', label = 'No LBA Case')


    plt .ylabel ("Number of eNBs (above beta)")
    plt .xlabel ("Time")
    plt .xticks (np .array (x_pos) +bar_width / 2, (str (i) for i in x_pos))
    plt .title ('/' .join (sys .argv [2] .split ('_') [1:]))
    plt .ylim ([0, 25])
    tok = sys .argv [2] .split ('_')
    percentage = float (tok [-4])
    alpha_val = float (tok [-2]) * percentage 
    p_val = '$\\alpha=$' + str (100* percentage) + '%'
    if tok [-4] != 'none':
        plt .plot (x_pos, [alpha_val for x in x_pos], color = 'r', ls = '-.')
        if percentage == 0.8 or percentage == 0.1 :
            plt .text (130, alpha_val - 1.2, p_val, {'color': 'r', 'fontsize': 18})
        else :
            plt .text (130, alpha_val + .2, p_val, {'color': 'r', 'fontsize': 18})
    plt .legend ()
    plt .tight_layout ()
    plt .gcf () .set_size_inches (14, 3)
    #plt .savefig (sys.argv[2] .replace ('.', '-') + '.png', dpi = 400)
    print ("saved as ", sys.argv[2] .replace ('.', '-') + '.png')
    plt .show ()

if __name__ == '__main__':
    if sys .argv [1] == "1":
        plot1 ()
    elif sys .argv [1] == "2":
        plot2 ()
    elif sys .argv [1] == "3":
        plot3 ()
