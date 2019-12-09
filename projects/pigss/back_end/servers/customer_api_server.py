#!usr/bin/env/python3
""" Creates an API server which facilitates customers to query influx db
"""

from urllib.parse import parse_qs
from traceback import format_exc

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
        self._keys = None

    def setup_routes(self):
        self.app.router.add_get("/api/v0.1/getkeys", self.handle_get_keys)
        self.app.router.add_get("/api/v0.1/getpoints", self.handle_get_points)

    async def on_startup(self, app):
        log.debug("CustomerAPIServer is starting up")

        self.app["config"] = self.app["farm"].config.get_gdg_plugin_config()

        # Create influxdb connection
        self.app["db_client"] = InfluxDBInstance(self.app["config"]["database"]).get_instance()

    async def on_shutdown(self, app):
        log.debug("CustomerAPIServer is shutting down")

    async def on_cleanup(self, app):
        # Close influxdb connection
        if self.app["db_client"] is not None:
            InfluxDBInstance.close_connection()

    async def get_keys(self):
        measurement = self.app["config"]["database"]["measurements"]
        return await Model.get_keys(self.app["db_client"], log, measurement) 

    async def get_common_keys(self, keys):
        if self._keys is None:
            self._keys = await self.get_keys()
        return list(set(self._keys) & set(keys))

    async def handle_get_keys(self, request=None):
        """
        description: API for fetching keys available to querying measurements

        tags:
            -   Controller
        summary: API for fetching keys available to querying measurements
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation returns keys
        """
        self._keys =  await self.get_keys()
        return web.json_response({"keys": self._keys})

    async def handle_get_points(self, request):
        """
        description: Fetch points in measurement given keys and time range

        tags:
            -   Controller
        summary: Fetch points in measurement given keys and time range
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation returns points in measurement
        """

        query_params = parse_qs(request.query_string)
        measurement = self.app["config"]["database"]["measurements"]
        keys = await self.get_common_keys(query_params["keys"])
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
                    time_from = (int)(parse(time_from, fuzzy=True).timestamp() * i)
                    time_to = (int)(parse(time_to, fuzzy=True).timestamp() * i)
            except OverflowError:
                log.critical(f"Error in Customer API Service {format_exc()}")
                return web.json_response(
                    text="""There is an issue with passed time from and to epoch
                    fields""",
                    status=400,
                )
            except ValueError:
                log.critical(f"Error in Customer API Service {format_exc()}")
                return web.json_response(text="There is an issue with passed from and to fields.", status=400)
        else:
            latest = True

        return web.json_response(
            {"points": await Model.get_points(self.app["db_client"], log, keys, measurement, time_from, time_to, latest)})
