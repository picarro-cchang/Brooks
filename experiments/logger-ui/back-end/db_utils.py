import os
import sqlite3
from flask import g

DATABASE = '../db/Logs.db'


def get_connection():
    """
    create a sqlite db connection

    params:
        The database file location, currently hard-coded in DATABASE variable
    return:
        Connection object
    """
    connection = getattr(g, '_database', None)
    if connection is None:
        connection = g._database = sqlite3.connect(DATABASE)
    return connection


