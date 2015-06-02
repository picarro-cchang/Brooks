import wx
import matplotlib
import time
import threading
from pylab import *

# cursors
class Cursors:  #namespace
    HAND, POINTER, SELECT_REGION, MOVE, MAGNIFIER = range(5)
cursors = Cursors()
# Dictionary for mapping cursor names to wx cursor names
cursord = {
    cursors.MOVE : wx.CURSOR_HAND,
    cursors.HAND : wx.CURSOR_HAND,
    cursors.POINTER : wx.CURSOR_ARROW,
    cursors.SELECT_REGION : wx.CURSOR_CROSS,
    cursors.MAGNIFIER : wx.CURSOR_MAGNIFIER,
    }

# Decorator to protect access to matplotlib figure from several threads
#  self.lock should be a recursive lock
def checkLock(func):
    def wrapper(self,*a,**k):
        try:
            self.lock.acquire()
            return func(self,*a,**k)
        finally:
            self.lock.release()
    return wrapper

class FigureInteraction(object):
    def __init__(self,fig,lock):
        self.fig = fig
        self.lock = lock
        self.canvas = fig.canvas
        w = self.canvas
        # Find the nearest top-level window
        while w and not w.IsTopLevel():
            w = w.GetParent()
        self.topLevel = {self.canvas:w}
        self.lastTime = 0
        self.lastButton = 0
        self._button_pressed=None
        self._idDrag=self.canvas.mpl_connect('motion_notify_event', self.onMouseMove)
        self._active = ""
        self._idle = True
        self._xypress=[]
        self._lastCursor = None
        self.canvas.mpl_connect('button_press_event',self.onClick)
        self.canvas.mpl_connect('button_release_event',self.onRelease)
        self.canvas.mpl_connect('key_press_event',self.onKeyDown)
        self.canvas.mpl_connect('key_release_event',self.onKeyUp)
        self.canvas.mpl_connect('figure_enter_event', self.onEnterFigure)
        #self.canvas.mpl_connect('figure_leave_event', self.onLeaveFigure)
        #self.canvas.mpl_connect('axes_enter_event', self.onEnterAxes)
        #self.canvas.mpl_connect('axes_leave_event', self.onLeaveAxes)
        # Get all the subplots within the figure
        self.subplots = fig.axes
        self.autoscale = {}
        for s in self.subplots:
            self.autoscale[s] = True

    @checkLock
    def isActive(self):
        return self._active

    @checkLock
    def onEnterFigure(self,event):
        w = wx.Window.FindFocus()
        if w not in self.topLevel:
            p = w
            while p and not p.IsTopLevel():
                p = p.GetParent()
            self.topLevel[w] = p
        if self.topLevel[w] == self.topLevel[event.canvas]:
            event.canvas.SetFocus()

    @checkLock
    def onLeaveFigure(self,event):
        print "Leaving figure", event.canvas.figure
    @checkLock
    def onEnterAxes(self,event):
        print "Entering axes", event.inaxes
    @checkLock
    def onLeaveAxes(self,event):
        print "Leaving axes", event.inaxes

    @checkLock
    def onKeyDown(self,event):
        if self._active: return
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        elif event.key == "shift":
            self.setCursor(cursors.MOVE)

    @checkLock
    def onKeyUp(self,event):
        if self._active: return
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        elif event.key == "shift":
                self.setCursor(cursors.MAGNIFIER)

    @checkLock
    def draw(self):
        'redraw the canvases, update the locators'
        for a in self.fig.get_axes():
            xaxis = getattr(a, 'xaxis', None)
            yaxis = getattr(a, 'yaxis', None)
            locators = []
            if xaxis is not None:
                locators.append(xaxis.get_major_locator())
                locators.append(xaxis.get_minor_locator())
            if yaxis is not None:
                locators.append(yaxis.get_major_locator())
                locators.append(yaxis.get_minor_locator())

            for loc in locators:
                loc.refresh()
        self.canvas.draw()

    @checkLock
    def onRelease(self,event):
        # Get the axes within which the point falls
        if self._active == "ZOOM":
            self.release_zoom(event)
        elif self._active == "PAN":
            self.release_pan(event)
        self._active = ""

    @checkLock
    def release_zoom(self, event):
        if not self._xypress: return
        last_a = []

        for cur_xypress in self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, ind, lim, trans = cur_xypress

            # ignore singular clicks - 5 pixels is a threshold
            if abs(x-lastx)<5 or abs(y-lasty)<5:
                self._xypress = None
                self.draw()
                return

            x0, y0, x1, y1 = lim.extents

            # zoom to rect
            inverse = a.transData.inverted()
            lastx, lasty = inverse.transform_point( (lastx, lasty) )
            x, y = inverse.transform_point( (x, y) )
            Xmin,Xmax=a.get_xlim()
            Ymin,Ymax=a.get_ylim()

            # detect twinx,y axes and avoid double zooming
            twinx, twiny = False, False
            if last_a:
                for la in last_a:
                    if a.get_shared_x_axes().joined(a,la): twinx=True
                    if a.get_shared_y_axes().joined(a,la): twiny=True
            last_a.append(a)

            if twinx:
                x0, x1 = Xmin, Xmax
            else:
                if Xmin < Xmax:
                    if x<lastx:  x0, x1 = x, lastx
                    else: x0, x1 = lastx, x
                    if x0 < Xmin: x0=Xmin
                    if x1 > Xmax: x1=Xmax
                else:
                    if x>lastx:  x0, x1 = x, lastx
                    else: x0, x1 = lastx, x
                    if x0 > Xmin: x0=Xmin
                    if x1 < Xmax: x1=Xmax

            if twiny:
                y0, y1 = Ymin, Ymax
            else:
                if Ymin < Ymax:
                    if y<lasty:  y0, y1 = y, lasty
                    else: y0, y1 = lasty, y
                    if y0 < Ymin: y0=Ymin
                    if y1 > Ymax: y1=Ymax
                else:
                    if y>lasty:  y0, y1 = y, lasty
                    else: y0, y1 = lasty, y
                    if y0 > Ymin: y0=Ymin
                    if y1 < Ymax: y1=Ymax

            if self._button_pressed == 1:
                a.set_xlim((x0, x1))
                a.set_ylim((y0, y1))
            elif self._button_pressed == 3:
                if a.get_xscale()=='log':
                    alpha=np.log(Xmax/Xmin)/np.log(x1/x0)
                    rx1=pow(Xmin/x0,alpha)*Xmin
                    rx2=pow(Xmax/x0,alpha)*Xmin
                else:
                    alpha=(Xmax-Xmin)/(x1-x0)
                    rx1=alpha*(Xmin-x0)+Xmin
                    rx2=alpha*(Xmax-x0)+Xmin
                if a.get_yscale()=='log':
                    alpha=np.log(Ymax/Ymin)/np.log(y1/y0)
                    ry1=pow(Ymin/y0,alpha)*Ymin
                    ry2=pow(Ymax/y0,alpha)*Ymin
                else:
                    alpha=(Ymax-Ymin)/(y1-y0)
                    ry1=alpha*(Ymin-y0)+Ymin
                    ry2=alpha*(Ymax-y0)+Ymin
                a.set_xlim((rx1, rx2))
                a.set_ylim((ry1, ry2))

        self.draw()
        self._xypress = None
        self._button_pressed = None
        try: del self.lastrect
        except AttributeError: pass

    @checkLock
    def onClick(self,event):
        # Get the axes within which the point falls
        self._active = "ACTIVE"
        axes = event.inaxes
        if axes not in self.subplots:
            return
        now, button = time.time(), event.button
        delay = now - self.lastTime
        self.lastTime, self.lastButton = now, button
        if button == self.lastButton and delay<0.3:
            print "DoubleClick"
            for a in self.fig.get_axes():
                if a.in_axes(event):
                    a.relim()
                    a.autoscale(enable=True, axis='both', tight=True)
                    self.autoscale[a] = True
            self.draw()
            return
        if event.key == None:
            self._active = "ZOOM"
            self.press_zoom(event)
        elif event.key == "shift":
            self._active = "PAN"
            self.press_pan(event)
        else:
            return

    @checkLock
    def press_zoom(self, event):
        if event.button == 1:
            self._button_pressed=1
        elif  event.button == 3:
            self._button_pressed=3
        else:
            self._button_pressed=None
            return
        x, y = event.x, event.y
        self._xypress=[]
        for i, a in enumerate(self.fig.get_axes()):
            if x is not None and y is not None and a.in_axes(event) \
                    and a.get_navigate() and a.can_zoom():
                self.autoscale[a] = False
                self._xypress.append(( x, y, a, i, a.viewLim.frozen(), a.transData.frozen()))

    @checkLock
    def setCursor(self,cursor):
        if self._lastCursor != cursor:
            self.set_cursor(cursor)
            self._lastCursor = cursor

    @checkLock
    def onMouseMove(self,event):
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        else:
            if self._active=='ZOOM':
                self.setCursor(cursors.MAGNIFIER)
                if self._xypress:
                    x, y = event.x, event.y
                    lastx, lasty, a, ind, lim, trans = self._xypress[0]
                    self.draw_rubberband(event, x, y, lastx, lasty)
            elif self._active=='PAN':
                self.setCursor(cursors.MOVE)
            else:
                if event.key == None:
                    self.setCursor(cursors.MAGNIFIER)
                elif event.key == "shift":
                    self.setCursor(cursors.MOVE)
                else:
                    self.setCursor(cursors.POINTER)

    @checkLock
    def draw_rubberband(self, event, x0, y0, x1, y1):
        'adapted from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/189744'
        canvas = self.canvas
        dc =wx.ClientDC(canvas)

        # Set logical function to XOR for rubberbanding
        dc.SetLogicalFunction(wx.XOR)

        # Set dc brush and pen
        # Here I set brush and pen to white and grey respectively
        # You can set it to your own choices

        # The brush setting is not really needed since we
        # dont do any filling of the dc. It is set just for
        # the sake of completion.

        wbrush =wx.Brush(wx.Colour(255,255,255), wx.TRANSPARENT)
        wpen =wx.Pen(wx.Colour(200, 200, 200), 1, wx.SOLID)
        dc.SetBrush(wbrush)
        dc.SetPen(wpen)

        dc.ResetBoundingBox()
        dc.BeginDrawing()
        height = self.canvas.figure.bbox.height
        y1 = height - y1
        y0 = height - y0

        if y1<y0: y0, y1 = y1, y0
        if x1<y0: x0, x1 = x1, x0

        w = x1 - x0
        h = y1 - y0

        rect = int(x0), int(y0), int(w), int(h)
        try: lastrect = self.lastrect
        except AttributeError: pass
        else: dc.DrawRectangle(*lastrect)  #erase last
        self.lastrect = rect
        dc.DrawRectangle(*rect)
        dc.EndDrawing()

    @checkLock
    def press_pan(self, event):
        'the press mouse button in pan/zoom mode callback'

        if event.button == 1:
            self._button_pressed=1
        elif  event.button == 3:
            self._button_pressed=3
        else:
            self._button_pressed=None
            return

        x, y = event.x, event.y

        self._xypress=[]
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if x is not None and y is not None and a.in_axes(event) and a.get_navigate():
                a.start_pan(x, y, event.button)
                self.autoscale[a] = False
                self._xypress.append((a, i))
                self.canvas.mpl_disconnect(self._idDrag)
                self._idDrag=self.canvas.mpl_connect('motion_notify_event', self.drag_pan)

    @checkLock
    def release_pan(self, event):
        'the release mouse button callback in pan/zoom mode'
        self.canvas.mpl_disconnect(self._idDrag)
        self._idDrag=self.canvas.mpl_connect('motion_notify_event', self.onMouseMove)
        for a, ind in self._xypress:
            a.end_pan()
        if not self._xypress: return
        self._xypress = []
        self._button_pressed=None
        self.draw()

    @checkLock
    def drag_pan(self, event):
        'the drag callback in pan/zoom mode'

        for a, ind in self._xypress:
            #safer to use the recorded button at the press than current button:
            #multiple button can get pressed during motion...
            a.drag_pan(self._button_pressed, event.key, event.x, event.y)
        self.dynamic_update()

    @checkLock
    def dynamic_update(self):
        d = self._idle
        self._idle = False
        if d:
            self.canvas.draw()
            self._idle = True

    @checkLock
    def set_cursor(self, cursor):
        cursor =wx.StockCursor(cursord[cursor])
        self.canvas.SetCursor( cursor )

if __name__ == "__main__":
    x = linspace(0,4*pi,201)
    y = sin(x)
    subplot(2,1,1)
    plot(x,y)
    subplot(2,1,2)
    plot(2*x,3*y)
    fi = FigureInteraction(gcf(),threading.RLock())
    show()