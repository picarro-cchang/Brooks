import os
import sqlite3

# DATABASE = "~/Code/POCs/NEW0814_2019_08.db"
DATABASE = "Logs.db"


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

    def __init__(self):
        if DBInstance.__instance != None:
            raise Exception("This is a Singleton DB connection class")
        else:
            DBInstance.__instance = self = sqlite3.connect(DATABASE)