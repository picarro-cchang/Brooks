import asyncio
import time

from aiohttp import web

from async_hsm import Event, Framework, Signal
from experiments.common.async_helper import log_async_exception
from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from experiments.common.service_template import ServiceTemplate

log = LOLoggerClient(client_name="SupervisorService", verbose=True)


class SupervisorService(ServiceTemplate):
    def __init__(self):
        super().__init__()

    def setup_routes(self):
        self.app.router.add_route('GET', '/device_map', self.handle_device_map)
        self.app.router.add_route('GET', '/processes', self.handle_processes)

    async def on_startup(self, app):
        self.tasks = []

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()

    async def on_cleanup(self, app):
        print("SupervisorService is cleaning up")

    async def handle_device_map(self, request):
        """
        description: Fetch device map info from PigssSupervisor

        tags:
            -   Supervisor
        summary: fetch device map from PigssSupervisor
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns device map
        """
        supervisor = request.app['farm'].pigss_supervisor
        return web.json_response(supervisor.get_device_map())

    async def handle_processes(self, request):
        """
        description: Fetch list of managed processes

        tags:
            -   Supervisor
        summary: Fetch list of managed processes
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns process list
        """
        supervisor = request.app['farm'].pigss_supervisor
        return web.json_response(supervisor.get_processes())
