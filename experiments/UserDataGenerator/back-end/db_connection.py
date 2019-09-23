from influxdb import InfluxDBClient

class DBInstance:

    """
    Singleton class for handling db connections
    """

    __instance = None

    @classmethod
    def get_instance(cls, app):
        if DBInstance.__instance is None:
            DBInstance.init_influxdb(app)
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
        TO DO
        """
        print("TO DO: close db connection")
        return {}
