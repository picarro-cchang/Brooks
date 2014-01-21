#!/usr/bin/python

import pymongo


class DbaseError(Exception):
    pass



class DatabaseInterface(object):

    def __init__(self):
        ports = [27017, 37017, 37018]
        for p in ports:
            try:
                self.client = pymongo.MongoClient(port=p)
            except pymongo.errors.ConnectionFailure:
                continue
            if self.client.is_primary:
                break
            self.client.close()
        else:
            raise DbaseError("Unable to connect to primary database")
        self.dbase = self.client["test"]
        self.counters = self.dbase["counters"]
        self.immutable_names = self.dbase["immutable_names"]

    def getAndIncrementSequenceNumber(self, name="immutable_names"):
        result = self.counters.find_and_modify({"_id": name}, {"$inc": {"next": 1}}, new=False)
        return result["next"]

    def getIndexOf(self, name):
        """Get the index of the specified name in the immutable_names table. If the name
        does not currently exist in the table, it is added to the table and its index is 
        returned"""
        result = self.immutable_names.find_one({"name": name})
        if result is None:
            seq = self.getAndIncrementSequenceNumber()
            print seq
            try:
                self.immutable_names.insert({"name": name, "nint":seq})
            except pymongo.OperationFailure as e:
                result = self.immutable_names.find_one({"name": name})
                if result is None:
                    raise DbaseError("Error getting index of %s" % name)
                return result["nint"]
        else:
            return result["nint"]

    def close(self):
        self.client.close()

if __name__ == "__main__":
    try:
        db = DatabaseInterface()
        print db.getIndexOf("baz")
        print db.getIndexOf("foo")
        print db.getIndexOf("bar")
        print db.getIndexOf("baz")
        print db.getIndexOf("bar")
        print db.getIndexOf("foo")
    finally:
        db.close()
