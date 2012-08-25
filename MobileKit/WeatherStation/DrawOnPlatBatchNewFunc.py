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
from Host.Common.namedtuple import namedtuple
from FindPlats import FindPlats
from configobj import ConfigObj

DECIMATION_FACTOR = 20
NOT_A_NUMBER = 1e1000/1e1000
EARTH_RADIUS = 6378100

class PasquillGiffordApprox(object):
    def __init__(self):
        PGTuple = namedtuple("PGTuple",["power","scale"])
        self.classConstants = { 'A':PGTuple(1.92607854134,7.06164265123),
                                'B':PGTuple(1.85109993492,9.23174186112),
                                'C':PGTuple(1.83709437442,14.0085461312),
                                'D':PGTuple(1.79141020506,21.8533325178),
                                'E':PGTuple(1.74832538645,29.2243762172),
                                'F':PGTuple(1.72286808749,46.0503577192)}

    def getConc(self,stabClass,Q,u,x):
        """Get concentration in ppm from a point source of Q cu ft/hr at 
        distance x m downwind when the wind speed is u m/s."""
        pg = self.classConstants[stabClass.upper()]
        return (Q/u)*(x/pg.scale)**(-pg.power)
        
    def getMaxDist(self,stabClass,Q,u,conc,u0=0,a=1,q=2):
        """Get the maximum distance at which a source of rate Q cu ft/hr can
        be located if it is to be found with an instrument capable of measuring
        concentration "conc" above ambient, when the wind speed is u m/s.
        
        Since this would normally diverge at small u, a regularization is applied
        so that the maximum distance is made to vary as u**a for u<u0. The 
        sharpness of the transition at u0 is controlled by 1<q<infinity
        """
        pg = self.classConstants[stabClass.upper()]
        d = pg.scale*((u*conc)/Q)**(-1.0/pg.power)
        if u0>0:
            v = u/u0
            d *= v**a/(v**(a*q)+v**(-float(q)/pg.power))**(1.0/q)
        return d

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

def metersPerPixel(minlng,maxlng,minlat,maxlat,imsize):
    nx,ny = imsize
    deltaLat = (180.0/np.pi)/EARTH_RADIUS
    deltaLng = (180.0/np.pi)/(EARTH_RADIUS*np.cos(0.5*(minlat+maxlat)*(np.pi/180.0)))
    mppx = (maxlng-minlng)/(deltaLng*nx)
    mppy = (maxlat-minlat)/(deltaLat*ny)
    print "Meters per pixel: ", mppx, mppy
    return 0.5*(mppx+mppy)
    
def widthFunc(windspeed,minAmpl,minLeak,stabClass):
    # For v>>v0, we want c*v**b
    v0 = 1
    a = 1       # low velocity power law
    b = -0.5    # high velocity power law
    p = 2       # Power for transition
    Q = minLeak    # cubic ft/hr
    L = 1000*minAmpl # ppb detection limit
    c = 1200*np.sqrt(Q/L)
    x = windspeed/v0
    if x<1e-6: x=1e-6
    return c*(v0**b)*x**(a+b)/((x**a)**p+(x**b)**p)**(1.0/p)
    
