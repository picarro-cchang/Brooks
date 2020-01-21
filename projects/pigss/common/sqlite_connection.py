#!/usr/bin/env/python3
""" Used to create a singleton instance to a sqlite database
"""

import os
import sqlite3


class SQLiteInstance:
    """ Singleton instance for sqlite db connection
    """
    __instance = None
    __current_db = None

    def __init__(self, DB_FILE_PATH):

        if not os.path.isfile(DB_FILE_PATH):
            raise FileNotFoundError(f"Database file does not exist: {DB_FILE_PATH}")

        if SQLiteInstance.__instance is not None and SQLiteInstance.__current_db != DB_FILE_PATH:
            # Close old connection instance
            SQLiteInstance.close_connection()
        if SQLiteInstance.__instance is not None and SQLiteInstance.__current_db == DB_FILE_PATH:
            pass
        else:
            SQLiteInstance.__current_db = DB_FILE_PATH
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
