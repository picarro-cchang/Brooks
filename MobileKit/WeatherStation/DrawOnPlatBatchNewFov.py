import PIL
import cStringIO
from PIL import Image
from PIL import ImageDraw, ImageFont
from collections import deque
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
import findFovWidth as fw

DECIMATION_FACTOR = 20
NOT_A_NUMBER = 1e1000/1e1000
EARTH_RADIUS = 6378100
DTR = np.pi/180.0
RTD = 180.0/np.pi

AttrTuple = namedtuple('AttrTuple',['attr','default','conv','sel'])

class PasquillGiffordApprox(object):
    def __init__(self):
        # Semi opening angle of a cone representing turbulence induced
        #  atmospheric dispersion for rural conditions
        PGTuple = namedtuple("PGTuple",["theta_y","theta_z"])
        self.classConstants = {'A':PGTuple(0.2685,0.1395),
                               'B':PGTuple(0.1927,0.1060),
                               'C':PGTuple(0.1246,0.0744),
                               'D':PGTuple(0.0820,0.0465),
                               'E':PGTuple(0.0612,0.0353),
                               'F':PGTuple(0.0407,0.0233)}

    def getConc(self,stabClass,Q,u,dstd,x,umin=0):
        """Get concentration in ppm from a point source of Q cu ft/hr at 
        distance x m downwind when the wind speed is u m/s and dstd is the
        standard deviation of the wind direction in radians.
        Since this would normally diverge at small u, a regularization is applied
        so that u is replaced by max(u,umin)
        """
        pg = self.classConstants[stabClass.upper()]
        theta_y = np.sqrt((dstd/2)**2 + pg.theta_y**2)
        u = max(u,umin)
        return 7.866*Q/(np.pi*u*theta_y*pg.theta_z*x**2)
        
    def getMaxDist(self,stabClass,Q,u,dstd,conc,umin=0):
        """Get the maximum distance at which a source of rate Q cu ft/hr can
        be located if it is to be found with an instrument capable of measuring
        concentration "conc" above ambient, when the wind speed is u m/s and dstd
        is the standard deviation of the wind direction in radians
        
        Since this would normally diverge at small u, a regularization is applied
        so that u is replaced by max(u,umin)
        """
        pg = self.classConstants[stabClass.upper()]
        theta_y = np.sqrt((dstd/2)**2 + pg.theta_y**2)
        u = max(u,umin)
        return np.sqrt(7.866*Q/(conc*np.pi*u*theta_y*pg.theta_z))

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
    def getBubble(self,size,fontsize,text,color="40FFFF"):    
        self.conn.request("GET","/chart?chst=d_map_spin&chld=%s|0|%s|%s|b|%s" % (size,color,fontsize,text))
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
    deltaLat = RTD/EARTH_RADIUS
    deltaLng = RTD/(EARTH_RADIUS*np.cos(0.5*(minlat+maxlat)*DTR))
    mppx = (maxlng-minlng)/(deltaLng*nx)
    mppy = (maxlat-minlat)/(deltaLat*ny)
    print "Meters per pixel: ", mppx, mppy
    return 0.5*(mppx+mppy)

def astd(wind,vcar):
    a = 0.15*np.pi
    b = 0.25
    c = 0.0
    return min(np.pi,a*(b+c*vcar)/(wind+0.01))
    
