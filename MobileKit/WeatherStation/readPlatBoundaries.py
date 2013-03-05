#
# Make plat boundaries file from CSV file
#
import csv
try:
    import json
except:
    import simplejson as json
     
fname = "S:\For David Steele\Plats surveyed on Monday.csv"
oname = "S:\For David Steele\Plats surveyed on Monday.json"
fp = file(fname,"rb")
reader = csv.reader(fp)
platDict = {}
headings = None
for row in reader:
    if headings is None:
        if row:
            headings = [h.lower() for h in row]
            nameIndex = headings.index('name')
            minLatIndex = headings.index('minlat')
            maxLatIndex = headings.index('maxlat')
            minLngIndex = headings.index('minlng')
            maxLngIndex = headings.index('maxlng')
    else:
        name = row[nameIndex]
        minLat = float(row[minLatIndex])
        maxLat = float(row[maxLatIndex])
        minLng = float(row[minLngIndex])
        maxLng = float(row[maxLngIndex])
        platDict[name] = [minLng,minLat,maxLng,maxLat] 
fp.close()
op = file(oname,"wb")
json.dump(platDict,op)
op.close()
