from influxdb.exceptions import InfluxDBClientError


class Model:

    __keys = None

    @classmethod
    def get_common_keys(cls, keys):
        if cls.__keys is None:
            raise InfluxDBClientError()
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
            keys = cls.get_common_keys(query_params["keys"].split(","))

            # influx epoch times are nanoseconds based
            time_from = query_params["from"]
            time_to = query_params["to"]
            if not (cls.is_dt(time_from) or cls.is_dt(time_to)):
                raise InfluxDBClientError()

            keys = [f"{key}" for key in keys]
            keys = ", ".join(keys)

            query = (f"SELECT {keys} FROM {measurements} "
                     f"WHERE time > {time_from} AND time <= {time_to} fill(previous) "
                     f"ORDER BY time DESC")

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
            
            print(cls.__keys)
            return cls.__keys if result is not None else []
        except ConnectionError as ex:
            log.error(f"Error while retrieving points from measurement {ex}")
