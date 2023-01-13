#!/usr/bin/pytgon
import sys
import random
import math
import collections
import networkx as nx
import itertools as it
import my_modules .my_tracing as debugging
import my_modules .my_io as io

class Preprocessing:
    def __init__ (self, ue_positions_file, enb_positions_file):
        debugging .log ("Initializing Preprocessing")
        self .lambda_threshold      = -85
        self .G                     = nx .DiGraph ()
        self .ue_positions          = io .pickle_load (ue_positions_file)
        self .ue_positions_index    = sorted (self .ue_positions .keys ())
        self .enb_positions         = io .pickle_load (enb_positions_file)
        self .sink                  = self .node (self .ue_positions_index [-1] + 1, 0)
        self .result                = collections .defaultdict (dict)
        
    def __enter__ (Self):
        debugging .log ("Enter Preprocessing")

    def __exit__ (self):
        debugging .log ("Exit Preprocessing")

    @debugging .trace (level = 1)
    def run (self):
        for p in self .ue_positions_index [:-1]:
            self .G .add_weighted_edges_from (self .edge_generator (p, 
                                                                    self .predict (self .ue_positions [p]),
                                                                    self .predict (self .ue_positions [p + 1])))

        self .G .add_weighted_edges_from (self .edge_generator (self .ue_positions_index [-1], 
                                                                self .predict (self .ue_positions [self .ue_positions_index [-1]]),
                                                                [self .enb (self .sink)]))
        self .preprocess ()
        return self .result
    
    @debugging .trace (level = 2)
    def predict (self, ue_pos) :
        predicted_enbs = set ([])
        for enb in self .enb_positions .keys ():
            signal_strength_dBm = self .log_distance_signal_strength (self .enb_positions [enb], ue_pos)
            if signal_strength_dBm >= self .lambda_threshold :
                predicted_enbs .add(enb) 
        return list (predicted_enbs)
    
    @debugging .trace (level = 4)
    def node (self, time, enb) :
        return int ((time * 1e9) + (enb))

    @debugging .trace (level = 4)
    def enb (self, node) :
        return int (node % 1e9)

    @debugging .trace (level = 2)
    def edge_generator (self, p, enbs, enbs_next) :
        for e1, e2 in it .product (enbs, enbs_next) :
            weight = 0 if e1 == e2 else 1
            yield (self .node (p, e1), self .node (p + 1, e2), weight)

    @debugging .trace (level = 2)
    def preprocess (self) :
        for p in self .ue_positions_index :
            enbs = self .predict (self .ue_positions [p])
            for enb in enbs :
                self .result [p] [enb] = self .find_next_hop_for_shortest_path_to_sink (self .node (p, enb))

    @debugging .trace (level = 3)
    def find_next_hop_for_shortest_path_to_sink (self, node) :
        path = nx .dijkstra_path (self .G, node, self .sink)
        return self .enb (path [1])

    @debugging .trace (level = 5)
    def calc_distance (self, p1, p2):
        return math .sqrt (math .pow ((p1 [0] - p2 [0]), 2) + math.pow ((p1 [1] - p2 [1]), 2))

    @debugging .trace (level = 4)
    def log_distance_signal_strength (  self, enb_pos, ue_pos,
                                        tx_power_dBm = 5,               #eNB transmitt power scaled from 46 to 5
                                        gain_tx = 1,                    #no gain at transmitter
                                        gain_rx = 1,                    #no gain at receiver
                                        reference_distance = 11,        #need to confirm the value in meters
                                        system_loss = 1,                #system loss , 1 means no loss
                                        wavelength = (1 / float (55)),  #1800 mhz -> 1/6 meters - scaled as 1:9
                                        exponent = 2                    #could be 4 (alpha)
                                        ) :
        distance = self .calc_distance (enb_pos, ue_pos)
        tx_pow_mW = math .pow (10, float (tx_power_dBm) / 10) #p_(dbm)  = 10 * log (p_(mW) / 1 mW)
        rx_pow_ref_mW = ((tx_pow_mW * gain_tx * gain_rx * math .pow (wavelength, 2)) 
                                / (math .pow (4 * math .pi * reference_distance, 2) * system_loss))
        rx_pow_dbm = 10 * math .log (rx_pow_ref_mW, 10)

        if distance < reference_distance:
            signal_strength = rx_pow_dbm
        else :
            path_loss = exponent * 10 * math .log (reference_distance / distance, 10)
            signal_strength = rx_pow_dbm + path_loss
        return signal_strength
        

if __name__ == "__main__":
    ue_positions_fname, enb_positions_fname = sys .argv [1:]
    pp = Preprocessing (ue_positions_fname, enb_posisions_fname)
    ret = pp .run ()
    for p in ret .keys ():
        print ("Position", p, "Keys:", list (ret [p] .keys ()))
        for e in ret [p] .keys () :
            print ("enb", e, "next hop", ret [p] [e])

