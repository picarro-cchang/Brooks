from flask import Flask, Markup
from flask import make_response, render_template, request, Response
try:
    import simplejson as json
except:
    import json
import os
import sys
import calendar
import time
import traceback
import urllib

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
IMAGEROOT = os.path.join(appDir,'images')
STATICROOT = os.path.join(appDir,'static')
imagesAvailable = {}

# Images are stored in images/<imageName>/<epochTime>.png. This allows multiple versions of each image to be kept.
#
# The call /rest/getImagePath returns the full path of the images directory. This is useful for the artist to know where 
#  to place the image files.
#
# When the server starts up, it goes through the subdirectories of images. It constructs a dictionary called imagesAvailable 
# such that imagesAvailable[<imageName>] is a sorted list of the epoch times of the images available called imageName.
#
# When an artist generates a new version of an image, it calls the server function rest/newImage?name=<imageName>&time=<epochTime>. 
# The server updates imagesAvailable and deletes any old versions of that image until at most two remain. Note that the list in 
# imagesAvailable must be updated before the file is removed from the directory.
#
# When a consumer wishes to request an image, it first calls rest/mostRecentImage?name=<imageName>. The server returns the epoch 
#  time of the most recent image with that name, by looking up imagesAvailable. The consumer can decide whether to call 
#  rest/getImage?name=<imageName>, which returns the most recent image then available. Note that this may be more recent than that 
#  sent back to the consumer, but this is not a problem, since all that the #consumer does with the time it is given is to decide 
#  whether to load a more recent image.

for dirpath,dirnames,filenames in os.walk(IMAGEROOT):
    pngfiles = sorted([int(f[:-4]) for f in filenames if f.endswith('.png')])
    if pngfiles:
        name = os.path.split(dirpath)[-1]
        for f in pngfiles[:-2]:
            os.remove(os.path.join(dirpath,'%d.png'%f))
        imagesAvailable[name] = pngfiles[-2:]

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def index():
    return render_template('graph.html')

def getImagePathEx(params):
    try:
        return dict(path=os.path.abspath(IMAGEROOT))
    except:
        return dict(error=traceback.format_exc())
    
@app.route('/rest/getImagePath')
def getImagePath():
    result = getImagePathEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
    
def newImageEx(params):
    try:
        name = params['name'].strip()
        when = int(params['when'].strip())
        fname = os.path.join(IMAGEROOT,'%s/%d.png'%(name,when))
        if not os.path.exists(fname):
            raise ValueError('Image file %s not found on server' % fname)
        if name not in imagesAvailable: imagesAvailable[name] = []
        imagesAvailable[name].append(when)
        for f in imagesAvailable[name][:-2]:
            try:
                os.remove(os.path.join(IMAGEROOT,'%s/%d.png'%(name,f)))
            except:
                pass
        imagesAvailable[name][:] = imagesAvailable[name][-2:]
        return dict(available=imagesAvailable[name])
    except:
        return dict(error=traceback.format_exc())
    
@app.route('/rest/newImage')
def newImage():
    result = newImageEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))

def mostRecentImageEx(params):
    try:
        name = params['name'].strip()
        return dict(when=imagesAvailable[name][-1])
    except:
        return dict(when=None)
        
@app.route('/rest/mostRecentImage')
def mostRecentImage():
    result = mostRecentImageEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
        
@app.route('/rest/getImage')
def getImage():
    try:
        name = request.values['name'].strip()
        when = imagesAvailable[name][-1]
        fname = os.path.join(IMAGEROOT,'%s/%d.png'%(name,when))
        fp = file(fname,'rb')
        try:
            response = make_response(fp.read())
        finally:
            fp.close()
    except:
        fname = os.path.join(STATICROOT,'errorIcon.png')
        fp = file(fname,'rb')
        try:
            response = make_response(fp.read())
            when = time.time()
        finally:
            fp.close()
    response.headers['Content-Type'] = 'image/png'
    response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(when))
    return response
    
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5200,debug=True)
