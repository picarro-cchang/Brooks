#!/usr/bin/env/python3
""" Used to create a singleton instance to a influx database
"""

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError


class InfluxDBInstance:
    """ Singleton instance for influx db connection
    """

    __instance = None

    def __init__(self, config):
        """ Initializes instance of influx db connection

        Arguments:
            config {dict} -- config dict consists of parameters to create a
            connection

            eg config = {
                'host': '0.0.0.0',
                'port': 8086,
                'database': 'dbname',
                'timeout': None
                'retries': 3
            }
        """
        if InfluxDBInstance.__instance is not None:
            pass

        try:
            InfluxDBInstance.__instance = InfluxDBClient(
                host=config["host"],
                port=config["port"],
                timeout=config["timeout"],
                retries=config["retries"],
                database=config["database"]
            )
        except InfluxDBClientError:
            raise ConnectionError(
                "Unable to connect to influx db. Check configuration.")
    
    @classmethod
    def get_instance(cls):
        if InfluxDBInstance.__instance is None:
            InfluxDBInstance()
        return InfluxDBInstance.__instance

    @classmethod
    def close_connection(cls):
        if InfluxDBInstance.__instance is not None:
            InfluxDBInstance.__instance.close()
