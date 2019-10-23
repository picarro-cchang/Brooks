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
    async def get_points(cls, client, log, keys, measurement, time_from=None, time_to=None, latest=False):
        """Generate and execute SQL statements to fetch points from measurement

        Arguments:
            query_params {dict} -- dictionary of all constraints
            measurement {list(str)} -- list of influx measurement

        Returns:
            {list(dict)} -- the list of all rows satisfying given conditions
        """
        try:
            # Filter common keys and create a string
            keys = cls.get_common_keys(keys)

            if latest is False and not (cls.is_dt(time_from) or cls.is_dt(time_to)):
                raise InfluxDBClientError()

            keys = ", ".join(keys)
            query = f"SELECT {keys} FROM {measurement} "

            if not latest:
                query += f"WHERE time >= {time_from} AND time <= {time_to}"
            else:
                query = (f"SELECT {keys} FROM {measurement}" f" ORDER BY time DESC LIMIT 1", )

            data_generator = client.query(query=query, epoch="ms").get_points()
            result = []
            for datum in data_generator:
                result.append(datum)

            return result

        except ConnectionError as ce:
            log.error("ConnectionError in CustomerAPIServer", ce)
        except InfluxDBClientError:
            log.error("Error executing query", query)

    @classmethod
    async def get_keys(cls, client, log, measurement):
        """Returns list of field keys in measurements from influxdb

        Arguments:
            measurements {list(str)} -- list of str representing measurements

        Returns:
            dict -- dict of field keys for each measurement
        """

        try:
            result = []
            query = f"SHOW FIELD KEYS FROM {measurement}"
            data_generator = client.query(query)
            for datum in data_generator:
                for field in datum:
                    result.append(field["fieldKey"])
            cls.__keys = result
            return result
        except ConnectionError:
            log.error("ConnectionError in CustomerAPIServer")
        except InfluxDBClientError:
            log.error("CustomerAPIServer: Error getting keys from databases.")
