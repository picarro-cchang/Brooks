import random
import datetime

try:
    import simplejson as json
except:
    import json
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
import httplib
import urllib
import socket
import time
import traceback
   
class RestCallError(Exception):
    pass

class RestCallTimeout(Exception):
    pass

def registerImage(name,when):
    host = 'localhost:5200'
    conn = httplib.HTTPConnection(host)
    argsDict = {'name':name,'when':when}
    url = '/rest/newImage'
    try:
        conn.request("GET","%s?%s" % (url,urllib.urlencode(argsDict)))
        r = conn.getresponse()
        if not r.reason == 'OK':
            raise RestCallError("%s: %s\n%s" % (r.status,r.reason,r.read()))
        else:
            return json.loads(r.read()).get("result",{})
    except socket.timeout:
        raise RestCallTimeout(traceback.format_exc())
    finally:
        conn.close()

while True:
    when = int(time.time())
    fig=Figure()
    ax=fig.add_subplot(111)
    x=[]
    y=[]
    now=datetime.datetime.now()
    delta=datetime.timedelta(days=1)
    for i in range(10):
        x.append(now)
        now+=delta
        y.append(random.randint(0, 1000))
    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    #name = ['mygraph','weather','station'][random.randint(0,2)]
    name = 'mygraph'
    fp = open('images/%s/%d.png'%(name,when),'wb')
    canvas.print_png(fp)
    fp.close()
    try:
        print registerImage(name,when)
    except:
        print traceback.format_exc()
    time.sleep(3)
    
