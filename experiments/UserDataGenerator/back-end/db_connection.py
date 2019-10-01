from influxdb import InfluxDBClient


class DBInitError(Exception):
    """ DB initialization error
    
    """

    pass


class DBInstance:

    """
    Singleton class for handling db connections
    """

    __instance = None

    @classmethod
    def get_instance(cls, app=None):
        if DBInstance.__instance is None:
            try:
                if app is None:
                    raise DBInitError("")
                DBInstance.init_influxdb(app)
            except DBInitError:
                print("App is not initialized")
                raise
        return DBInstance.__instance

    @classmethod
    async def init_influxdb(cls, app):
        try:
            db = app["config"]["influxdb"]
            client = InfluxDBClient(
                host=db["host"],
                port=db["port"],
                timeout=db["timeout"],
                retries=db["retries"],
                database=db["database"],
            )
            # client.switch_database(db["database"])
            DBInstance.__instance = client
        except ConnectionError as ex:
            print(ex)

    @classmethod
    async def close_influxdb(cls, app):
        """
        TODO
        """
        try:
            DBInstance.get_instance().close()
            return True
        except Exception as ex:
            raise

