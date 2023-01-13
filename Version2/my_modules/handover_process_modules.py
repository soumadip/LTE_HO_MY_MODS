
import my_modules .my_tracing as debugging
import my_modules .my_io as io


class HandoverExecutionModule :
    def __init__ (self, uecs_obj, enbcs_obj) :
        self .uecs_module = uecs_obj
        self .enbcs_module = enbcs_obj

    @debugging .trace (level = 2)
    def execute_handover(self, time, ue, src, dst):
        if src == dst:
            debugging .log ("UE", ue, "stays under eNB", src, "at time", time)
        elif src == -1:
            self .attach_ue_in_system (time, ue, dst)
        elif dst == -1:
            self .remove_ue_from_system (time, ue, src)
        else :
            self .transfer_ue (time, ue, src, dst)

    @debugging .trace (level = 2)
    def attach_ue_in_system (self, time, ue, target):
        debugging .log ("UE", ue, "is attached to eNB", target, "at time", time)
        self .enbcs_module .add_ue_to_enb (time, ue, target)
        self .uecs_module .update_ue_association (time, ue, target)

    @debugging .trace (level = 2)
    def remove_ue_from_system (self, time, ue, serving):
        debugging .log ("UE", ue, "is removed from eNB", serving, "at time", time)
        self .enbcs_module .remove_ue_from_enb (time, ue, serving)
        self .uecs_module .update_ue_association (time, ue, -1)

    @debugging .trace (level = 2)
    def transfer_ue (self, time, ue, serving, target):
        debugging .log ("UE", ue, ": Handover from eNB", serving, "to eNB", target, "at time", time)
        self .enbcs_module .remove_ue_from_enb (time, ue, serving)
        self .enbcs_module .add_ue_to_enb (time, ue, target)
        self .uecs_module .update_ue_association (time, ue, target)

    @debugging .trace (level = 1)
    def initialize_connection_status_for_time (self, time) :
        debugging .log ("Initializing UE and eNB connection statuses for time", time)
        self .uecs_module .load_connections_for_time (time)
        self .enbcs_module .load_connections_for_time (time)
