from aiohttp import web
from multidict import MultiDict
from urllib.parse import parse_qs
import csv
from os import listdir, error, path, stat, environ
from db import get_field_keys, get_points
from datetime import datetime
from traceback import format_exc, print_exc


def validate_request():
    """ Validation for request for pre-defined constraints
    """
    pass


async def get_files_meta(request):
    """ Get files meta to be returned to frontend
    """
    data_dir = request.app["config"]["server"]["data_dir"]

    try:
        # Filter only CSV files
        files = [
            f
            for f in listdir(data_dir)
            if f.endswith(request.app["config"]["server"]["file_type"])
        ]
    except error as ex:
        from traceback import format_exc

        format_exc()
        return web.json_response(text="OS Permission Error", status=404)

    files.sort(key=lambda name: name.lower())

    return web.json_response({"files": files})


def chunks(stream, chunk_size=1024):
    """ Read a CSV file in chunks
    
    Arguments:
        stream {file} -- IO wrapper
    
    Keyword Arguments:
        chunk_size {int} -- (default: {1024})
    """
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        yield chunk


async def send_file(request):
    """ Send file to the user for download
    
    Arguments:
        request {Request}
    
    Returns:
        [Response] -- responsds with file if correct format and found
    """

    query_dict = parse_qs(request.query_string)
    data_dir = request.app["config"]["server"]["data_dir"]
    file_name = query_dict["name"][0]
    print(file_name)
    file_path = path.join(data_dir, file_name)
    file_type = request.app["config"]["server"]["file_type"]

    if not (file_name.endswith(file_type) and path.exists(file_path)):
        return web.HTTPNotFound()

    stats = stat(file_path)

    res = web.StreamResponse(
        headers={"Content-Disposition": f"Attachment; filename={file_name}"}
    )
    res.content_type = file_type
    res.content_length = stats.st_size

    with open(file_path, "rb") as fl:
        await res.prepare(request)
        for chunk in chunks(fl):
            await res.write(chunk)
            await res.drain()
        await res.write_eof()
        res.force_close()
        return res


async def write_csv_file(result, data_dir, file_name):
    file_path = f"{data_dir}/{file_name}"
    print("file_path", file_path)

    # TODO: Uncomment for production
    # if path.exists(file_path) and path.isfile(file_name):
    #     return web.json_response(
    #         {"message": "File already exist for such query. Try downloading it."}
    #     )
    keys = result[0].keys()
    try:
        with open(file_path, "w+") as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(result)
        return True
    except IOError as ioe:
        print_exc()
    except Exception as e:
        print_exc()
    return False


async def generate_file(request):
    """Save the file on data_dir folder
    
    Returns:
        [filename: string] -- [filename if the file is successfully saved]
    """

    query_dict = parse_qs(request.query_string)
    query_params = {
        "keys": ",".join(query_dict["keys"]),
        "from": int(query_dict["from"][0]),
        "to": int(query_dict["to"][0]),
    }
    measurements = ", ".join(request.app["config"]["influxdb"]["measurements"])
    result = await get_points(query_params, measurements)

    if len(result) == 0:
        return web.json_response({"message": "No observation in the measurements"})

    try:
        host_name = environ["HOSTNAME"]
        data_dir = request.app["config"]["server"]["data_dir"]
        print(query_params["from"], query_params["to"])

        # python's epoch time is in seconds
        time_from = datetime.fromtimestamp(query_params["from"] / 1000000000)
        time_to = datetime.fromtimestamp(query_params["to"] / 1000000000)

        from_formatted = time_from.strftime("%m-%d-%Y_%H%M%S")
        to_formatted = time_to.strftime("%m-%d-%Y_%H%M%S")

        file_name = f"{host_name}-{from_formatted}->{to_formatted}.csv"

        success = await write_csv_file(result, data_dir, file_name)
    except KeyError as ke:
        print("HOSTNAME enveironment variable is not defined.")
    except Exception as ex:
        print_exc()
        return web.json_response({"message": "Error in generating file"})
    if success:
        return web.json_response({"filename": file_name})


async def get_user_keys(request):
    """ Return the keys to the user which are not in admin_keys config
    """
    field_keys = await get_field_keys()
    user_keys = request.app["config"]["user_keys"]
    print(field_keys[:5])
    # {"keys": list(filter(lambda x: x in field_keys, user_keys))}
    # return web.json_response({"keys": field_keys})
    return web.json_response(
        {"keys": list(filter(lambda x: x in field_keys, user_keys))}
    )
