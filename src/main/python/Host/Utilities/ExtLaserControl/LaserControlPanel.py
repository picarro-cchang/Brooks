from Host.Utilities.ExtLaserControl.LaserControlPanelGui import LaserControlPanelGui

class LaserControlPanel(LaserControlPanelGui):
    def __init__(self, *args, **kwargs):
        super(LaserControlPanel, self).__init__(*args, **kwargs)
        self.view_model = None

    def set_view_model(self, view_model):
        self.view_model = view_model

    def onLevelSelect(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.update_level_index(event.GetEventObject().GetSelection())
        event.Skip()

    def onLevelEntryEnter(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        print "Event handler 'onLevelEntryEnter' not implemented!"
        event.Skip()

    def onUpdatedLevelEnter(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.update_selected_level(int(event.GetEventObject().GetValue()))
        event.Skip()

    def onSlopeFactorEnter(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.set_model_parameter("slope_factor", float(event.GetEventObject().GetValue()))
        event.Skip()

    def onTimeBetweenStepsEnter(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.set_model_parameter("time_between_steps", int(event.GetEventObject().GetValue()))
        event.Skip()

    def onUpperWindowEnter(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.set_model_parameter("upper_window", int(event.GetEventObject().GetValue()))
        event.Skip()

    def onLowerWindowEnter(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.set_model_parameter("lower_window", int(event.GetEventObject().GetValue()))
        event.Skip()

    def onBinningRdEnter(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.set_model_parameter("binning_rd", int(event.GetEventObject().GetValue()))
        event.Skip()

    def onUpdateLevelsCheck(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.set_model_parameter("update_levels", event.GetEventObject().GetValue())
        event.Skip()

    def onUpdateWaveformCheck(self, event):  # wxGlade: LaserControlPanelGui.<event_handler>
        self.view_model.set_model_parameter("update_waveform", event.GetEventObject().GetValue())
        event.Skip()

