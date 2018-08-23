import wx
import threading

def fill_checkbox(control, bool_value):
    control.SetValue(bool_value)

def fill_list_box(control, data_list):
    control.Clear()
    for datum in data_list:
        control.Append("%s" % datum)

def fill_list_box_with_diff(control, data_list):
    control.Clear()
    last = None
    for datum in data_list:
        if last is None:
            control.Append("%s" % (datum,))
        else:
            control.Append("%s %s" % (datum,datum - last))
        last = datum
class LaserCurrentViewModel(object):
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.level_index = None
        self.updated_level = None
        self.work_thread = None

        view.text_ctrl_level_entry.Bind(wx.EVT_KILL_FOCUS, view.onLevelEntryEnter)
        view.text_ctrl_updated_level.Bind(wx.EVT_KILL_FOCUS, view.onUpdatedLevelEnter)
        view.text_ctrl_slope_factor.Bind(wx.EVT_KILL_FOCUS, view.onSlopeFactorEnter)
        view.text_ctrl_time_between_steps.Bind(wx.EVT_KILL_FOCUS, view.onTimeBetweenStepsEnter)
        view.text_ctrl_upper_window.Bind(wx.EVT_KILL_FOCUS, view.onUpperWindowEnter)
        view.text_ctrl_lower_window.Bind(wx.EVT_KILL_FOCUS, view.onLowerWindowEnter)
        view.text_ctrl_binning_rd.Bind(wx.EVT_KILL_FOCUS, view.onBinningRdEnter)
        model.addListener(self.model_listener)
        model.update(changed="all")

    def model_listener(self, model):
        assert model == self.model
        print "Listener called by ", self.model.name
        self.update_view()

    def set_model_parameter(self, name, value):
        print "Set model parameter %s with %s" % (name, value)
        setattr(self.model, name, value)
        self.model.update(changed=name)

    def update_level_index(self, value):
        self.level_index = value
        self.updated_level = self.model.levels[value]
        self.view.text_ctrl_updated_level.SetValue(str(self.updated_level))

    def update_selected_level(self, value):
        if self.level_index is not None:
            self.model.levels[self.level_index] = value
            self.model.update(changed="levels")
            self.view.list_box_levels.SetSelection(self.level_index)

    def update_view(self):
        widget_lookup = {
            "updated_level" : {"control" : self.view.text_ctrl_updated_level},
            "slope_factor" : {"control" : self.view.text_ctrl_slope_factor},
            "time_between_steps" : {"control" : self.view.text_ctrl_time_between_steps},
            "upper_window" : {"control" : self.view.text_ctrl_upper_window},
            "lower_window" : {"control" : self.view.text_ctrl_lower_window},
            "binning_rd" : {"control" : self.view.text_ctrl_binning_rd},
            "levels" : {"control" : self.view.list_box_levels, "set_value" : fill_list_box_with_diff},
            "update_levels" : {"control" : self.view.checkbox_update_levels, "set_value" : fill_checkbox},
            "update_waveform" : {"control" : self.view.checkbox_update_waveform, "set_value" : fill_checkbox},
        }

        def set_widget_from(name):
            if name in widget_lookup:
                widget = widget_lookup[name]
                control = widget["control"]
                if "set_value" in widget:
                    widget["set_value"](control, getattr(self.model, name))
                else:
                    if hasattr(self.model, name):
                        control.SetValue(str(getattr(self.model, name)))

        if self.model.changed == "all":
            for name in widget_lookup:
                set_widget_from(name)
        else:
            set_widget_from(self.model.changed)

    # Not currently used
    def find_bins(self):
        if self.work_thread is not None:
            wx.MessageDialog(None, "Computation in Progress", "Busy", wx.OK | wx.ICON_EXCLAMATION).ShowModal()
            return
        def _find_bins():
            self.model.find_bins()
            wx.CallAfter(self.model.update, changed="levels")
            self.work_thread = None
        self.work_thread = threading.Thread(target=_find_bins)
        self.work_thread.setDaemon(True)
        self.work_thread.start()