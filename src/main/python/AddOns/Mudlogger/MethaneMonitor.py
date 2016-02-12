class MethaneMonitor(object):
    def __init__(self):
        self.methane_flag_threshold = 5.0 # ppm

    def check_methane(self, methane_concentration):
        return methane_concentration > self.methane_flag_threshold





