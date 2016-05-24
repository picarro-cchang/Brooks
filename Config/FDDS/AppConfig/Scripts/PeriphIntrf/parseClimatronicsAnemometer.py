from math import cos, sin, pi

def parseWeatherStation(rawStr):
    retList = []
    rawStr = rawStr.strip()
    (windLon,windLat,heading) = \
        tuple([float(x.strip()) for x in rawStr.split(",") if not x.strip().startswith("*")])
    # Convert angle variables into cosines and sines for proper averaging
    h = heading * pi / 180.0
    retList = [windLon,windLat,cos(h),sin(h)]
    return retList
