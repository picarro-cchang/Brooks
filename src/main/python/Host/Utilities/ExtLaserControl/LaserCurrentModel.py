from Host.Utilities.ExtLaserControl.Subject import Subject
import time

class StatsCollector(object):
    """Statistics collection object which transitions from arithmetic
    averaging to exponential averaging"""
    def __init__(self, max_samples):
        self.average = 0.0
        self.num_samples = 0
        self.max_samples = max_samples

    def add_sample(self, value):
        self.num_samples = min(self.num_samples + 1, self.max_samples)
        alpha = 1.0 / self.num_samples
        self.average = alpha * value + (1.0 - alpha) * self.average

    def __repr__(self):
        return "Average of %d points: %s" % (self.num_samples, self.average)

class LaserCurrentModel(Subject):
    def __init__(self, *args, **kwargs):
        super(LaserCurrentModel, self).__init__(*args, **kwargs)
        self.slope_factor = None
        self.time_between_steps = None
        self.upper_window = None
        self.lower_window = None
        self.binning_rd = None
        self.levels = [10000, 15000, 20000, 25000, 30000, 35000]
        self.fsr_stats = {}
        self.coeffs = None
        self.max_samples = 20
        self.update_levels = None
        self.update_waveform = None

    def load_from_config(self, config):
        for key in config:
            if hasattr(self, key):
                setattr(self, key, config[key])

    def find_bins(self):
        self.levels = range(5000, 36000, 5000)
        time.sleep(2.0)

    def update_fsr_stats(self, fsr_index, current):
        if fsr_index not in self.fsr_stats:
            self.fsr_stats[fsr_index] = StatsCollector(self.max_samples)
        self.fsr_stats[fsr_index].add_sample(current)

class LaserCurrentModels(object):
    def __init__(self):
        self.models = []

    def load_from_config(self, config):
        if "Lasers" not in config:
            raise ValueError("Configuration file should have a section named Lasers")
        cfg_lasers = config["Lasers"]
        keys = ["Laser1", "Laser2", "Laser3", "Laser4"]
        for key in keys:
            if key in cfg_lasers:
                model = LaserCurrentModel(name=key)
                model.load_from_config(cfg_lasers[key])
                self.models.append(model)
            else:
                self.models.append(None)
        print self.models