from aiohttp import web
from multidict import MultiDict
from urllib.parse import parse_qs
import json

# import os
from os import listdir, error, path, stat


async def index(request):
    print("request", request)

    return web.json_response({"hello": "world"})


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


async def save_file():
    """ Save the file on data_dir folder
    """
    # TO DO:    Get data from influx db
    #           Save the file in tmp/udfg directory
    #           Download at the client
    pass


async def get_user_keys():
    """ Return the keys to the user which are not in admin_keys config
    """
    pass
