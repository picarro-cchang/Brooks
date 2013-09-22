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
        dbMain = client['main_' + env]
        collections = dbMain.collection_names()
        fovCount = 0
        lrtCount = 0
        """
        for c in collections:
           if c.startswith('fov_'): fovCount += 1
           elif c in ['lrt_meta']: print c
           elif c.startswith('lrt_'): lrtCount += 1
           else: print c
        """
        print "<%s>--------------------------------------------------------" % (env,)
        """
        for a in dbMain.analyzer.find().sort([("name",pymongo.ASCENDING)]):
            print a['name'], a.get('lastlog','')
        """
        immutable_names = []
        for x in dbMain.immutable_names.find():
            immutable_names.append((x['nint'], x['name']))
        if immutable_names:
            print "Number of unique names: %d, max index: %d" % (len(set([n for i, n in immutable_names])), max([i for i, n in immutable_names]))
        else:
            print "Number of unique names: 0"
        name_by_index = {}
        index_by_name = {}
        for i,n in immutable_names:
            name_by_index[i] = n
            index_by_name[n] = i

        print "%d dat logs" % (dbMain.analyzer_dat_logs_list.count(),)
        """
        for a in dbMain.analyzer_dat_logs_list.find().sort([("name",pymongo.ASCENDING)]):
            # Check fnm mapping
            try:
                name = a['name'] 
                fileIndex = a['fnm']
                if name_by_index[fileIndex] != name:
                    print "Bad file name mapping"
                nrec = dbMain.analyzer_dat_logs.find({"fnm": fileIndex}).count()
                print name, nrec

            except Exception as e:
                print e
        """

        """
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
        """

finally:
    client.close()
