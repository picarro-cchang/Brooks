from traceback import format_exc

from influxdb.exceptions import InfluxDBClientError


class DataExportModel:

    __keys = None

    @classmethod
    async def get_common_keys(cls, keys, client, measurements, log):
        if cls.__keys is None:
            cls.__keys = await cls.get_user_keys(client, measurements, log)
        return list(set(cls.__keys) & set(keys))

    @classmethod
    def is_dt(cls, dt):
        return isinstance(dt, int)

    @classmethod
    async def get_points(cls, client, log, query_params, measurements):
        """ Given query_params dictionary, executes SELECT statement to get
        points from measurement "crds"

        Arguments:
            query_params {[dict]} -- [ dictionary of all the paramters ]
        """
        try:
            # Filter common keys and create a string
            keys = await cls.get_common_keys(
                query_params["keys"].split(","), client, measurements, log)
            analyzer = query_params["analyzer"]
            port = query_params["port"]

            # influx epoch times are nanoseconds based
            time_from = query_params["from"]
            time_to = query_params["to"]
            if not (cls.is_dt(time_from) or cls.is_dt(time_to)):
                raise InfluxDBClientError()

            keys = [f"{key}" for key in keys]
            keys = ", ".join(keys)
            
            # Enabling user to download processed and unprocessed data
            if query_params["isProcessedData"]:
                query = (f"SELECT time as Time, analyzer as Analyzer, valve_pos as Port, {keys} FROM {measurements} "
                        f"WHERE analyzer =~ /{analyzer}/ "
                        f"AND valve_pos =~ /{port}/ "
                        f"AND valve_stable_time > 15 "
                        f"AND time > {time_from} AND time <= {time_to} "
                        f"ORDER BY time DESC")
            else:
                query = (f"SELECT time as Time, analyzer as Analyzer, valve_pos as Port, {keys} FROM {measurements} "
                        f"WHERE analyzer =~ /{analyzer}/ "
                        f"AND valve_pos =~ /{port}/ "
                        f"AND time > {time_from} AND time <= {time_to} "
                        f"ORDER BY time DESC")
            
            print("----> Check out query", query)

            data_generator = client.query(query=query, epoch="ms").get_points()
            result = []
            for datum in data_generator:
                result.append(datum)

            return result
        except ConnectionError as ex:
            log.error(f"Error while retrieving points from measurement {ex}")

    @classmethod
    async def get_user_keys(cls, client, measurements, log):
        """ Returns field keys and tag keys in measurements

        Returns:
            list[str] -- list of all keys
        """
        try:
            field_keys = client.query(f"SHOW FIELD KEYS FROM {measurements}")
            tag_keys = client.query(f"SHOW TAG KEYS FROM {measurements}")
            datum = None
            
            for datum in field_keys:
                result = datum
            cls.__keys = [field["fieldKey"]for field in result]

            for datum in tag_keys:
                result = datum
            cls.__keys.extend([tag["tagKey"]for tag in result])
            
            return cls.__keys if result is not None else []
        except ConnectionError as ex:
            log.error(f"Error while retrieving points from measurement.")
            log.debug(f"Error while retrieving points from measurement {ex}")

    @classmethod
    async def get_analyzers(cls, client, measurement, log):
        """ Returns list of analyzers available in the SAM setup

        Returns:
            list[str] -- list of available analyzers
        """
        try:
            analyzers_result_set = client.query(f'SHOW TAG VALUES FROM {measurement} WITH KEY = "analyzer"')
            analyzers = []
            for datum in analyzers_result_set:
                analyzers = datum
            return [analyzer["value"] for analyzer in analyzers]
        except ConnectionError:
            log.error(f"Error while retrieving available analyzers.")
            log.debug(f"Error while retrieving available analyzers {format_exc()}")
