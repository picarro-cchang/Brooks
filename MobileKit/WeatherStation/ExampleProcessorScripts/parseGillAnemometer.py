from math import cos, sin, pi

def parseGillAnemometer(rawStr):
    retList = []
    rawStr = rawStr.strip()
    atoms = rawStr.split(",")
    windLon,windLat = -float(atoms[1]), -float(atoms[2])
    retList = [windLon,windLat]
    return retList
