import aiohttp_cors
from aiohttp import web

from db_connection import DBInstance
from api import get_keys, get_points


async def init_app():

    app = web.Application()
    app["config"] = {
        "influxdb": {
            "host": "10.100.3.28",
            "port": 8086,
            "database": "pigss_data",
            "timeout": 60,
            "retries": 3,
            "measurement": "crds",
        },
    }

    # DB Init on app startup
    app.on_startup.append(DBInstance.init_influxdb)

    # DB Init on app startup
    app.on_shutdown.append(DBInstance.close_influxdb)

    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*"
            )
        },
    )

    # Setup routes
    app.router.add_get("/api/v0.1/getkeys", get_keys)
    app.router.add_get("/api/v0.1/getpoints", get_points)

    for route in app.router.routes():
        cors.add(route)

    return app


def main():
    """Server entry point
    """

    app = init_app()

    web.run_app(app, host="0.0.0.0", port=8010)
