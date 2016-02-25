import wx

class SetupParameters(wx.Frame):
    def __init__(self, main_frame):
            self.main_frame = main_frame
            title = 'Setup Chromatography Parameters'
            wx.Frame.__init__(self, None, title = title, size=(300,285)) #275
            self.setup_panel = wx.Panel(self, -1)
            sizer_far_left = wx.BoxSizer(wx.VERTICAL)
            empty_text_one = wx.StaticText(self.setup_panel, -1, '', size =(10,-1))
            sizer_far_left.Add(empty_text_one, -1, wx.EXPAND)
            
            
            text_one    = wx.StaticText(self.setup_panel, -1, 'Detection Threshold (ppm)', size = (200,20))
            text_two    = wx.StaticText(self.setup_panel, -1, 'GC Run Duration (seconds):', size = (150,20))
            text_six    = wx.StaticText(self.setup_panel, -1, 'Transit Time Duration (seconds):', size = (150,20))
            #text_five   = wx.StaticText(self.setup_panel, -1, 'Valve Delay for Filtering (seconds):', size = (150,20))
            #text_ten    = wx.StaticText(self.setup_panel, -1, 'Valve Duration for Filtering (seconds):', size = (150,20))
            text_three  = wx.StaticText(self.setup_panel, -1, 'Number of SEQ1 GC Runs:', size = (150,20))
            text_seven  = wx.StaticText(self.setup_panel, -1, 'Number of SEQ2 GC Runs:', size = (150,20))
            text_eight  = wx.StaticText(self.setup_panel, -1, 'Number of SEQ3 GC Runs:', size = (150,20))
            text_nine   = wx.StaticText(self.setup_panel, -1, 'Number of SEQ4 GC Runs:', size = (150,20))
            text_four   = wx.StaticText(self.setup_panel, -1, 'Run Indefinitely', size = (150,20))
            text_lst    = [text_one,text_two,text_six,text_three,
                            text_seven,text_eight,text_nine,text_four]

            sizer_left = wx.BoxSizer(wx.VERTICAL)
            for text in text_lst:
                sizer_left.Add(text, 0, wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.EXPAND)
           
            self.var_one    = wx.TextCtrl(self.setup_panel, -1, value='100', size = (50,20))
            self.var_two    = wx.TextCtrl(self.setup_panel, -1, value='450', size = (50,20))
            self.var_three  = wx.TextCtrl(self.setup_panel, -1, value='120', size = (50,20))
            #self.var_five   = wx.TextCtrl(self.setup_panel, -1, value='10', size = (50,20))
            #self.var_ten    = wx.TextCtrl(self.setup_panel, -1, value='0', size = (50,20))
            self.var_six    = wx.TextCtrl(self.setup_panel, -1, value='5', size = (50,20))
            self.var_seven  = wx.TextCtrl(self.setup_panel, -1, value='5', size = (50,20))
            self.var_eight  = wx.TextCtrl(self.setup_panel, -1, value='10', size = (50,20))
            self.var_nine   = wx.TextCtrl(self.setup_panel, -1, value='0', size = (50,20))
            self.var_four   = wx.CheckBox(self.setup_panel, -1)
            var_lst = [self.var_one,self.var_two,self.var_three,self.var_six,
                        self.var_seven,self.var_eight,self.var_nine,self.var_four]

            sizer_right = wx.BoxSizer(wx.VERTICAL)
            for var in var_lst:
                sizer_right.Add(var, -1, wx.ALIGN_LEFT)
            
            sizer_bottom = wx.BoxSizer(wx.HORIZONTAL)
            button_cancel= wx.Button(self.setup_panel, id=-1, label='Cancel')
            button_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
            button_ok = wx.Button(self.setup_panel, id=-1, label='OK')
            button_ok.Bind(wx.EVT_BUTTON, self.on_ok)
            sizer_bottom.Add(button_ok, -1, wx.ALIGN_RIGHT)
            sizer_bottom.Add(button_cancel, -1, wx.ALIGN_RIGHT)

            sizer_top = wx.BoxSizer(wx.HORIZONTAL)
            
            sizer_top.Add(sizer_far_left, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP)
            sizer_top.Add(sizer_left, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP)
            sizer_top.Add(sizer_right, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP)
            sizer_top.Add(empty_text_one, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP)
            
            sizer = wx.BoxSizer(wx.VERTICAL)
            empty_text_two = wx.StaticText(self.setup_panel, -1, '', size =(-1,10))
            empty_text_three = wx.StaticText(self.setup_panel, -1, '', size =(-1,10))
            sizer.Add(empty_text_two, 0, wx.ALIGN_TOP | wx.EXPAND)
            sizer.Add(sizer_top, 0, wx.ALIGN_TOP | wx.EXPAND)
            sizer.Add(empty_text_three, 0, wx.ALIGN_TOP | wx.EXPAND)
            sizer.Add(sizer_bottom, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)

            self.setup_panel.SetSizer(sizer, wx.EXPAND)


    def on_ok(self, event):
            error_flag = False
            try:
                concentration_threshold = float(self.var_one.GetValue())
                duration = float(self.var_two.GetValue())
                transit_duration = float(self.var_three.GetValue())
                
                max_seq1 = int(self.var_six.GetValue())
                max_seq2 = int(self.var_seven.GetValue())
                max_seq3 = int(self.var_eight.GetValue())
                max_seq4 = int(self.var_nine.GetValue())
                
                lst = [max_seq1, max_seq2, max_seq3, max_seq4]
                lst_value = [1,2,3,4] ## seq numbers that get passed to gc
                max_run = sum(lst)
                
                seq_lst = []
                for i,seq in enumerate(lst):
                    for j in range(seq):
                        seq_lst.append(lst_value[i])
                
                
                #valve_delay = float(self.var_five.GetValue())
                #valve_duration = float(self.var_ten.GetValue())
            except:
                wx.MessageBox('Please Enter Valid Numbers.', 'Error', wx.OK | wx.ICON_ERROR)
                error_flag = True
            if not error_flag:
                self.main_frame.page_one.plot_area.peak_detector.concentration_threshold = concentration_threshold
                self.main_frame.page_one.plot_area.peak_detector.dynamic_threshold = concentration_threshold
                self.main_frame.page_one.plot_area.run_ctrl_params.run_duration = duration
                #self.main_frame.page_one.plot_area.baseline_control.open_sample_valve_delay = valve_delay
                #self.main_frame.page_one.plot_area.baseline_control.open_sample_valve_duration = valve_duration
                if self.main_frame.read_data_file is None:
                    if self.var_four.GetValue() == True:
                        self.main_frame.page_one.plot_area.run_ctrl_params.max_runs = -1
                    elif self.var_four.GetValue() == False:
                       self.main_frame.page_one.plot_area.run_ctrl_params.max_runs = max_run
                   
                self.main_frame.page_one.plot_area.run_ctrl_params.seq_lst = seq_lst
                self.main_frame.page_one.plot_area.baseline_control.furnace_delay = transit_duration
                
                
                self.main_frame.setup_parameters_flag = True
                self.Destroy()
        
    def on_cancel(self, event):
            self.Destroy()

