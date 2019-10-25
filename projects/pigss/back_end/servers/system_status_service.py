#!/usr/bin/env python3
"""
Provides a JSON datasource for Grafana which serves up information
 about the status of various aspects of the system, such as the
 Picarro analyzers.
"""

from aiohttp import web

from back_end.lologger.lologger_client import LOLoggerClient
from back_end.servers.service_template import ServiceTemplate

log = LOLoggerClient(client_name="SystemStatusService", verbose=True)


class SystemStatusService(ServiceTemplate):
    def __init__(self):
        super().__init__()

    def setup_routes(self):
        self.app.router.add_route("GET", "/", self.health_check)
        self.app.router.add_route('GET', '/analyzer_status', self.handle_analyzer_status)

    async def on_startup(self, app):
        log.info("System status service is starting up")

    async def on_shutdown(self, app):
        log.info("System status service is shutting down")

    async def handle_analyzer_status(self, request):
        """
        description: Retrieve status of Picarro analyzers

        tags:
            -   System status server
        summary: Retrieve status of Picarro analyzers
        produces:
            -   text/plain
        responses:
            "200":
                description: successful operation."
        """
        farm = request.app['farm']
        result = []
        self.picarro_analyzers = [rpc_name for rpc_name in farm.RPC if rpc_name.startswith("Picarro_")]
        for analyzer in self.picarro_analyzers:
            name = analyzer[len("Picarro_"):]
            inst_mgr_state = (await farm.RPC[analyzer].INSTMGR_GetStateRpc())["InstMgr"]
            warming_state = await farm.RPC[analyzer].DR_getWarmingState()
            cavity_temp, cavity_temp_setpoint = warming_state["CavityTemperature"]
            warm_box_temp, warm_box_temp_setpoint = warming_state["WarmBoxTemperature"]
            cavity_pressure, cavity_pressure_setpoint = warming_state["CavityPressure"]
            result.append({
                "name": name,
                "cavity_temp": cavity_temp,
                "cavity_temp_setpoint": cavity_temp_setpoint,
                "warm_box_temp": warm_box_temp,
                "warm_box_temp_setpoint": warm_box_temp_setpoint,
                "cavity_pressure": cavity_pressure,
                "cavity_pressure_setpoint": cavity_pressure_setpoint,
                "status": inst_mgr_state
            })
        return web.json_response(result)

    async def health_check(self, request):
        """
        description: Used to check that data source exists and works

        tags:
            -   System status server
        summary: Used to check that data source exists and works
        produces:
            -   application/text
        responses:
            "200":
                description: successful operation.
        """
        return web.Response(text='This datasource is healthy.')
