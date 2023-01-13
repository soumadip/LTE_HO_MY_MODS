import my_modules .my_tracing as debugging


class UEPositionProviderModule :
    def __init__ (self, common_config, ue_start_times, ue_pos) :
        debugging .log ("Initializing UEPositionProviderModule")
        self .journey_length = common_config ['journey_length']
        self .ue_start_times = ue_start_times
        self .ue_pos = ue_pos

    @debugging .trace (level = 3)
    def ue_still_in_system (self, ue, time) :
        start_time = self .get_ue_start_time (ue)
        return (time >= start_time) and (time <= (start_time + self .journey_length))

    @debugging .trace (level = 3)
    def get_ue_start_time (self, ue):
        return self .ue_start_times [ue]

    @debugging .trace (level = 3)
    def get_ue_end_time (self, ue):
        return self .ue_start_times [ue] + self .journey_length

    @debugging .trace (level = 2)
    def get_ue_position (self, ue, time) :
        if self .ue_still_in_system (ue, time) :
            return time - self .get_ue_start_time (ue) + 1
        else :
            return None

    @debugging .trace (level = 2)
    def get_ue_position_XY (self, ue, time) :
        return self .ue_pos [self .get_ue_position (ue, time)]

    @debugging .trace (level = 2)
    def get_journey_end_time (self, ue) :
        return self .get_ue_start_time (ue) + self .journey_length

    @debugging .trace (level = 2)
    def get_set_of_ues (self) :
        return set (self .ue_start_times .keys ())


class eNBPositionProviderModule :
    def __init__ (self, enb_pos) :
        debugging .log ("Initializing eNBPositionProviderModule")
        self .enb_pos = enb_pos

    @debugging .trace (level = 2)
    def get_enb_position_XY (self, enb) :
        return self .enb_pos [enb]

    @debugging .trace (level = 2)
    def get_set_of_enbs (self) :
        return set (self .enb_pos .keys())

