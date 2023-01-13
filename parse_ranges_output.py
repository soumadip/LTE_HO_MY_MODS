import sys
import pickle

def parse_ranges (fname):
    with open (fname) as f:
        fl = f .readlines ()

    ue_pos_dict = {} #UE-id as key to ue position
    enb_pos_dict = {} #enb-id as key to enb position
    measurement_rsrp_dict = {} #ue-id as key to a dictionary on time
    measurement_rsrq_dict = {} #ue-id as key to a dictionary on time 

    for l in fl:
        if l .find (" imsi=") != -1:
            d = l .split ()
            #time = int (float (d [0]) * 2 + 0.5)
            time = int (float (d [0]))
            ue = int (d [1] .split ('=') [1])
            enb = int (d [2] .split ('=') [1])
            rsrp = int (d [4] .split ('=') [1])
            rsrp_dbm = int (d [5] [1:])
            rsrq = int (d[7] .split ('=') [1])
            rsrq_db = float (d [8] [1:])

            if ue not in measurement_rsrp_dict:
                measurement_rsrp_dict [ue] = {}
                measurement_rsrq_dict [ue] = {}
            if time not in measurement_rsrp_dict [ue]:
                measurement_rsrp_dict [ue] [time] = set ([])
                measurement_rsrq_dict [ue] [time] = set ([])
            measurement_rsrp_dict [ue] [time] .add ((enb, rsrp, rsrp_dbm))
            measurement_rsrq_dict [ue] [time] .add ((enb, rsrq, rsrq_db))
            
            if enb not in enb_pos_dict:
                enb_x, enb_y = [float (v) for v in d [3].split ('=') [1] [1:-1].split (',')]
                enb_pos_dict [enb] = (enb_x, enb_y)

        elif l .find ("0:: C") != -1:
            d = l .split ()
            ue_x = float (d [3] .split ('=') [1] [:-1])
            ue_y = float (d [4] .split ('=') [1])
            ue = int (d [5] .split (':') [1])
            
            ue_pos_dict [ue] = (ue_x, ue_y)

    return ue_pos_dict, enb_pos_dict, measurement_rsrp_dict, measurement_rsrq_dict

def write_to_file (case, data_dict, context):
    with open (context + '/' + context + '_' + case, 'w') as f, open (context + '/' + context + '_' + case + '_' + 'pickle_dump', 'wb') as fp:
        if (case == 'ue_pos') or (case == 'enb_pos'):
            for k in sorted (data_dict .keys ()):
                print (k, data_dict [k], file = f)

        if (case == 'rsrp') or (case == 'rsrq'):
            for k in sorted (data_dict .keys ()):
                ue_time_data = data_dict [k]
                for t in sorted (ue_time_data .keys ()):
                    print (k, t, ue_time_data [t], file = f)
        pickle .dump (data_dict, fp)
    return True

if __name__ == '__main__':
    ue_pos, enb_pos, rsrp_meas, rsrq_meas = parse_ranges (sys .argv [1])
    context = sys .argv [-1]
    for case, var in zip (['ue_pos', 'enb_pos', 'rsrp', 'rsrq'], [ue_pos, enb_pos, rsrp_meas, rsrq_meas]) :
        write_to_file (case, var, context)
