import matplotlib
import numpy as np
class mplConnect(object):
    def __init__(self,canvas,data_loaded_flag):
        self.canvas = canvas
        self.data_loaded_flag = data_loaded_flag
        self.run_number = None
        self.plot_ID = None
        self.new_click = False
        self.cid = self.canvas.mpl_connect('button_press_event', self.on_click)
    
    def on_click(self,event):
        scalar_two = 2
        if (self.data_loaded_flag == 1 and event.button == 1 and
        event.xdata != None and event.ydata != None):
            self.x_data, self.y_data = event.xdata, event.ydata
        ### Testing which of the two plots were clicked
        if event.y > self.canvas.GetSize()[1]/scalar_two:
            self.plot_ID = 'top'
            self.new_click = True
            self.determine_run_number()
        else:
            self.plot_ID = 'bottom'
            self.new_click = True
            self.calculate_point(self.x_data)

   


    def determine_run_number(self):
        '''returns the run number of the data point selected'''
        self.run_number = self.round_this(self.x_data)


    def round_this(self,point):
        value = None
        if isinstance(point,float):
            value = int(np.around(point))
        elif isinstance(point, int):
           value = np.rint(point)
        return value
        
