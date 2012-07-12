
try:
    import simplejson as json
except:
    import json
import datetime
import httplib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
import os
import random
import socket
import time
import traceback
import urllib

HOST = 'localhost:5200'
   
class RestCallError(Exception):
    pass

class RestCallTimeout(Exception):
    pass

def restCall(host, callUrl, method, params={}):
    conn = httplib.HTTPConnection(host)
    url = callUrl + '/' + method
    try:
        conn.request("GET","%s?%s" % (url,urllib.urlencode(params)))
        r = conn.getresponse()
        if not r.reason == 'OK':
            raise RestCallError("%s: %s\n%s" % (r.status,r.reason,r.read()))
        else:
            return json.loads(r.read()).get("result",{})
    except socket.timeout:
        raise RestCallTimeout(traceback.format_exc())
    finally:
        conn.close()

def registerImage(name,when):
    return restCall(HOST,'/rest','newImage',{'name':name,'when':when})

def getImagePath():
    try:
        return restCall(HOST,'/rest','getImagePath')['path']
    except:
        return None
        
def renderFigure(fig,name):
    when = int(time.time())
    canvas = FigureCanvas(fig)
    fp = open(os.path.join(getImagePath(),'%s/%d.png'%(name,when)),'wb')
    canvas.print_figure(fp,facecolor='w',edgecolor='w',format='png')
    fp.close()
    try:
        print registerImage(name,when)
    except:
        print traceback.format_exc()
        
fig=Figure()
ax=fig.add_subplot(111)
line, = ax.plot_date([], [], '-')

while True:
    x=[]
    y=[]
    now=datetime.datetime.now()
    delta=datetime.timedelta(days=1)
    for i in range(10):
        x.append(now)
        now+=delta
        y.append(random.randint(0, 1000))
        line.set_data(x,y)
    ax.grid(True)
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    #name = ['mygraph','weather','station'][random.randint(0,2)]
    name = 'mygraph'
    ax.relim()
    ax.autoscale_view()
    renderFigure(fig,name)
    time.sleep(3)
