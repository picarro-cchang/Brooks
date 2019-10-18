#!/usr/bin/env/python3
""" Used to create a singleton instance to a sqlite database
"""

import os
import sqlite3


class SQLiteInstance:
    """ Singleton instance for sqlite db connection
    """
    __instance = None

    def __init__(self, DB_FILE_PATH):

        if not os.path.isfile(DB_FILE_PATH):
            raise FileNotFoundError("Database file does not exist.")

        if SQLiteInstance.__instance is not None:
            pass
        else:
            SQLiteInstance.__instance = self = sqlite3.connect(DB_FILE_PATH)

    @classmethod
    def get_instance(cls):
        if SQLiteInstance.__instance is None:
            raise RuntimeError("SQLITE Connection has not been initialized.")
        return SQLiteInstance.__instance

    @classmethod
    def close_connection(cls):
        if SQLiteInstance.__instance is not None:
            SQLiteInstance.__instance.close()
