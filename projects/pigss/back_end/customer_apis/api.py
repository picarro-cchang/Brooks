from urllib.parse import parse_qs


from aiohttp import web
from dateutil.parser import parse


import db


def is_date(date_str, fuzzy=True):
    try:
        parse(date_str, fuzzy=fuzzy)
        return True
    except ValueError:
        return False


async def get_keys(request):
    """ Fetches field keys from measurement
    
    Arguments:
        request  -- 
    
    Returns:
        JSON -- JSON object containing list of keys from measurement
    """
    return web.json_response(
        {"keys": await db.get_keys(request.app["config"]["influxdb"]["measurement"])}
    )


async def get_points(request):
    """ Returns list of points in measurements based on provided constrains

    It can parse two different time formats: UTC and unix epoch
    
    Arguments:
        request {[type]} -- request object
    
    Returns:
        JSON -- returns JSON object of points in measurement for given keys
    """

    query_params = parse_qs(request.query_string)
    measurement = request.app["config"]["influxdb"]["measurement"]
    keys = query_params["keys"]
    time_from = time_to = None
    latest = False
    is_epoch = query_params["epoch"][0] if "epoch" in query_params else None

    if "time" not in keys:
        keys.append("time")
    if "valve_pos" not in keys:
        keys.append("valve_pos")

    keys = ", ".join(keys)
    if "from" in query_params and "to" in query_params:
        time_from = query_params["from"][0]
        time_to = query_params["to"][0]

        try:
            # Check if provided time is epoch
            # Understand JS epoch time
            if is_epoch == "true":
                time_from = int(time_from) * 1000000
                time_to = int(time_to) * 1000000
            else:
                time_from = (int)(parse(time_from, fuzzy=True).timestamp() * 1000000000)
                time_to = (int)(parse(time_to, fuzzy=True).timestamp() * 1000000000)
        except OverflowError:
            return web.json_response(
                text="There is some issue with passed time- from and to epoch fields",
                status=400,
            )
        except ValueError:
            return web.json_response(
                text="There is some issue with passed from and to fields.", status=400
            )
    else:
        latest = True

    return web.json_response(
        {"keys": await db.get_points(keys, measurement, time_from, time_to, latest)}
    )
