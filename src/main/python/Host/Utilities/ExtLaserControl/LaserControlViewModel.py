import wx

class LaserControlViewModel(object):
    def __init__(self, model, view):
        self.model = model
        self.view = view
        view.Bind(wx.EVT_TIMER, self.on_timer, view.process_rd_timer)
        view.process_rd_timer.Start(milliseconds=2000)

    def on_timer(self, event):
        self.model.process_task()


