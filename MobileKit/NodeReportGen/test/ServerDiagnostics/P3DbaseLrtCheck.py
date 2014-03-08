#!/usr/bin/python

# Connect to the mongo database using Python

class DbaseError(Exception):
    pass

import datetime
import json
import pymongo

ports = [27017, 37017, 37018]
for p in ports:
    try:
        client = pymongo.MongoClient(port=p)
    except pymongo.errors.ConnectionFailure:
        continue
    if client.is_primary:
        break
    client.close()
else:
    raise DbaseError("Unable to connect to primary database")

try:
    dbNames = client.database_names()
    envNames = [name[6:] for name in dbNames if name.startswith('admin_')]
    print "Environments found:"
    for env in envNames:
        dbAdmin = client['admin_' + env]
        users = dbAdmin.users

        dbMain = client['main_' + env]
        collections = dbMain.collection_names()
        fovCount = 0
        lrtCount = 0
        for c in collections:
           if c.startswith('fov_'): fovCount += 1
           elif c in ['lrt_meta']: continue
           elif c.startswith('lrt_'): lrtCount += 1
           else: continue

        print "%20s: %3d users, %d lrt, %d fov" % (env, users.count(), lrtCount, fovCount)
        # Find lrt job status
        for i,j in enumerate(dbMain.lrt_meta.find({"status": {"$lt": 16}})):
            if i==0: print 'Incomplete Long Running Tasks'
            params = json.loads(j['lrt_prms_str'])
            dt = datetime.datetime.utcnow() - j['lrt_start_ts']
            lrtCollection = j['lrt_collection']
            print '%s:%s (%d) started %.2f hours ago [%s]' % (params['resource'], params['qry'], 
                j['status'], dt.total_seconds()/3600.0, lrtCollection)
            print "  %d records" % dbMain[lrtCollection].count()
            
finally:
    client.close()
