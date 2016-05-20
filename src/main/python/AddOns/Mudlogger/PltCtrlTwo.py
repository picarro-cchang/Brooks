import pylab
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties


class PltCtrlTwo(object):
    def __init__(self):
        self.shift_cnt = 0
        self.min_range = 0
        self.max_range = 25

        self.dpi = 150
       
        self.selected_run = 0
        self.default_index = 0 #used for y-axis label
        self.plot_one_selection = None
        self.user_bounds = None
        self.initialize_plots()

    def initialize_plots(self):
        self.create_two_plots()
        self.label_plots()
        self.set_tick_labels()
        return self.fig

    def create_two_plots(self):
        self.fig = plt.figure(dpi=self.dpi, facecolor='white', frameon=True)
        self.ax_one = self.fig.add_subplot(211)
        self.ax_one.set_axis_bgcolor('white')
        self.ax_two = self.fig.add_subplot(212)
        self.ax_two.set_axis_bgcolor('white')

    def clear_plot_data(self):
        self.ax_one.cla()
        self.ax_two.cla()
        self.label_plots()
        self.set_tick_labels()

    def plot_data(self,x,Y,t,c,label_index,labels):
        increase_by_one = 1
        self.clear_plot_data()
        self.change_top_plot_y_label(label_index)
        if len(Y) != 0 and len(Y[0]) != 0:
            number_of_species = len(Y)
            number_of_samples = len(Y[0])
            for i in range(1,number_of_species):
                self.plot_one = self.ax_one.plot(x,Y[i], 'o', markersize=3, label=labels[i])[0]
                self.reset_plot_range(self.max_range,self.shift_cnt,Y)
                self.set_tick_labels()
            self.set_legend(number_of_species)
            #self.ax_one.set_xlim(0,max(map(len,Y))+increase_by_one)
            #self.ax_one.set_ylim(0.8*min(map(min,Y)),1.2*max(map(max,Y)))

        return self.fig

    def set_legend(self,number_of_species):
        if number_of_species > 0:
            font_prop = FontProperties()
            if number_of_species < 5:
                font_prop.set_size(5)
            elif 4 < number_of_species < 7:
                font_prop.set_size(4)
            else:
                font_prop.set_size(3)
            legend = self.ax_one.legend(bbox_to_anchor = (0,1.05,1,0.125),
                                        loc=1,
                                        ncol=number_of_species,
                                        prop = font_prop,
                                        scatterpoints = 1)
            legend.get_frame().set_alpha(0)
        
    def highlight_selection(self,x,y):
        if self.plot_one_selection is not None:
            try:
                self.plot_one_selection.remove()
            except:
                pass
        self.plot_one_selection = self.ax_one.plot(x,y,'oy',alpha=0.5)[0]

    def display_selected_GC_run(self,x,y):
        if self.ax_two is not None:
            self.clear_bottom_plot()
        self.plot_two = self.ax_two.plot(x,y,color='black')[0]

    def display_integration_bounds(self,p_ibounds,s_time,
                                   s_conc,selection):
        shift = 1
        threshold = 0
        bounds = self.convert_bounds_to_int(p_ibounds)
        for i,bound in enumerate(bounds):
            if not math.isnan(bound[0]) and not math.isnan(bound[1]):
                if i + shift != selection:
                    color = 'blue'
                else:
                    color = 'red'
                self.i_bounds_two = self.ax_two.plot(s_time[bound[0]],  
                                                     s_conc[bound[0]],
                                                     s_time[bound[1]-shift],
                                                     s_conc[bound[1]-shift],
                                                     marker = '|',
                                                     markersize = 15,
                                                     color = color)
                                                     
    def display_new_integration_bounds(self,peak_cnt,s_conc,s_time,left_flag,right_flag,
                                       left_bound,right_bound,p_ibounds,selection):
        self.clear_bottom_plot()
        bounds = []
        if left_flag:
            bounds.append(left_bound)
        if right_flag:
            bounds.append(right_bound)
        x_values = [s_time[bound] for bound in bounds]
        y_values = [s_conc[bound] for bound in bounds]
        self.display_selected_GC_run(s_time,s_conc)
        self.display_integration_bounds(p_ibounds,s_time,s_conc,selection)
        self.ax_two.plot(x_values,
                            y_values,
                            linestyle = 'None',
                            marker = 'v',
                            markersize = 6,
                            color = 'red')

    def convert_bounds_to_int(self,ibounds):
        int_bounds = []
        for bound in ibounds:
            if bound != '':
                int_bounds.append(map(int,bound.replace('[','').replace(']','').split(',')))
            else:
                int_bounds.append([np.NaN,np.NaN])
        return int_bounds


    def clear_plots(self):
        self.clear_top_plot()
        self.clear_bottom_plot()
        self.label_top_plot()
        self.label_bottom_plot()
        self.set_tick_label_top()
        self.set_tick_label_bottom()
        self.hard_reset_plot_range()

    def clear_bottom_plot(self):
        self.ax_two.cla()
        self.label_bottom_plot()
        self.set_tick_label_bottom()

    def clear_top_plot(self):
        self.ax_one.cla()
        self.label_top_plot()
        self.set_tick_label_top()

    def label_plots(self):
        self.label_top_plot()
        self.label_bottom_plot()

    def label_top_plot(self):
        self.size = 6
        self.ax_one.set_ylabel('$\delta^{13}$C, permil', size=self.size)
        self.ax_one.set_xlabel('Sample Number', size=self.size)
        
    def change_top_plot_y_label(self,label_index):
        self.size = 6
        labels = ['$\delta^{13}$C, permil','Peak $[CO_{2}]$, ppm','t$_{ret.}$, seconds']
        self.ax_one.set_ylabel(labels[label_index])
        
    def label_bottom_plot(self):
        self.size = 6   
        self.ax_two.set_ylabel('CO$_{2}$, ppm', size=self.size)
        self.ax_two.set_xlabel('Time, seconds', size=self.size)

    def set_tick_labels(self):
        self.set_tick_label_top()
        self.set_tick_label_bottom()
        
    def set_tick_label_top(self):
        self.fontsize = 6
        pylab.setp(self.ax_one.get_xticklabels(), fontsize=self.fontsize)
        pylab.setp(self.ax_one.get_yticklabels(), fontsize=self.fontsize)
        
    def set_tick_label_bottom(self):
        self.fontsize = 6    
        pylab.setp(self.ax_two.get_xticklabels(), fontsize=self.fontsize)
        pylab.setp(self.ax_two.get_yticklabels(), fontsize=self.fontsize)

    def reset_plot_range(self,range,cnt,Y):
        ten_percent = 0.10
        first_species_index = 0
        increase_by_one = 1
        y_lower,y_upper = [],[]
        for i in np.arange(len(Y)):
            data_length = len(Y[first_species_index])
            if data_length < range:
                x_lower_limit = self.min_range
                x_upper_limit = data_length + increase_by_one
            else:
                x_lower_limit = cnt*range
                x_upper_limit = min([(cnt+1)*range,data_length])
            if x_upper_limit > x_lower_limit:
                try:
                #this try skips peak data that is emtpy for a given range
                #and the range is then choosen without that peak data
                    min_y = min([y_i for y_i in Y[i][x_lower_limit:x_upper_limit] if not math.isnan(y_i)])
                    max_y = max([y_i for y_i in Y[i][x_lower_limit:x_upper_limit] if not math.isnan(y_i)])
                    y_lower.append(min_y)
                    y_upper.append(max_y)
                except ValueError:
                    pass
        self.ax_one.set_xlim(x_lower_limit,x_upper_limit)
        y_lower_limit = min(y_lower) - ten_percent*(max(y_upper)-min(y_lower))
        y_upper_limit = max(y_upper) + ten_percent*(max(y_upper)-min(y_lower))
        if y_lower_limit == y_upper_limit:
            y_lower_limit = y_lower_limit - increase_by_one
            y_upper_limit = y_upper_limit + increase_by_one
        self.ax_one.set_ylim(y_lower_limit,y_upper_limit)

    def hard_reset_plot_range(self):
        self.ax_one.set_xlim(self.min_range,self.max_range)
        self.ax_one.set_ylim(0,1)




