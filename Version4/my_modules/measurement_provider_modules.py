import math
import my_modules.my_tracing as debugging

class RSRPMeasurementProviderModule :
    def __init__ (self, rsrp_meas_data, enbpp_obj, uepp_obj, lambda_threshold) :
        self .uepp_module = uepp_obj
        self .rsrp_meas_dict = rsrp_meas_data          #[pos] [time] = [set([(enb, rsrp, power)...])]
        self .enbpp_module = enbpp_obj
        self .lambda_threshold = lambda_threshold

    @debugging .trace (level = 2)
    def measurement_report (self, t, ue, lambda_th) :
        ue_pos = self .uepp_module .get_ue_position (ue, t)
        meas = {}
        for enb, rsrp, power_dbm in self .rsrp_meas_dict [ue_pos] [t] :
            if power_dbm >= lambda_th :
                if enb not in meas :
                    meas [enb] = [rsrp]
                else :
                    meas [enb] += [rsrp]

        measurements = []
        for enb in meas :
            avg_rsrp = sum (meas [enb]) / len (meas [enb])
            measurements .append ((enb, avg_rsrp))

        return measurements

    @debugging .trace (level = 2)
    def get_reading_for (self, ue, t, enb) :
        ue_pos = self . uepp_module .get_ue_position (ue, t)
        reading = [(rsrp, dbm) for e, rsrp, dbm in self .rsrp_meas_dict [ue_pos] [t] 
                                    if e == enb]
        if not bool (reading):
            reading = [(self .lambda_threshold - 30 + 141, self .lambda_threshold - 30)]
        avg_dbm = sum ([x [1] for x in reading]) / len (reading)
        avg_rsrp = sum ([x [0] for x in reading]) / len (reading)
        return (avg_rsrp, avg_dbm)

    @debugging .trace (level = 4)
    def calc_distance (self, p1, p2):
        return math .sqrt (math .pow ((p1 [0] - p2 [0]), 2) + math.pow ((p1 [1] - p2 [1]), 2))

    @debugging .trace (level = 3)
    def log_distance_signal_strength (  self, enb_pos, ue_pos,
                                        tx_power_dBm = 5,               #eNB transmitt power scaled from 46 to 5
                                        gain_tx = 1,                    #no gain at transmitter
                                        gain_rx = 1,                    #no gain at receiver
                                        reference_distance = 11,        #need to confirm the value in meters
                                        system_loss = 1,                #system loss , 1 means no loss
                                        wavelength = (1 / float (55)),  #1800 mhz -> 1/6 meters - scaled as 1:9
                                        exponent = 2                  #could be 4 (alpha)
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
        
    @debugging .trace (level = 2)
    def predict_measurement_report (self, t, ue, lambda_th):
        predicted_meas = set ([])
        for enb in self .enbpp_module .get_set_of_enbs () :
            signal_strength_dBm = self .log_distance_signal_strength (  self .enbpp_module .get_enb_position_XY (enb), 
                                                                        self .uepp_module .get_ue_position_XY (ue, t))
            if signal_strength_dBm >= lambda_th :
                rsrp = round (141 + signal_strength_dBm)
                predicted_meas .add((enb, rsrp)) 
        return list (predicted_meas)


class RSRQMeasurementProviderModule :
    def __init__ (self, rsrq_meas_data, enbpp_obj, uepp_obj, lambda_threshold = 25) :
        self .uepp_module = uepp_obj
        self .rsrq_meas_dict = rsrq_meas_data          #[pos] [time] = [set([(enb, rsrp, power)...])]
        self .enbpp_module = enbpp_obj
        self .lambda_threshold = lambda_threshold #??

    @debugging .trace (level = 2)
    def measurement_report (self, t, ue, lambda_th):
        ue_pos = self .uepp_module .get_ue_position (ue, t)
        meas = {}
        for enb, rsrq, power_db in self .rsrq_meas_dict [ue_pos] [t] :
            if power_db >= lambda_th : #??
                if enb not in meas :
                    meas [enb] = [rsrq]
                else :
                    meas [enb] += [rsrq]

        measurements = []
        for enb in meas :
            avg_rsrq = sum (meas [enb]) / len (meas [enb])
            measurements .append ((enb, avg_rsrq))

        return measurements

    @debugging .trace (level = 2)
    def get_reading_for (self, ue, t, enb) :
        reading = [(rsrq, db) for e, rsrq, db in self .rsrq_meas_dict [self . uepp_module .get_ue_position (ue, t)] [t] if e == enb]
        if not bool (reading):
            return [(self .lambda_threshold - 30 + 141, self .lambda_threshold - 30)] #??
        else :
            return reading



if __name__ == '__main__':
    debugging .log ("MeasurementProviderModule")
