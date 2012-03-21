import PIL
import cStringIO
from PIL import Image
from PIL import ImageDraw, ImageFont
import httplib
import numpy as np
import csv
import os
import sys
import sets
import threading
import traceback
from namedtuple import namedtuple
from FindPlats import FindPlats
from configobj import ConfigObj

DECIMATION_FACTOR = 20
NOT_A_NUMBER = 1e1000/1e1000
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

class GoogleMap(object):
    def __init__(self):
        self.conn = httplib.HTTPConnection("maps.googleapis.com")
    def close(self):
        self.conn.close()
    def getMap(self,latCen,lonCen,zoom,nx,ny,scale=1):
        self.conn.request("GET","/maps/api/staticmap?center=%.6f,%.6f&zoom=%d&maptype=satellite&size=%dx%d&scale=%d&sensor=false" % 
                          (latCen,lonCen,zoom,nx,ny,scale))
        r1 = self.conn.getresponse()
        if r1.status != 200:
            raise RuntimeError("%d %s" % (r1.status,r1.reason))
        return r1.read()
    
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
    def getMiss(self,size,fontsize,text,color='FF0000'):    
        self.conn.request("GET","/chart?chst=d_map_spin&chld=%s|0|%s|%s|b|%s" % (size,color,fontsize,text))
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
    
class DrawOnMapBatch(object):
    def __init__(self, iniFile):
        self.config = ConfigObj(iniFile)
        self.padX = 50
        self.padY = 200
        
    def run(self):
        self.gMap = GoogleMap()
        varList = {'DAT_FILE':'datFile','OUT_DIR':'outDir','MIN_AMP':'minAmpl',
                   'LAT_CENTER': 'latCen', 'LON_CENTER':'lngCen', 'ZOOM':'zoom',
                   'PNG_FILE': 'pngFile'}
        
        for secName in self.config:
            if secName == 'DEFAULTS': continue
            if 'DEFAULTS' in self.config:
                for v in varList:
                    if v in self.config['DEFAULTS']: 
                        setattr(self,varList[v],self.config['DEFAULTS'][v])
                    else: 
                        setattr(self,varList[v],None)
                for v in varList:
                    if v in self.config[secName]: 
                        setattr(self,varList[v],self.config[secName][v])
            self.minAmpl = float(self.minAmpl)
            self.latCen = float(self.latCen)
            self.lngCen = float(self.lngCen)
            self.zoom = int(self.zoom)
            try:
                datName = os.path.join(self.outDir,self.datFile)
                peakName = datName.replace(".dat", ".peaks")
                self._draw(datName,peakName,self.padX,self.padY)
            except Exception:
                print traceback.format_exc()
            
    def _draw(self, datFile, peakFile, padX, padY):
        mx,my = 640, 640
        scale = 2
        p = Image.open(cStringIO.StringIO(self.gMap.getMap(self.latCen,self.lngCen,self.zoom,mx,my,scale)))
        # 1 pxl = 360/(256*scale*2**zoom) degrees longitude
        # 1 pxl = 360*cos(latitude)/(256*scale*2**zoom) degrees latitude
        dlngpp = 360.0/(256.0*scale*2**(self.zoom))
        dlatpp = dlngpp*np.cos(self.latCen*np.pi/180.0)
        minlng, maxlng = self.lngCen-(mx*scale/2)*dlngpp, self.lngCen+(mx*scale/2)*dlngpp
        minlat, maxlat = self.latCen-(my*scale/2)*dlatpp, self.latCen+(my*scale/2)*dlatpp
        self.imsize = (scale*mx,scale*my)
        nx,ny = p.size
        q = Image.new('RGBA',(nx+2*padX,ny+2*padY),(255,255,255,255))
        q.paste(p,(padX,padY))
        datTimestamp = "-".join(os.path.basename(self.datFile).split("-")[1:3])
        print minlng, maxlng, minlat, maxlat
        # Overlay for path, bubbles, etc.
        ov = Image.new('RGBA',q.size,(0,0,0,0))
        # p = p.resize((nx//8,ny//8),Image.ANTIALIAS)
        odraw = ImageDraw.Draw(ov)
        font = ImageFont.truetype("ariblk.ttf",60)
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
                                    # q.paste(temp,mask,temp)
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
                odraw.line(path,fill=(0,0,255,255),width=2)
                path = []
        if path:        
            odraw.line(path,fill=(0,0,255,255),width=2)
        
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
            size = 1.5*amp**0.25
            fontsize = int(20.0*size);
            buff = cStringIO.StringIO(bubble.getBubble(size,fontsize,"%.1f"%ch4))
            b = Image.open(buff)
            b = b.convert('RGBA')
            bx,by = b.size
            x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
            if (0<=x<nx) and (0<=y<ny) and (amp>self.minAmpl):
                box = (padX+x-bx//2,padY+y-by)
                if "WIND_N" in pk._fields:
                    wind = np.sqrt(windN*windN + windE*windE)
                    meanBearing = (180.0/np.pi)*np.arctan2(windE,windN)
                    if not(np.isnan(wind) or np.isnan(meanBearing)):
                        minBearing = meanBearing-min(2*windSdev,180.0)
                        maxBearing = meanBearing+min(2*windSdev,180.0)
                        radius = min(150,int(30.0*wind))
                        odraw.pieslice((padX+x-radius,padY+y-radius,padX+x+radius,padY+y+radius),int(minBearing-90.0),int(maxBearing-90.0),
                                        fill=(255,255,0,100),outline=(0,0,0,255))
                q.paste(b,box,mask=b)
                #odraw.text((padX+x,padY+y),"%.1f"%ch4,font=font,fill=(0,0,255,255))
        # cp = open(missFile,"rb")
        # reader = csv.reader(cp)
        # color = {'P':'9090FF','T':'90FF90','B':'C0C0C0'}
        # for i,row in enumerate(reader):
            # if i==1: # Headings
                # headings = [r.strip() for r in row]
                # LNG = headings.index('LONG')
                # LAT = headings.index('LAT')
                # GRADE = headings.index('GRADE')
                # CODE = headings.index('P/T/B')
            # elif i>1:
                # try:
                    # lng = float(row[LNG])
                    # lat = float(row[LAT])
                    # grade = row[GRADE]
                    # code = row[CODE]
                    # x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                    # if (0<=x<nx) and (0<=y<ny) and (grade not in ['MS']):
                        # buff = cStringIO.StringIO(bubble.getMiss(5,100,"%d"%(i+1,),color[code]))
                        # b = Image.open(buff)
                        # b = b.convert('RGBA')
                        # bx,by = b.size
                        # print "Marker at", x,y
                        # box = (padX+x-bx//2,padY+y-by)
                        # q.paste(b,box,mask=b)
                # except:
                    # print traceback.format_exc()
                    # print row
        # cp.close()
        
        q.paste(ov,mask=ov)
        bubble.close()
        q.save(os.path.join(self.outDir,self.pngFile),format="PNG")                
        
if __name__ == "__main__":
    app = DrawOnMapBatch(sys.argv[1])
    app.run()