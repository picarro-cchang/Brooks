import numpy as np

class DataCtrlTwo(object):
    def __init__(self):
        self.number_of_runs = 65
        self.duration_GC_traces = 250
        self.number_of_species = 4

    def initialize_data_trace(self):
        '''Creates concentration and time lists'''
        return [[],[],[]]

    def initialize_data_integrated(self):
        '''Creates sample isotope,concentration,
        retention time,integration bounds lists'''
        return [[],[],[],[],[]]

    def initialize_faux_data_trace(self):
        conc, time = [], []
        for run in range(self.number_of_runs):
            conc.append([np.random.random() for i in np.arange(0,self.duration_GC_traces)])
            time.append(np.arange(0,self.duration_GC_traces))
        return [time,conc]

    def initialize_faux_data_integrated(self):
        sample, iso, conc, retent, int_bnds = [],[],[],[],[]
        for species in np.arange(self.number_of_species):
            sample.append([])
            iso.append([])
            conc.append([])
            retent.append([])
            int_bnds.append([])
            for run in range(self.number_of_runs):
                sample[species] = np.arange(1,self.number_of_runs+1)
                iso[species] = [(np.random.random() + species*10) for i in np.arange(self.number_of_runs)]
                conc[species] = [(np.random.random() + species*100) for i in np.arange(self.number_of_runs)]
                retent[species] = [(np.random.random() + species*30) for i in np.arange(self.number_of_runs)]
                int_bnds[species] = [(np.random.random() + species) for i in np.arange(self.number_of_runs)]
        return [iso,conc,retent,int_bnds,sample]

