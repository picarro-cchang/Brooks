class RunCtrlParams(object):
    def __init__(self):
        self.start_time = 0
        self.start_local_time = 0
        self.run_duration = 0 #seconds
        self.max_runs = 0
        self.seq_lst = []
        self.run_cnt = 0
        ### 
        self.plot_timer = 0
        self.plot_start_time = 0
        self.delay_for_plot_update = 0.2 #2.0 #seconds

    def clear_all(self):
        self.run_cnt = 0
        self.start_time = 0
        self.start_gmttime = 0
        self.plot_timer = 0
        self.plot_start_time = 0
        
    def next_sequence(self):
        index_shift = -1
        return self.seq_lst[self.run_cnt % self.max_runs + index_shift]
