# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

try:
    from collections import namedtuple
except:
    from Host.Common.namedtuple import namedtuple
import cStringIO
import math
import socket
import traceback
import urllib
import urllib2
import Image
import ImageDraw
import ImageFont
import subprocess
 
RTD = 180.0/math.pi
DTR = math.pi/180.0
EARTH_RADIUS = 6378100
NOT_A_NUMBER = 1e1000/1e1000

APIKEY = "AIzaSyDuKrJI6smrNA1MOuriEmlW9XFZikNahhs"
MapParams = namedtuple("MapParams",["minLng","minLat","maxLng","maxLat","nx","ny","padX","padY"])
MapRect = namedtuple("MapRect",["swCorner","neCorner"])
LatLng  = namedtuple("LatLng", ["lat","lng"])
WKHTMLTOPDF = r"C:\Program Files (x86)\wkhtmltopdf\wkhtmltopdf.exe"

def asPNG(image):
    output = cStringIO.StringIO()
    image.save(output,format="PNG")                
    try:
        return output.getvalue()
    finally:
        output.close()

class GoogleMap(object):
    def getMap(self,latCen,lonCen,zoom,nx,ny,scale=1,satellite=True):
        url = 'http://maps.googleapis.com/maps/api/staticmap'
        params = dict(center="%.6f,%.6f"%(latCen,lonCen),zoom="%d"%zoom,size="%dx%d" % (nx,ny),scale="%d"%scale,sensor="false")
        if satellite: params["maptype"] = "satellite"
        if APIKEY is not None: params["key"] = APIKEY
        paramStr = urllib.urlencode(params)
        get_url = url+("?%s" % paramStr)
        print get_url
        timeout = 5.0
        try:
            socket.setdefaulttimeout(timeout)
            resp = urllib2.urlopen(get_url)
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
            raise
        except:
            print traceback.format_exc()
            raise
        else:
            return resp.read()
            
    def getPlatParams(self,minLng,maxLng,minLat,maxLat,satellite=True,padX=50,padY=50):
        return self.getPlat(minLng,maxLng,minLat,maxLat,satellite,padX,padY,fetchPlat=False)
    
    def getPlat(self,minLng,maxLng,minLat,maxLat,satellite=True,padX=50,padY=50,fetchPlat=True):
        meanLat = 0.5*(minLat + maxLat)
        meanLng = 0.5*(minLng + maxLng)
        Xp = maxLng-minLng
        Yp = maxLat-minLat
        # Find the largest zoom consistent with these limits
        cosLat = math.cos(meanLat*DTR)
        zoom = int(math.floor(math.log(min((360.0*640)/(256*Xp),(360.0*640*cosLat)/(256*Yp)))/math.log(2.0)))
        # Find the number of pixels in each direction
        fac = (256.0/360.0)*2**zoom
        mx = int(math.ceil(fac*Xp))
        my = int(math.ceil(fac*Yp/cosLat))
        scale = 2
        mp = MapParams(minLng,minLat,maxLng,maxLat,mx*scale,my*scale,padX,padY)
        if fetchPlat:
            p = Image.open(cStringIO.StringIO(self.getMap(meanLat,meanLng,zoom,mx,my,scale,satellite)))
            q = Image.new('RGBA',(scale*mx+2*padX,scale*my+2*padY),(255,255,255,255))
            q.paste(p,(padX,padY))
            return q, mp
        else:
            return mp

def partition(mapRect,ny,nx):
    swCorner = mapRect.swCorner
    neCorner = mapRect.neCorner
    dx = float(neCorner.lng - swCorner.lng)/nx
    dy = float(neCorner.lat - swCorner.lat)/ny
    maxLat = neCorner.lat
    rectList = []
    for my in range(ny):
        minLat = maxLat - dy
        minLng = swCorner.lng
        rowList = []
        for mx in range(nx):
            maxLng = minLng + dx
            rowList.append(MapRect(LatLng(minLat,minLng),LatLng(maxLat,maxLng)))
            minLng = maxLng
        rectList.append(rowList)
        maxLat = minLat
    return rectList

class PartitionedMap(object):
    def __init__(self,minLng,minLat,maxLng,maxLat,nx,ny,padX,padY):
        # The map is in the middle, of size nx by ny. It is padded by padX on left and right, and by
        #  padY on top and bottom. This makes the padded image have size nx+2*padX, ny+2*padY
        self.minLng = minLng
        self.minLat = minLat
        self.maxLng = maxLng
        self.maxLat = maxLat
        self.nx = nx
        self.ny = ny
        self.padX = padX
        self.padY = padY
       
    def xform(self,lng,lat):
        """Get pixel corresponding to (lng,lat), where pixel (0,0) is
           (minLng,maxLat) and (nx,ny) is (maxLng,minLat)"""
        x = int(self.nx*(lng-self.minLng)/(self.maxLng-self.minLng))
        y = int(self.ny*(lat-self.maxLat)/(self.minLat-self.maxLat))
        return x,y

    def drawPartition(self,map,rectList):
        assert(map.size == (self.nx+2*self.padX,self.ny+2*self.padY))
        font = ImageFont.truetype(r"c:\windows\fonts\arial.ttf",40)
        mDraw = ImageDraw.Draw(map)
        for ky,row in enumerate(rectList):
            for kx,mr in enumerate(row):
                x1, y1 = self.xform(mr.swCorner.lng,mr.swCorner.lat)
                x2, y2 = self.xform(mr.neCorner.lng,mr.neCorner.lat)
                mDraw.rectangle(((self.padX+x1,self.padY+y1),(self.padX+x2,self.padY+y2)),outline=(0,0,0,255))
                xc, yc = (x1+x2)/2,(y1+y2)/2
                label = chr(ord('A')+ky) + "%d" % (kx+1,)
                w,h = mDraw.textsize(label,font=font)
                mDraw.text((self.padX+xc-w/2,self.padY+yc-h/2),label,font=font,fill=(0,0,255,255))

        return map
    
#lat = 37.389391
#lng = -121.987088
#zoom = 14
#g = GoogleMap().getMap(lat,lng,zoom,640,480)
#p = Image.open(cStringIO.StringIO(g))
#op = file("test1.png","wb")
#op.write(asPNG(p))
#op.close()
'''
minLat, minLng = 37.397437,-122.006278
maxLat, maxLng = 37.41046,-121.995463
q, mp = GoogleMap().getPlat(minLng,maxLng,minLat,maxLat,satellite=False,padX=50,padY=50,fetchPlat=True)
op = file("test2.png","wb")
op.write(asPNG(q))
op.close()
mapRect = MapRect(LatLng(mp.minLat,mp.minLng),LatLng(mp.maxLat,mp.maxLng))
rectList = partition(mapRect,3,2)
print rectList
pm = PartitionedMap(mp.minLng,mp.minLat,mp.maxLng,mp.maxLat,mp.nx,mp.ny,mp.padX,mp.padY)
q1 = pm.drawPartition(q,partition(mapRect,3,2))
op = file("test3.png","wb")
op.write(asPNG(q1))
op.close()
pdfFname = "output1.pdf"
pic = '<img id="image" src="%s" alt="" width="95%%"></img>' % "file:///c:/FetchGoogleMaps/test3.png"
s = "<h1>Key Map</h1>" + pic
proc = subprocess.Popen([WKHTMLTOPDF,"-",pdfFname],
                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
stdout = proc.communicate(s)
print stdout
'''