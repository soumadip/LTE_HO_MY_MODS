
import my_modules .my_tracing as debugging
import my_modules .my_io as io

class UEConnectionStatusModule :
    def __init__ (self, ues) :
        self .set_of_ues = ues

        self .last_time_seen = 0
        self .ue_connection_status = {}

        debugging .log ("Initializing UE connection status for time", self .last_time_seen)
        self .ue_connection_status [self .last_time_seen] = {ue : -1 for ue in self .set_of_ues}

    @debugging .trace (level = 2)
    def load_connections_for_time (self, t):
        if t == self .last_time_seen :
            return
        else :
            debugging .log ("Loading UE connection status for time", t)
            self .ue_connection_status [t] = io .deep_copy (self .ue_connection_status [(t - 1)])
            self .last_time_seen = t

    @debugging .trace (level = 2)
    def get_serving_enb_of (self, ue, time) :
        return io .deep_copy (self .ue_connection_status [time] [ue])

    @debugging .trace (level = 3)
    def get_ue_connection_status_at (self, time) :
        return io .deep_copy (self .ue_connection_status [time])

    @debugging .trace (level = 2)
    def update_ue_association (self, time, ue, enb) :
        self .ue_connection_status [time] [ue] = enb

    @debugging .trace (level = 4)
    def get_set_of_ues (self):
        return io .deep_copy (self .set_of_ues)


class eNBConnectionStatusModule :
    def __init__ (self, enbs) :
        self .set_of_enbs = enbs 

        self .last_time_seen = 0
        self .enb_connection_status = {}

        debugging .log ("Initializing eNB connection status for time", self .last_time_seen)
        self .enb_connection_status [self .last_time_seen] = {e : [] for e in self .set_of_enbs}

    @debugging .trace (level = 2)
    def load_connections_for_time (self, t):
        if t == self .last_time_seen :
            return
        else :
            debugging .log ("Loading eNB connection status for time", t)
            self .enb_connection_status [t] = io .deep_copy (self .enb_connection_status [(t - 1)])
            self .last_time_seen = t

    @debugging .trace (level =2)
    def get_ues_under_enb (self, enb, time) :
        #debugging .log ("Getting UEs under enb", enb, "at time", time)
        return io .deep_copy (self .enb_connection_status [time] [enb])

    @debugging .trace (level = 3)
    def get_enb_connection_status_at (self, time) :
        return io .deep_copy (self .enb_connection_status [time])

    @debugging .trace (level = 2)
    def remove_ue_from_enb (self, time, ue, enb) :
        debugging .log (time, enb, self .enb_connection_status [time] [enb])
        self .enb_connection_status [time] [enb] .remove (ue)

    @debugging .trace (level =2)
    def add_ue_to_enb (self , time, ue, enb) :
         self .enb_connection_status [time] [enb] .append (ue)

    @debugging .trace (level = 4)
    def get_set_of_enbs (self):
        return io .deep_copy (self .set_of_enbs)

