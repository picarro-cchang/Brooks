from db_connection import DBInstance
from traceback import format_exc
import time


async def get_points(query_params, measurements):
    """ Given query_params dictionary, executes SELECT statement to get points
    from measurement "crds"
    
    Arguments:
        query_params {[dict]} -- [ dictionary of all the paramters ]
    """
    print(query_params)
    try:
        client = DBInstance.get_instance()

        # influx epoch times are nanoseconds based
        time_from = query_params["from"]
        time_to = query_params["to"]
        keys = query_params["keys"].split(",")
        keys = [f"last({key})" for key in keys]
        keys = ",".join(keys)

        query = f"SELECT {query_params['keys']} FROM {measurements} where time > {time_from} AND time <= {time_to} fill(previous)"

        # query = f"SELECT {keys} FROM {measurements} where time > {time_from} AND time <= {time_to} group by time(1s) fill(previous) order by time desc "
        print(query)

        start_time = time.time()

        data_generator = client.query(query=query, epoch="ms").get_points()
        result = []
        for datum in data_generator:
            result.append(datum)

        print(f"-> Execution time in seconds {time.time() - start_time}")
        return result
    except ConnectionError as ex:

        format_exc(ex)


async def get_field_keys():
    """ Returns field keys in 'crds' measurement
    
    Returns:
        list[str] -- list of all keys
    """
    client = DBInstance.get_instance()
    data_generator = client.query(f"SHOW FIELD KEYS FROM crds")
    result = None
    for datum in data_generator:
        result = datum
    return [field["fieldKey"] for field in result] if result is not None else []

