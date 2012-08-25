import PIL
import cStringIO
from PIL import Image
from PIL import ImageDraw, ImageFont
import httplib
import numpy as np
import csv
import os
import re
import sys
import sets
import threading
import time
import traceback
from Host.Common.namedtuple import namedtuple
from FindPlats import FindPlats
from configobj import ConfigObj

DECIMATION_FACTOR = 20
NOT_A_NUMBER = 1e1000/1e1000
EARTH_RADIUS = 6378100

AttrTuple = namedtuple('AttrTuple',['attr','default','conv','sel'])

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
        
    def getMaxDist(self,stabClass,Q,u,dstd,conc,u0=0,a=1,q=2):
        """Get the maximum distance at which a source of rate Q cu ft/hr can
        be located if it is to be found with an instrument capable of measuring
        concentration "conc" above ambient, when the wind speed is u m/s and dstd
        is the standard deviation of the wind direction in radians
        
        Since this would normally diverge at small u, a regularization is applied
        so that the maximum distance is made to vary as u**a for u<u0. The 
        sharpness of the transition at u0 is controlled by 1<q<infinity
        """
        pg = self.classConstants[stabClass.upper()]
        d = pg.scale*((u*conc)/Q)**(-1.0/pg.power)
        if u0>0:
            v = u/u0
            d *= v**a/(v**(a*q)+v**(-float(q)/pg.power))**(1.0/q)
        dn = np.sqrt(3)*dstd
        fac = np.sin(dn)/(dn+1.e-6) if dn<np.pi else 0.0       
        return d*fac**(1.0/pg.power)

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
        
