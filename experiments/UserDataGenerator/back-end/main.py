from aiohttp import web
import logging
import sys
import asyncio
import aiohttp_cors

from settings import get_config
from db_connection import DBInstance
from api import get_files_meta, send_file, get_user_keys, generate_file


async def init_app(argv=None):

    app = web.Application()
    app["config"] = get_config(argv)

    # Handle db init on app start up
    app.on_startup.append(DBInstance.init_influxdb)

    # Handle db init on app start up
    app.on_startup.append(DBInstance.close_influxdb)

    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*"
            )
        },
    )

    # Setup routes
    app.router.add_get("/api/getsavedfiles", get_files_meta)
    app.router.add_get("/api/getfile", send_file)
    app.router.add_get("/api/getkeys", get_user_keys)
    app.router.add_get("/api/generatefile", generate_file)

    for route in app.router.routes():
        cors.add(route)

    return app


def main(argv):
    """
    Server entry point
    """
    config = get_config(argv)
    app = init_app(argv)
    web.run_app(app, host=config["server"]["host"], port=config["server"]["port"])
