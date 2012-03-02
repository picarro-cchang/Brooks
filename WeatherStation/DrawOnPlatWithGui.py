import PIL
import cStringIO
from PIL import Image
from PIL import ImageDraw
import httplib
import numpy as np
import os
import sys
import sets
import wx
import threading
from namedtuple import namedtuple
from FindPlats import FindPlats
from DrawOnPlatFrame import DrawOnPlatFrame

DECIMATION_FACTOR = 20
NOT_A_NUMBER = 1e1000/1e1000
MINAMP = 0.1
EARTH_RADIUS = 6378100
    
def pFloat(x):
    try:
        return float(x)
    except:
        return NOT_A_NUMBER
        
def xReadDatFile(fileName):
    # Read a data file with column headings and yield a list of named tuples with the file contents
    fp = open(fileName,'r')
    headerLine = True
    for l in fp:
        if headerLine:
            colHeadings = l.split()
            DataTuple = namedtuple("Bunch",colHeadings)
            headerLine = False
        else:
            yield DataTuple(*[pFloat(v) for v in l.split()])
    fp.close()

def list2cols(datAsList):
    datAsCols = []
    if datAsList:
        for f in datAsList[0]._fields:
            datAsCols.append(np.asarray([getattr(d,f) for d in datAsList]))
        return datAsList[0]._make(datAsCols)
    
def aReadDatFile(fileName):
    # Read a data file into a collection of numpy arrays
    return list2cols([x for x in xReadDatFile(fileName)])

class Bubble(object):
    def __init__(self):
        self.conn = httplib.HTTPConnection("chart.apis.google.com")
    def close(self):
        self.conn.close()
    def getBubble(self,size,fontsize,text):    
        self.conn.request("GET","/chart?chst=d_map_spin&chld=%s|0|40FFFF|%s|b|%s" % (size,fontsize,text))
        r1 = self.conn.getresponse()
        if r1.status != 200:
            raise RuntimeError("%d %s" % (r1.status,r1.reason))
        return r1.read()
    def getMiss(self,size,fontsize,text):    
        self.conn.request("GET","/chart?chst=d_map_spin&chld=%s|0|FF0000|%s|b|%s" % (size,fontsize,text))
        r1 = self.conn.getresponse()
        if r1.status != 200:
            raise RuntimeError("%d %s" % (r1.status,r1.reason))
        return r1.read()
    def getCallout(self,text):
        self.conn.request("GET","/chart?chst=d_bubble_texts_big&chld=%s|%s|%s|%s" % ("bb","FF0000","000000",text))
        r1 = self.conn.getresponse()
        if r1.status != 200:
            raise RuntimeError("%d %s" % (r1.status,r1.reason))
        return r1.read()
    
    
def xform(lng,lat,minlng,maxlng,minlat,maxlat,imsize):
    """Get pixel in image of size "imsize" corresponding to "lng", "lat"
       where pixel (0,0) is (minlng,minlat) and (imsize[0]-1,imsize[1]-1)
       is (maxlng,maxlat)"""
    nx,ny = imsize
    x = int((nx-1)*(lng-minlng)/(maxlng-minlng))
    y = int((ny-1)*(lat-maxlat)/(minlat-maxlat))
    return x,y

def widthFunc(windspeed):
    v0 = 5
    w0 = 50
    return w0*np.exp(1.0)*(windspeed/v0)*np.exp(-windspeed/v0)
    