class DrawOnPlatBatch(object):
    def __init__(self, iniFile):
        self.config = ConfigObj(iniFile)
        self.pg = PasquillGiffordApprox()
        self.padX = 50
        self.padY = 200
        
    def run(self):
        varList = {re.compile('MISS_FILE$'):AttrTuple('missFile',None,lambda x:x,False),
                   re.compile('BOUNDARIES_FILE$'):AttrTuple('boundaryFile',None,lambda x:x,False),
                   re.compile('TIF_DIR$'):AttrTuple('tifDir',None,lambda x:x,False),
                   re.compile('REPORT_DIR$'):AttrTuple('outDir',None,lambda x:x,False),
                   re.compile('MIN_AMP$'):AttrTuple('minAmpl',0.1,lambda x:float(x),False),
                   re.compile('PLAT$'):AttrTuple('plat',None,lambda x:x,False),
                   re.compile('MIN_LEAK$'):AttrTuple('minLeak',1.0,lambda x:float(x),False),
                   re.compile('STABILITY_CLASS(_[0-9]+)?$'):AttrTuple('stabClass',{'':'D'},lambda x:x,True),
                   re.compile('SHOW_INDICATORS(_[0-9]+)?$'):AttrTuple('showIndicators',{'':1},lambda x:int(x),True),
                   re.compile('SHOW_MARKERS(_[0-9]+)?$'):AttrTuple('showMarkers',{'':1},lambda x:int(x),True),
                   re.compile('SHOW_LISA(_[0-9]+)?$'):AttrTuple('showLisa',{'':1},lambda x:int(x),True),
                   re.compile('SHOW_FOV(_[0-9]+)?$'):AttrTuple('showFov',{'':1},lambda x:int(x),True),
                   re.compile('DAT(_[0-9]+)?$'):AttrTuple('dat',{},lambda x:x,True),
                   re.compile('FOV(_[0-9]+)?$'):AttrTuple('fov',{'':('FFA00040','FFA000FF')},lambda x:x,True)}
        for secName in self.config:
            for k in varList:
                if varList[k].sel:
                    setattr(self,varList[k].attr+'_dict',varList[k].default.copy())
                else:
                    setattr(self,varList[k].attr,varList[k].default)
            if secName == 'DEFAULTS': continue
            if 'DEFAULTS' in self.config:
                for v in self.config['DEFAULTS']:
                    for k in varList:
                        varName = varList[k].attr
                        result = k.match(v)
                        if result:
                            value = varList[k].conv(self.config['DEFAULTS'][v])
                            if result.groups() and varList[k].sel:
                                if not hasattr(self,varName+'_dict'): setattr(self,varName,{})
                                if result.group(1):
                                    getattr(self,varName+'_dict')[result.group(1)] = value
                                else:
                                    getattr(self,varName+'_dict')[''] = value
                            else:
                                setattr(self,varName,value)
            for v in self.config[secName]:
                for k in varList:
                    varName = varList[k].attr
                    result = k.match(v)
                    if result:
                        value = varList[k].conv(self.config[secName][v])
                        if result.groups() and varList[k].sel:
                            if not hasattr(self,varName+'_dict'): setattr(self,varName,{})
                            if result.group(1):
                                getattr(self,varName+'_dict')[result.group(1)] = value
                            else:
                                getattr(self,varName+'_dict')[''] = value
                        else:
                            setattr(self,varName,value)
                            
            if not os.path.exists(self.outDir):
                os.makedirs(self.outDir)
            self.findPlats = FindPlats(self.boundaryFile)
            self.boundaries = np.load(self.boundaryFile,"rb")
            self._draw()
            
                    
    def keyselect(self,attrList,k):
        for attr in attrList:
            var = getattr(self,attr+'_dict')
            if k in var:
                setattr(self,attr,var[k])
            elif '' in var:
                setattr(self,attr,var[''])
            
    def _draw(self):
        platName = self.plat
        missFile = self.missFile
        padX = self.padX
        padY = self.padY
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
        odraw = ImageDraw.Draw(ov)
        font = ImageFont.truetype("ariblk.ttf",60)
        font1 = ImageFont.truetype("arial.ttf",80)
        bubble = Bubble()
        self.mpp = metersPerPixel(minlng,maxlng,minlat,maxlat,(nx,ny))

        for k in sorted(self.dat_dict.keys()):  # Iterate through keys of DAT
            kIndex = int(k[1:])
            self.keyselect(['dat','stabClass','showIndicators','showMarkers','showLisa','showFov','fov'],k)
            datName = self.dat
            datFile = datName + '.dat'
            peakFile = datName + '.peaks'
            # Draw the path of the vehicle
            path = []
            penDown = False
            LastMeasTuple = namedtuple("LastMeasTuple",["lat","lng","deltaLat","deltaLng"])
            lastMeasured = None
            
            startTime = None
            for d in xReadDatFile(datFile):
                lng = d.GPS_ABS_LONG
                lat = d.GPS_ABS_LAT
                t = d.EPOCH_TIME
                if startTime is None:
                    startTime = time.strftime("%d %b %Y %H:%M",time.localtime(t))
                fit = d.GPS_FIT
                if fit>0:
                    x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                    if (0<=x<nx) and (0<=y<ny) and self.showFov:
                        path.append((padX+x,padY+y))
                        if "WIND_N" in d._fields:
                            windN = d.WIND_N
                            windE = d.WIND_E
                            dstd = (np.pi/180.0)*d.WIND_DIR_SDEV
                            bearing = np.arctan2(windE,windN)
                            speed = np.sqrt(windE*windE + windN*windN)
                            width = self.pg.getMaxDist(self.stabClass,self.minLeak,speed,dstd,self.minAmpl,u0=1.0,a=1,q=2)
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
                                        fill,outline = int(self.fov[0],16),int(self.fov[1],16)
                                        fill = tuple([x&0xFF for x in (fill>>24,fill>>16,fill>>8,fill)])
                                        outline = tuple([x&0xFF for x in (outline>>24,outline>>16,outline>>8,outline)])
                                        tdraw.polygon([(x1-xmin,y1-ymin),(x2-xmin,y2-ymin),(x3-xmin,y3-ymin),(x4-xmin,y4-ymin)],
                                                        fill=fill,outline=outline)
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
                    if "WIND_N" in pk._fields:
                        wind = np.sqrt(windN*windN + windE*windE)
                        radius = 50.0; speedmin = 0.5
                        meanBearing = (180.0/np.pi)*np.arctan2(windE,windN)
                        if not(np.isnan(wind) or np.isnan(meanBearing)):
                            minBearing = meanBearing-min(2*windSdev,180.0)
                            maxBearing = meanBearing+min(2*windSdev,180.0)
                            # If the windspeed is too low, increase uncertainty
                            if wind<speedmin:
                                minBearing = 0.0
                                maxBearing = 360.0
                        else:
                            minBearing = 0
                            maxBearing = 360.0
                        # min(75.0,self.pg.getMaxDist(self.stabClass,self.minLeak,speed,self.minAmpl,u0=1.0,a=1,q=2))
                        # Convert distance in meters to pixels
                        radius = int(radius/self.mpp)
                        if self.showLisa: 
                            odraw.pieslice((padX+x-radius,padY+y-radius,padX+x+radius,padY+y+radius),
                                int(minBearing-90.0),int(maxBearing-90.0),fill=(255,255,0,100),outline=(0,0,0,255))
                            if not self.showIndicators: odraw.text((padX+x,padY+y),"%.1f"%ch4,font=font,fill=(0,0,255,255))
                    if self.showIndicators: q.paste(b,box,mask=b)

            odraw.text((padX,75*kIndex),"Plat %s, Start Time %s, MinAmpl %.3f" % (platName,startTime,self.minAmpl),font=font1,fill=(0,0,0,255))
        q.paste(ov,mask=ov)
        bubble.close()

        cp = open(missFile,"rb")
        reader = csv.reader(cp)
        color = {'P':'9090FF','T':'FF9090','B':'C0C0C0'}
        for i,row in enumerate(reader):
            if i==0: # Headings
                headings = [r.strip() for r in row]
                LNG = headings.index('LONG')
                LAT = headings.index('LAT')
                GRADE = headings.index('GRADE')
                CODE = headings.index('P/T/B')
                ID =  headings.index('Picarro Indication ID')
            elif i>0:
                try:
                    lng = float(row[LNG])
                    lat = float(row[LAT])
                    grade = row[GRADE]
                    code = row[CODE]
                    id = int(row[ID])
                    x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                    if (0<=x<nx) and (0<=y<ny) and (grade not in ['MS']):
                        buff = cStringIO.StringIO(bubble.getMiss(5,100,"%d"%(id,),color[code]))
                        b = Image.open(buff)
                        b = b.convert('RGBA')
                        bx,by = b.size
                        box = (padX+x-bx//2,padY+y-by)
                        if self.showMarkers: q.paste(b,box,mask=b)
                except:
                    print traceback.format_exc()
                    print row
        cp.close()
            
        outputPngFile = os.path.join(self.outDir, platName + "_%s.png" % (self.minAmpl,))
        q.save(outputPngFile,format="PNG")
        print "file:%s\n" % os.path.abspath(outputPngFile)
                
if __name__ == "__main__":
    app = DrawOnPlatBatch(sys.argv[1])
    app.run()