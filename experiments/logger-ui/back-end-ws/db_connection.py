import os
import sqlite3


class DBInstance:
    """
    Singleton class for creating DB connection
    """
    __instance = None

    @classmethod
    def get_instance(cls):
        if DBInstance.__instance == None:
            DBInstance()
        return DBInstance.__instance

    def __init__(self, DATABASE="Logs.db"):
        if DBInstance.__instance != None:
            raise Exception("This is a Singleton DB connection class")
        else:
            DBInstance.__instance = self = sqlite3.connect(DATABASE)

    @classmethod
    def close_db_connection(cls):
        if DBInstance.__instance is not None:
            DBInstance.__instance.close()