class DrawOnPlatWithGui(DrawOnPlatFrame):
    def __init__(self, *args, **kwds):
        self.boundaryFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison\platBoundaries.npz"
        self.findPlats = FindPlats(self.boundaryFile)
        self.boundaries = np.load(self.boundaryFile,"rb")
        self.datFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\20120213a\ZZZ-20120217-011711Z-DataLog_User_Minimal.dat"
        self.peakFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\20120213a\ZZZ-20120217-011711Z-DataLog_User_Minimal.peaks"
        self.missFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison\PicarroMissed.txt"
        self.defaultDatPath = os.path.dirname(self.datFile)
        self.defaultPeakPath = os.path.dirname(self.peakFile)
        self.defaultBoundaryPath = os.path.dirname(self.boundaryFile)
        self.defaultMissPath = os.path.dirname(self.missFile)
        self.tifDir = r"S:\Projects\Natural Gas Detection + P3\Files from PGE including TIFF maps\GEMS\CompTif\Gas\Distribution"
        self.outDir = os.getcwd()
        self.padX = 50
        self.padY = 200
        defaults = (self.datFile, self.peakFile, self.boundaryFile, self.missFile, self.tifDir, self.outDir) 
        DrawOnPlatFrame.__init__(self, defaults, *args, **kwds)
        self.bindEvents()
    
    def bindEvents(self):
        self.Bind(wx.EVT_BUTTON, self.onDatButton, self.buttonList[0])              
        self.Bind(wx.EVT_BUTTON, self.onPeakButton, self.buttonList[1])
        self.Bind(wx.EVT_BUTTON, self.onBoundaryButton, self.buttonList[2])              
        self.Bind(wx.EVT_BUTTON, self.onMissButton, self.buttonList[3])
        self.Bind(wx.EVT_BUTTON, self.onTifDirButton, self.buttonList[4])              
        self.Bind(wx.EVT_BUTTON, self.onOutDirButton, self.buttonList[5])  
        self.Bind(wx.EVT_BUTTON, self.onProcButton, self.procButton)  
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrl, self.textCtrlMsg) 

    def onOverUrl(self, event):
        if event.MouseEvent.LeftDown():
            urlString = self.textCtrlMsg.GetRange(event.GetURLStart()+5, event.GetURLEnd())
            print urlString
            wx.LaunchDefaultBrowser(urlString)
        else:
            event.Skip()

    def onDatButton(self, event):
        if not self.defaultDatPath:
            self.defaultDatPath = os.getcwd()
        dlg = wx.FileDialog(self, "Select DAT file...",
                            self.defaultDatPath, wildcard = "*.dat", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.datFile = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.defaultDatPath = dlg.GetDirectory()
        self.textCtrlButton[0].SetValue(self.datFile)
        
    def onPeakButton(self, event):
        if not self.defaultPeakPath:
            self.defaultPeakPath = os.getcwd()
        dlg = wx.FileDialog(self, "Select PEAKS file...",
                            self.defaultPeakPath, wildcard = "*.peaks", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.peakFile = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.defaultPeakPath = dlg.GetDirectory()
        self.textCtrlButton[1].SetValue(self.peakFile)
        
    def onBoundaryButton(self, event):
        if not self.defaultBoundaryPath:
            self.defaultBoundaryPath = os.getcwd()
        dlg = wx.FileDialog(self, "Select PLAT BOUNDARIES file...",
                            self.defaultBoundaryPath, wildcard = "*.npz", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.boundaryFile = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.defaultBoundaryPath = dlg.GetDirectory()
        # Re-process the boundaries
        self.findPlats = FindPlats(self.boundaryFile)
        self.boundaries = np.load(self.boundaryFile,"rb")
        self.textCtrlButton[2].SetValue(self.boundaryFile)

    def onMissButton(self, event):
        if not self.defaultMissPath:
            self.defaultMissPath = os.getcwd()
        dlg = wx.FileDialog(self, "Select MISSED LEAKS file...",
                            self.defaultMissPath, wildcard = "*.txt", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.missFile = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.defaultMissPath = dlg.GetDirectory()
        self.textCtrlButton[3].SetValue(self.missFile)
        
    def onTifDirButton(self, event):
        d = wx.DirDialog(None,"Specify the directory that contains TIF files", style=wx.DD_DEFAULT_STYLE,
                         defaultPath=self.tifDir)
        if d.ShowModal() == wx.ID_OK:
            self.tifDir = d.GetPath().replace("\\", "/")
        self.textCtrlButton[4].SetValue(self.tifDir)
            
    def onOutDirButton(self, event):
        d = wx.DirDialog(None,"Specify the output directory that contains the output PNG files", style=wx.DD_DEFAULT_STYLE,
                         defaultPath=self.outDir)
        if d.ShowModal() == wx.ID_OK:
            self.outDir = d.GetPath().replace("\\", "/")
        self.textCtrlButton[5].SetValue(self.outDir)
        
    def onProcButton(self, event):
        self.textCtrlMsg.Clear()
        self.textCtrlMsg.WriteText("Search for plats...\n")
        procThread = threading.Thread(target = self.draw)
        procThread.setDaemon(True)
        procThread.start()

    def enableAll(self, onFlag):
        for i in range(len(self.buttonList)):
            self.buttonList[i].Enable(onFlag)
        self.procButton.Enable(onFlag)
        
    def draw(self):
        self.enableAll(False)
        try:
            platChoices = self.findPlats.search(self.datFile, DECIMATION_FACTOR)
            self.textCtrlMsg.WriteText("Covered plats found: %s\nCreating composite plots\n" % platChoices)
            for p in platChoices:
                self._draw(p, self.datFile, self.peakFile, self.missFile, self.padX, self.padY)
        except Exception:
            self.textCtrlMsg.WriteText(traceback.format_exc())
        finally:
            self.enableAll(True)
            
    def _draw(self, platName, datFile, peakFile, missFile, padX, padY):
        datTimestamp = "-".join(os.path.basename(self.datFile).split("-")[1:3])
        which = np.flatnonzero(self.boundaries["names"]==platName)
        if len(which) == 0:
            raise ValueError("Plat %s not found" % which)
        indx = which[0]
        minlng = self.boundaries["minlng"][indx]
        maxlng = self.boundaries["maxlng"][indx]
        minlat = self.boundaries["minlat"][indx]
        maxlat = self.boundaries["maxlat"][indx]
        print minlng, maxlng, minlat, maxlat

        tifFile = os.path.join(self.tifDir, platName+".tif")
        pngFile = os.path.join(self.outDir, platName+".png")
        os.system('convert "%s" "%s"' % ( tifFile, pngFile))
        p = Image.open(pngFile)
        nx,ny = p.size
        print p.size
        q = Image.new('RGBA',(nx+2*padX,ny+2*padY),(255,255,255,255))
        q.paste(p,(padX,padY))
        
        ov = Image.new('RGBA',q.size,(0,0,0,0))
        
        # p = p.resize((nx//8,ny//8),Image.ANTIALIAS)
        odraw = ImageDraw.Draw(ov)
        # Draw the path of the vehicle
        path = []
        penDown = False
        LastMeasTuple = namedtuple("LastMeasTuple",["lat","lng","deltaLat","deltaLng"])
        lastMeasured = None
        
        for d in xReadDatFile(datFile):
            lng = d.GPS_ABS_LONG
            lat = d.GPS_ABS_LAT
            fit = d.GPS_FIT
            if fit>0:
                x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                if (0<=x<nx) and (0<=y<ny):
                    path.append((padX+x,padY+y))
                    if "WIND_N" in d._fields:
                        windN = d.WIND_N
                        windE = d.WIND_E
                        bearing = np.arctan2(windE,windN)
                        speed = np.sqrt(windE*windE + windN*windN)
                        width = widthFunc(speed)
                        deltaLat = (180.0/np.pi)*width*np.cos(bearing)/EARTH_RADIUS
                        deltaLng = (180.0/np.pi)*width*np.sin(bearing)/(EARTH_RADIUS*np.cos(lat*(np.pi/180.0)))
                        if not (np.isnan(deltaLat) or np.isnan(deltaLng)):
                            if lastMeasured is not None:
                                if penDown:
                                    x1,y1 = xform(lastMeasured.lng+lastMeasured.deltaLng,lastMeasured.lat+lastMeasured.deltaLat,minlng,maxlng,minlat,maxlat,(nx,ny))
                                    x2,y2 = xform(lastMeasured.lng,lastMeasured.lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                                    x3,y3 = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                                    x4,y4 = xform(lng+deltaLng,lat+deltaLat,minlng,maxlng,minlat,maxlat,(nx,ny))
                                    xmin = min(x1,x2,x3,x4)
                                    xmax = max(x1,x2,x3,x4)
                                    ymin = min(y1,y2,y3,y4)
                                    ymax = max(y1,y2,y3,y4)
                                    temp = Image.new('RGBA',(xmax-xmin+1,ymax-ymin+1),(0,0,0,0))
                                    tdraw = ImageDraw.Draw(temp)
                                    tdraw.polygon([(x1-xmin,y1-ymin),(x2-xmin,y2-ymin),(x3-xmin,y3-ymin),(x4-xmin,y4-ymin)],
                                                    fill=(0,0,0xCC,0x40),outline=(0,0,0xCC,0xFF))
                                    mask = (padX+xmin,padY+ymin)
                                    q.paste(temp,mask,temp)
                            lastMeasured = LastMeasTuple(lat,lng,deltaLat,deltaLng)
                        else:
                            lastMeasured = None
                    penDown = True
                else:
                    penDown = False
                    lastMeasured = None
            else:
                penDown = False
                lastMeasured = None
            if (penDown == False) and path:
                odraw.line(path,fill=(0,0,255,255),width=4)
                path = []
        if path:        
            odraw.line(path,fill=(0,0,255,255),width=4)
        
        # Draw the peak bubbles and wind wedges
        bubble = Bubble()
        
        for pk in xReadDatFile(peakFile):
            lng = pk.GPS_ABS_LONG
            lat = pk.GPS_ABS_LAT
            amp = pk.AMPLITUDE
            ch4 = pk.CH4
            if "WIND_N" in pk._fields:
                windN = pk.WIND_N
                windE = pk.WIND_E
                windSdev = pk.WIND_DIR_SDEV
            size = 5*amp**0.25
            fontsize = int(20.0*size);
            buff = cStringIO.StringIO(bubble.getBubble(size,fontsize,"%.1f"%ch4))
            b = Image.open(buff)
            b = b.convert('RGBA')
            bx,by = b.size
            x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
            if (0<=x<nx) and (0<=y<ny) and (amp>MINAMP):
                box = (padX+x-bx//2,padY+y-by)
                q.paste(b,box,mask=b)
                if "WIND_N" in pk._fields:
                    wind = np.sqrt(windN*windN + windE*windE)
                    meanBearing = (180.0/np.pi)*np.arctan2(windE,windN)
                    if not(np.isnan(wind) or np.isnan(meanBearing)):
                        minBearing = meanBearing-min(2*windSdev,180.0)
                        maxBearing = meanBearing+min(2*windSdev,180.0)
                        radius = min(500.0,int(100.0*wind))
                        odraw.pieslice((padX+x-radius,padY+y-radius,padX+x+radius,padY+y+radius),int(minBearing-90.0),int(maxBearing-90.0),
                                        fill=(255,255,0,200),outline=(0,0,0,255))
        for i,miss in enumerate(xReadDatFile(missFile)):
            lng = miss.GPS_ABS_LONG
            lat = miss.GPS_ABS_LAT
            buff = cStringIO.StringIO(bubble.getMiss(5,100,"%d"%(i+1,)))
            #buff = cStringIO.StringIO(bubble.getMiss(2,40,"%d"%(i+1,)))
            b = Image.open(buff)
            b = b.convert('RGBA')
            bx,by = b.size
            x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
            if (0<=x<nx) and (0<=y<ny):
                print "Miss at", x,y
                box = (padX+x-bx//2,padY+y-by)
                q.paste(b,box,mask=b)
        
        q.paste(ov,mask=ov)
        # p.show()
        bubble.close()
        outputPngFile = os.path.join(self.outDir, platName + "_" + datTimestamp + "_missed_padded.png")
        print outputPngFile
        q.save(outputPngFile,format="PNG")
        self.textCtrlMsg.WriteText("file:%s\n" % os.path.abspath(outputPngFile))
        
        #Remove the originally converted PNG file
        os.remove(pngFile)
        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = DrawOnPlatWithGui(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()