#!usr/bin/env/python3

""" Creates an API server which fascilitates customers to query influx db
"""

from urllib.parse import parse_qs

from aiohttp import web
from dateutil.parser import parse

from back_end.lologger.lologger_client import LOLoggerClient
from common.influx_connection import InfluxDBInstance
from back_end.servers.service_template import ServiceTemplate
from back_end.customer_api_server.model import Model

log = LOLoggerClient(client_name="CustomerAPIServer")


class CustomerAPIService(ServiceTemplate):

    def __init__(self):
        super().__init__()

    def setup_routes(self):
        self.app.router.add_get("/api/v0.1/getkeys", self.get_keys)
        self.app.router.add_get("/api/v0.1/getpoints", self.get_points)

    async def on_startup(self, app):
        log.info("CustomerAPIServer is starting up")

        self.app["config"] = self.app["farm"].config.get_gdg_plugin_config()

        # Create influxdb connection
        self.app["db_client"] = InfluxDBInstance(
            self.app["config"]["database"]).get_instance()

    async def on_shutdown(self, app):
        log.info("CustomerAPIServer is shutting down")

    async def on_cleanup(self, app):
        # Close influxdb connection
        if self.app["db_client"] is not None:
            InfluxDBInstance.close_connection()

    async def get_keys(self, request):
        """ Fetches field keys from measurement

        Arguments:
            request  -- request object

        Returns:
            JSON -- JSON object containing list of keys from measurement
        """
        measurement = self.app["config"]["database"]["measurements"]
        return web.json_response({"keys": await Model.get_keys(self.app["db_client"], log, measurement)})

    async def get_points(self, request):
        """ Returns list of points in measurements based on provided constraints

        It can parse two different time formats: UTC and unix epoch

        Arguments:
            request {[type]} -- request object

        Returns:
            JSON -- returns JSON object of points in measurement for given keys
        """

        query_params = parse_qs(request.query_string)
        measurement = self.app["config"]["database"]["measurements"]
        keys = query_params["keys"]
        time_from = time_to = None
        latest = False
        is_epoch = query_params["epoch"][0] if "epoch" in query_params else None

        if "time" not in keys:
            keys.append("time")
        if "valve_pos" not in keys:
            keys.append("valve_pos")

        
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
                    # Multiplier for conversion into ns timestamps
                    i = 1000000000
                    time_from = (int)(
                        parse(time_from, fuzzy=True).timestamp() * i)
                    time_to = (int)(parse(time_to, fuzzy=True).timestamp() * i)
            except OverflowError:
                return web.json_response(
                    text="""There is an issue with passed time from and to epoch
                    fields""",
                    status=400,
                )
            except ValueError:
                return web.json_response(
                    text="There is an issue with passed from and to fields.",
                    status=400
                )
        else:
            latest = True

        return web.json_response(
            {
                "keys": await Model.get_points(
                    self.app["db_client"],
                    log,
                    keys,
                    measurement,
                    time_from,
                    time_to,
                    latest)
            }
        )
