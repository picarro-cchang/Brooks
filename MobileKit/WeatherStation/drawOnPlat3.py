import PIL
import cStringIO
from PIL import Image
from PIL import ImageDraw
import httplib
import numpy as np
import os
import sys
import sets
from Host.Common.namedtuple import namedtuple

NOT_A_NUMBER = 1e1000/1e1000
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
    
if __name__ == "__main__":
    fname = r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison\platBoundaries.npz"
    boundaries = np.load(fname,"rb")

    datFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\20120213a\ZZZ-20120217-011711Z-DataLog_User_Minimal.dat"
    peakFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\20120213a\ZZZ-20120217-011711Z-DataLog_User_Minimal.peaks"
    
    #datFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120214\ZZZ-20120216-211331Z-DataLog_User_Minimal.dat"
    #peakFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120214\ZZZ-20120216-211331Z-DataLog_User_Minimal.peaks"
    
    #platName = "45C13"
    platDir = r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison"
    platName = "45C11"
    
    missFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison\PicarroMissed.txt"
    
    MINAMP = 0.1
    earthRadius = 6378100
    
    padX = 50
    padY = 200
    which = np.flatnonzero(boundaries["names"]==platName)
    if len(which) == 0:
        raise ValueError("Plat %s not found" % which)
    indx = which[0]
    minlng = boundaries["minlng"][indx]
    maxlng = boundaries["maxlng"][indx]
    minlat = boundaries["minlat"][indx]
    maxlat = boundaries["maxlat"][indx]
    print minlng, maxlng, minlat, maxlat

    p = Image.open(os.path.join(platDir, platName+".png"))
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
                    deltaLat = (180.0/np.pi)*width*np.cos(bearing)/earthRadius
                    deltaLng = (180.0/np.pi)*width*np.sin(bearing)/(earthRadius*np.cos(lat*(np.pi/180.0)))
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
    q.save(platName+"_missed_padded.png",format="PNG")