class DrawOnPlatBatch(object):
    def __init__(self, iniFile):
        self.config = ConfigObj(iniFile)
        self.pg = PasquillGiffordApprox()
        self.padX = 200
        self.padY = 200

    def run(self):
        varList = {re.compile('MISS_FILE$'):AttrTuple('missFile',None,lambda x:x,False),
                   re.compile('RANK_FILE$'):AttrTuple('rankFile',None,lambda x:x,False),
                   re.compile('BOUNDARIES_FILE$'):AttrTuple('boundaryFile',None,lambda x:x,False),
                   re.compile('TIF_DIR$'):AttrTuple('tifDir',None,lambda x:x,False),
                   re.compile('REPORT_DIR$'):AttrTuple('outDir',None,lambda x:x,False),
                   re.compile('PLAT$'):AttrTuple('plat',None,lambda x:x,False),
                   re.compile('MIN_LEAK$'):AttrTuple('minLeak',1.0,lambda x:float(x),False),
                   re.compile('STABILITY_CLASS(_[0-9]+)?$'):AttrTuple('stabClass',{'':'D'},lambda x:x,True),
                   re.compile('SHOW_INDICATORS(_[0-9]+)?$'):AttrTuple('showIndicators',{'':1},lambda x:int(x),True),
                   re.compile('SHOW_MARKERS(_[0-9]+)?$'):AttrTuple('showMarkers',{'':1},lambda x:int(x),True),
                   re.compile('SHOW_LISA(_[0-9]+)?$'):AttrTuple('showLisa',{'':1},lambda x:int(x),True),
                   re.compile('SHOW_FOV(_[0-9]+)?$'):AttrTuple('showFov',{'':1},lambda x:int(x),True),
                   re.compile('DAT(_[0-9]+)?$'):AttrTuple('dat',{},lambda x:x,True),
                   re.compile('PEAKS(_[0-9]+)?$'):AttrTuple('peaks',{'':''},lambda x:x,True),
                   re.compile('FOV(_[0-9]+)?$'):AttrTuple('fov',{'':('FFA00040','FFA000FF')},lambda x:x,True),
                   re.compile('MIN_AMP(_[0-9]+)?$'):AttrTuple('minAmpl',{'':0.1},lambda x:float(x),True),
                   re.compile('MAX_AMP(_[0-9]+)?$'):AttrTuple('maxAmpl',{'':None},lambda x:float(x),True),
                   re.compile('RUN_BUBBLE_COLOR(_[0-9]+)?$'):AttrTuple('runBubbleColor',{'':"40FFFF"},lambda x:x,True)}
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
        
        qdraw = ImageDraw.Draw(q)
        ov = Image.new('RGBA',q.size,(0,0,0,0))
        odraw = ImageDraw.Draw(ov)
        font = ImageFont.truetype("ariblk.ttf",60)
        font1 = ImageFont.truetype("arial.ttf",80)

        bubble = Bubble()
        self.mpp = metersPerPixel(minlng,maxlng,minlat,maxlat,(nx,ny))
        
        for k in sorted(self.dat_dict.keys()):  # Iterate through keys of DAT
            kIndex = int(k[1:])
            self.keyselect(['dat','peaks','stabClass','showIndicators','showMarkers','showLisa','showFov','fov','minAmpl','maxAmpl','runBubbleColor'],k)
            datName = self.dat
            datFile = datName + '.dat'
            if not self.peaks:
                peakFile = datName + '.peaks'
            else:
                peakFile = self.peaks

            # Draw the peak bubbles and wind wedges
            pList = [(dat.AMPLITUDE,dat) for dat in xReadDatFile(peakFile)]
            for amp,pk in sorted(pList):
                if amp<self.minAmpl: continue
                if (self.maxAmpl is not None) and amp>self.maxAmpl: break
                lng = pk.GPS_ABS_LONG
                lat = pk.GPS_ABS_LAT
                ch4 = pk.CH4
                vcar = pk.CAR_SPEED if "CAR_SPEED" in pk._fields else 0.0
                if "WIND_N" in pk._fields:
                    windN = pk.WIND_N
                    windE = pk.WIND_E
                    dstd = DTR*pk.WIND_DIR_SDEV
                size = 5*amp**0.25
                fontsize = int(20.0*size);
                color = "40FFFF"
                if ("RUN" in pk._fields) and (int(pk.RUN) != kIndex): continue
                buff = cStringIO.StringIO(bubble.getBubble(size,fontsize,"%.1f"%ch4,self.runBubbleColor))
                b = Image.open(buff)
                b = b.convert('RGBA')
                bx,by = b.size
                x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                if (-padX<=x<nx+padX) and (-padY<=y<ny+padY) and (amp>self.minAmpl) and ((self.maxAmpl is None) or (amp<=self.maxAmpl)):
                    box = (padX+x-bx//2,padY+y-by)
                    if "WIND_N" in pk._fields:
                        wind = np.sqrt(windN*windN + windE*windE)
                        radius = 50.0; speedmin = 0.5
                        meanBearing = RTD*np.arctan2(windE,windN)
                        dstd = np.sqrt(dstd**2 + astd(wind,vcar)**2)
                        windSdev = RTD*dstd
                        if not(np.isnan(wind) or np.isnan(meanBearing)):
                            minBearing = meanBearing-min(2*windSdev,180.0)
                            maxBearing = meanBearing+min(2*windSdev,180.0)
                            # If the windspeed is too low, increase uncertainty
                            #if wind<speedmin:
                            #    minBearing = 0.0
                            #    maxBearing = 360.0
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
                    if self.showIndicators: ov.paste(b,box,mask=b)
                
            # Draw the path of the vehicle
            path = []
            penDown = False
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
                    if (-padX<=x<nx+padX) and (-padY<=y<ny+padY):
                        path.append((padX+x,padY+y))
                        penDown = True
                    else:
                        penDown = False
                else:
                    penDown = False
                    lastMeasured = None
                if (penDown == False) and path:
                    odraw.line(path,fill=(0,0,255,255),width=4)
                    path = []
            if path:        
                odraw.line(path,fill=(0,0,255,255),width=4)
            
            # Draw the field of view

            if self.showFov and "WIND_N" in d._fields:
                penDown = False
                LastMeasTuple = namedtuple("LastMeasTuple",["lat","lng","deltaLat","deltaLng"])
                lastMeasured = None
                fovBuff = deque()
                N = 10              # Use 2*N+1 samples for calculating FOV
                for newdat in xReadDatFile(datFile):
                    while len(fovBuff) >= 2*N+1: fovBuff.popleft()
                    fovBuff.append(newdat)
                    if len(fovBuff) == 2*N+1:
                        d = fovBuff[N]
                        lng = d.GPS_ABS_LONG
                        lat = d.GPS_ABS_LAT
                        cosLat = np.cos(lat*DTR)
                        t = d.EPOCH_TIME
                        fit = d.GPS_FIT
                        windN = d.WIND_N
                        windE = d.WIND_E
                        dstd = DTR*d.WIND_DIR_SDEV
                        if fit>0:
                            x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                            if (-padX<=x<nx+padX) and (-padY<=y<ny+padY):
                                bearing = np.arctan2(windE,windN)
                                wind = np.sqrt(windE*windE + windN*windN)
                                dmax = self.pg.getMaxDist(self.stabClass,self.minLeak,wind,0.0,self.minAmpl,umin=0.5)
                                xx = np.asarray([fovBuff[i].GPS_ABS_LONG for i in range(2*N+1)])
                                yy = np.asarray([fovBuff[i].GPS_ABS_LAT for i in range(2*N+1)])
                                xx = DTR*(xx-lng)*EARTH_RADIUS*cosLat
                                yy = DTR*(yy-lat)*EARTH_RADIUS
                                dt = fovBuff[N+1].EPOCH_TIME - fovBuff[N-1].EPOCH_TIME
                                vcar = np.sqrt((xx[N+1]-xx[N-1])**2 + (yy[N+1]-yy[N-1])**2)/dt
                                dstd = np.sqrt(dstd**2 + astd(wind,vcar)**2)
                                width = fw.maxDist(xx,yy,N,windE,windN,dstd,dmax,thresh=0.7,tol=1.0)
                                deltaLat = RTD*width*np.cos(bearing)/EARTH_RADIUS
                                deltaLng = RTD*width*np.sin(bearing)/(EARTH_RADIUS*cosLat)
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
            
            # Write the heading on the page
            
            if self.maxAmpl is None:
                odraw.text((padX,75*kIndex),"Plat %s, Start Time %s, PG class %s, MinAmpl %.3f" % (platName,startTime,self.stabClass,self.minAmpl),font=font1,fill=(0,0,0,255))
            else:
                odraw.text((padX,75*kIndex),"Plat %s, Start Time %s, PG class %s, MinAmpl %.3f, MaxAmpl %.3f" % (platName,startTime,self.stabClass,self.minAmpl,self.maxAmpl),font=font1,fill=(0,0,0,255))
                
        q.paste(ov,mask=ov)
        bubble.close()

        if self.missFile:
            cp = open(self.missFile,"rb")
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
                        if (-padX<=x<nx+padX) and (-padY<=y<ny+padY) and (grade not in ['MS']):
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

        if self.rankFile:
            rList = [(r+1,dat) for r,dat in enumerate(xReadDatFile(self.rankFile))]
            for id,dat in reversed(rList):
                lng = dat.GPS_ABS_LONG
                lat = dat.GPS_ABS_LAT
                x,y = xform(lng,lat,minlng,maxlng,minlat,maxlat,(nx,ny))
                if (-padX<=x<nx+padX) and (-padY<=y<ny+padY):
                    buff = cStringIO.StringIO(bubble.getMiss(5,100,"%d" % id,"90FF90"))
                    b = Image.open(buff)
                    b = b.convert('RGBA')
                    bx,by = b.size
                    box = (padX+x-bx//2,padY+y-by)
                q.paste(b,box,mask=b)
        
        if self.maxAmpl is None:
            outputPngFile = os.path.join(self.outDir, platName + "_%s.png" % (self.minAmpl,))
        else:    
            outputPngFile = os.path.join(self.outDir, platName + "_%s_%s.png" % (self.minAmpl,self.maxAmpl,))
        q.save(outputPngFile,format="PNG")
        print "file:%s\n" % os.path.abspath(outputPngFile)
                
if __name__ == "__main__":
    app = DrawOnPlatBatch(sys.argv[1])
    app.run()