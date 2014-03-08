#!/usr/bin/python

import pymongo


class DbaseError(Exception):
    pass


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
    dbase = client["test"]

    counters = dbase["counters"]
    counters.drop_indexes()
    counters.remove()

    counters.insert({"_id": "immutable_names", "next": 0})

    immutable_names = dbase["immutable_names"]
    immutable_names.drop_indexes()
    immutable_names.remove()

    immutable_names.ensure_index([("nint", pymongo.ASCENDING)], unique=True)
    immutable_names.ensure_index([("name", pymongo.ASCENDING)], unique=True)

finally:
    client.close()
