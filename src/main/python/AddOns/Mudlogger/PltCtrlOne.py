import pylab
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

class PltCtrlOne(object):
    def initialize_plots(self,var_lst):

        self.dpi = 150
        self.create_two_plots()
        self.label_plots()
        self.set_tick_labels()
        if var_lst is not None:
            self.update_plots(var_lst)
        return self.fig
       
    def clear_plots(self):
        self.ax_one.cla()
        self.ax_one.set_ylim(-1,1)
        self.ax_two.cla()
        self.ax_two.set_ylim(-1,1)
        self.label_plots()
        self.set_tick_labels()

    def label_plots(self):
        self.size = 6
        self.ax_one.set_ylabel('CO$_{2}$, ppm', size=self.size)
        self.ax_one.set_xlabel('Time, seconds', size=self.size)
        self.ax_two.set_ylabel('$\delta^{13}$C, permil', size=self.size)
        self.ax_two.set_xlabel('Time, seconds', size=self.size)

    def set_tick_labels(self):
        self.fontsize = 6
        pylab.setp(self.ax_one.get_xticklabels(), fontsize=self.fontsize)
        pylab.setp(self.ax_one.get_yticklabels(), fontsize=self.fontsize)
        pylab.setp(self.ax_two.get_xticklabels(), fontsize=self.fontsize)
        pylab.setp(self.ax_two.get_yticklabels(), fontsize=self.fontsize)
        
        
    def min_with_nan(self,lst):
        minimum_start = 1e9
        minimum = minimum_start
        for value in lst:
            if not np.isnan(value) and value < minimum:
                minimum = value
        if minimum != minimum_start:
            return minimum
        else:
            return -1
            
    def max_with_nan(self,lst):
        maximum_start = -1e9
        maximum = maximum_start
        for value in lst:
            if not np.isnan(value) and value > maximum:
                maximum = value
        if maximum != maximum_start:
            return maximum
        else:
            return 1

    def update_plots(self,vars):
        min_xlim_value = 0.0
        min_range_threshold = 2.0
        max_range_to_plot = 300
        x,y_one,y_two = vars[0],vars[1],vars[2]
        self.plot_one = self.ax_one.plot(x,y_one)[0]
        self.plot_two = self.ax_two.plot(x,y_two)[0]
        
        try:
            y_top_min,y_top_max = min(y_one), max(y_one)
            y_bottom_min, y_bottom_max = self.min_with_nan(y_two), self.max_with_nan(y_two)
            if (y_top_max - y_top_min) < min_range_threshold:
                y_top_min -= min_range_threshold
                y_top_max += min_range_threshold
            
            self.ax_one.set_ylim(y_top_min,y_top_max)
            if y_bottom_min != y_bottom_max:
                self.ax_two.set_ylim(y_bottom_min,y_bottom_max)
            else:
                self.ax_two.set_ylim(y_bottom_min-min_range_threshold,y_bottom_max+min_range_threshold)
        except ValueError:
            pass
        
        try:
            length_of_data = x[-1]
            if length_of_data < max_range_to_plot:
                self.ax_one.set_xlim(min_xlim_value,length_of_data)
                self.ax_two.set_xlim(min_xlim_value,length_of_data)
            else:
                self.ax_one.set_xlim(length_of_data-max_range_to_plot,length_of_data)
                self.ax_two.set_xlim(length_of_data-max_range_to_plot,length_of_data)
        except IndexError:
            pass
        self.set_tick_labels()
    
    def create_two_plots(self):
        self.fig = plt.figure(dpi=self.dpi, facecolor='white', frameon=True)
        self.ax_one = self.fig.add_subplot(211)
        self.ax_one.set_axis_bgcolor('white')
        self.ax_two = self.fig.add_subplot(212)
        self.ax_two.set_axis_bgcolor('white')
        self.ax_two.set_ylim(-1,1)


