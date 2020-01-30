#!/usr/bin/env python3
"""
Provides a JSON datasource for Grafana which serves up information
 about the species that can be analyzed by the current setup.
"""
import json
import time

from aiohttp import web
from aioinflux import iterpoints

from back_end.database_access.aio_influx_database import AioInfluxDBWriter
from back_end.lologger.lologger_client import LOLoggerClient
from back_end.servers.service_template import ServiceTemplate

log = LOLoggerClient(client_name="PortHistoryService", verbose=True)


class PortHistoryService(ServiceTemplate):
    def __init__(self):
        super().__init__()

    def setup_routes(self):
        self.app.router.add_route("GET", "/", self.health_check)
        self.app.router.add_route("POST", "/search", self.search)

    async def on_startup(self, app):
        log.debug("Species Type service is starting up")

    async def on_shutdown(self, app):
        log.debug("Species Type service is shutting down")

    async def health_check(self, request):
        """
        description: Used to check that data source exists and works

        tags:
            -   Species Type service
        summary: Used to check that data source exists and works
        produces:
            -   application/text
        responses:
            "200":
                description: successful operation.
        """
        return web.Response(text='This datasource is healthy.')

    async def search(self, request):
        """
        description: Gets the names of the available banks or the available ports

        tags:
            -   Species Type service
        summary:  Gets the names of the available banks or the available ports

        consumes:
            -   application/json
        parameters:
            -   in: body
                name: query
                description: Specify what to retrieve
                required: false
                schema:
                    type: object
                    properties:
                        target:
                            type: string
                            description: >
                                search string in JSON format, which can be a time range as
                                an array of millisecond start and end times or as an object with
                                type and range keys.
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        # The query can be a range with a list of start and end times in ms since epoch, or a dictionary
        #  with keys "range" and "type".

        # start_ms and end_ms are the Grafana time range for the plots
        species = [{ }]
        
        return web.json_response(species)
