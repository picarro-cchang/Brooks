from traceback import format_exc


from influxdb import InfluxDBClient


class DBInitError(Exception):
    """Raised when there is an issue in DB initialization
    """

    pass


class DBCloseError(Exception):
    """Raised when there is an isse in closing the db connection
    """

    pass


class DBInstance:
    """Singleton class for handling InfluxDB connection
    """

    __instance = None

    @classmethod
    def get_instance(cls, app=None):
        """Get the instance if it's not None else open connection with influxdb
        """
        if DBInstance.__instance is None:
            try:
                if app is None:
                    raise DBInitError()
                DBInstance.init_influxdb(app)
            except DBInitError:
                print("Unable to init influx db")
        return DBInstance.__instance

    @classmethod
    async def init_influxdb(cls, app=None):
        """ Initializes __instance with influx client connection
        """

        try:
            db_conf = app["config"]["influxdb"]
            client = InfluxDBClient(
                host=db_conf["host"],
                port=db_conf["port"],
                timeout=db_conf["timeout"],
                retries=db_conf["retries"],
                database=db_conf["database"],
            )
            DBInstance.__instance = client
        except ConnectionError:
            print(format_exc())

    @classmethod
    async def close_influxdb(cls, app=None):
        """Close influx db connection

        Returns:
            bool: indicates if the connection was closed successfully
        """
        try:
            client = DBInstance.get_instance()
            if client is not None:
                client.close()
                return True
            raise DBCloseError()
        except DBCloseError:
            print("Cound not close the DB connection")
            return False