class DrawOnPlatBatch(object):
    def __init__(self, iniFile):
        self.config = ConfigObj(iniFile)
        self.pg = PasquillGiffordApprox()
        self.padX = 50
        self.padY = 200
        
    def run(self):
        varList = {'DAT_FILE':'datFile','PEAKS_FILE':'peakFile',
                   'MISS_FILE':'missFile','BOUNDARIES_FILE':'boundaryFile',
                   'TIF_DIR':'tifDir','OUT_DIR':'outDir','MIN_AMP':'minAmpl',
                   'PLATS':'platList','MIN_LEAK':'minLeak',
                   'STABILITY_CLASS':'stabClass','SHOW_BUBBLES':'showBubbles'}
        
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
            self.minLeak = float(self.minLeak)
            self.showBubbles = int(self.showBubbles)
            if isinstance(self.platList,type("")):
                self.platList = [self.platList.strip()]
            self.findPlats = FindPlats(self.boundaryFile)
            self.boundaries = np.load(self.boundaryFile,"rb")
            
            try:
                if not self.platList:
                    platChoices = self.findPlats.search(self.datFile, DECIMATION_FACTOR)
                else:
                    platChoices = self.platList
                
                print "Plats to process: %s\nCreating composite plots\n" % platChoices
                for p in platChoices:
                    self._draw(p, self.datFile, self.peakFile, self.missFile, self.padX, self.padY)
            except Exception:
                print traceback.format_exc()
            
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
        if not os.path.exists(pngFile):
            os.system('convert "%s" "%s"' % ( tifFile, pngFile))
        p = Image.open(pngFile)
        nx,ny = p.size
        print p.size
        q = Image.new('RGBA',(nx+2*padX,ny+2*padY),(255,255,255,255))
        q.paste(p,(padX,padY))
        
        ov = Image.new('RGBA',q.size,(0,0,0,0))
        
        # p = p.resize((nx//8,ny//8),Image.ANTIALIAS)
        odraw = ImageDraw.Draw(ov)
        font = ImageFont.truetype("ariblk.ttf",60)
        # Draw the path of the vehicle
        path = []
        penDown = False
        LastMeasTuple = namedtuple("LastMeasTuple",["lat","lng","deltaLat","deltaLng"])
        lastMeasured = None
        
        self.mpp = metersPerPixel(minlng,maxlng,minlat,maxlat,(nx,ny))
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
                        width = self.pg.getMaxDist(self.stabClass,self.minLeak,speed,self.minAmpl,u0=1.0,a=1,q=2)
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
                                                    fill=(0xFF,0xA0,0x00,0x40),outline=(0xFF,0xA0,0x0,0xFF))
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
            if (0<=x<nx) and (0<=y<ny) and (amp>self.minAmpl):
                box = (padX+x-bx//2,padY+y-by)
                # q.paste(b,box,mask=b)
                if "WIND_N" in pk._fields:
                    wind = np.sqrt(windN*windN + windE*windE)
                    meanBearing = (180.0/np.pi)*np.arctan2(windE,windN)
                    if not(np.isnan(wind) or np.isnan(meanBearing)):
                        minBearing = meanBearing-min(2*windSdev,180.0)
                        maxBearing = meanBearing+min(2*windSdev,180.0)
                        radius = self.pg.getMaxDist(self.stabClass,self.minLeak,speed,self.minAmpl,u0=1.0,a=1,q=2)
                        # Convert distance in meters to pixels
                        radius = int(radius/self.mpp)
                        odraw.pieslice((padX+x-radius,padY+y-radius,padX+x+radius,padY+y+radius),int(minBearing-90.0),int(maxBearing-90.0),
                                        fill=(255,255,0,100),outline=(0,0,0,255))
                odraw.text((padX+x,padY+y),"%.1f"%ch4,font=font,fill=(0,0,255,255))
        cp = open(missFile,"rb")
        reader = csv.reader(cp)
        color = {'P':'9090FF','T':'90FF90','B':'C0C0C0'}
        for i,row in enumerate(reader):
            if i==1: # Headings
                headings = [r.strip() for r in row]
                LNG = headings.index('LONG')
                LAT = headings.index('LAT')
                GRADE = headings.index('GRADE')
                CODE = headings.index('P/T/B')
            elif i>1:
                try:
                    lng = float(row[LNG])
                    lat = float(row[LAT])
                    grade = row[GRADE]
                    code = row[CODE]
                    x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                    if (0<=x<nx) and (0<=y<ny) and (grade not in ['MS']):
                        buff = cStringIO.StringIO(bubble.getMiss(5,100,"%d"%(i+1,),color[code]))
                        b = Image.open(buff)
                        b = b.convert('RGBA')
                        bx,by = b.size
                        print "Marker at", x,y
                        box = (padX+x-bx//2,padY+y-by)
                        if self.showBubbles: q.paste(b,box,mask=b)
                except:
                    print traceback.format_exc()
                    print row
        cp.close()
        
        q.paste(ov,mask=ov)
        # p.show()
        bubble.close()
        outputPngFile = os.path.join(self.outDir, platName + "_" + datTimestamp + "_%s.png" % (self.minAmpl,))
        q.save(outputPngFile,format="PNG")
        print "file:%s\n" % os.path.abspath(outputPngFile)
        
        
if __name__ == "__main__":
    app = DrawOnPlatBatch(sys.argv[1])
    app.run()