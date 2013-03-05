try:
    import simplejson as json
except:
    import json
import numpy as np
# Write out plat boundaries as a JSON file
fname = "platBoundaries.npz"
result = np.load(fname,"rb")
platBoundaries = {}
for n,a,b,c,d in zip(result['names'],result['minlng'],result['minlat'],result['maxlng'],result['maxlat']):
    platBoundaries[n] = (a,b,c,d)
file("platBoundaries.json","wb").write(json.dumps(platBoundaries))
