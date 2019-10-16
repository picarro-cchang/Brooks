from traceback import format_exc
import time

from influxdb.exceptions import InfluxDBClientError

from db_connection import DBInstance


async def get_points(keys, measurement, time_from=None, time_to=None, latest=False):
    """Generate and execute SQL statements to fetch points from measurement
    
    Arguments:
        query_params {dict} -- dictionary of all constraints
        measurement {list(str)} -- list of influx measurement

    Returns:
        {list(dict)} -- the list of all rows satisying given conditions
    """
    try:
        client = DBInstance.get_instance()

        query = f"SELECT {keys} FROM {measurement} "

        if not latest:
            query += f"WHERE time >= {time_from} AND time <= {time_to}"
        else:
            query = f"SELECT {keys} FROM {measurement} order by time desc limit 1"

        print("query", query)
        data_generator = client.query(query=query, epoch="ms").get_points()
        result = []
        for datum in data_generator:
            result.append(datum)

        return result

    except ConnectionError:
        print(format_exc())
    except InfluxDBClientError:
        print("Error executing query", query)


async def get_keys(measurement):
    """Returns list of field keys in measurements from influxdb
    
    Arguments:
        measurements {list(str)} -- list of str representing measurements
    
    Returns:
        dict -- dict of field keys for each measurement
    """

    try:
        client = DBInstance.get_instance()
        result = []
        query = f"SHOW FIELD KEYS FROM {measurement}"
        data_generator = client.query(query)
        for datum in data_generator:
            for field in datum:
                result.append(field["fieldKey"])
        return result
    except ConnectionError:
        print(format_exc())
    except InfluxDBClientError:
        print("Error getting keys from databases.")
