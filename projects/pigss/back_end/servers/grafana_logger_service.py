#!/usr/bin/env python3
""" Provides an API for sending logs to grafana logger plugin using websockets
"""

import asyncio
import time
from json import loads
from datetime import datetime, timedelta

from aiohttp import web, WSMsgType, WSCloseCode

from back_end.lologger.lologger_client import LOLoggerClient
from common.CmdFIFO import CmdFIFOServerProxy
from common.rpc_ports import rpc_ports
from back_end.servers.service_template import ServiceTemplate
from common.async_helper import log_async_exception
from back_end.grafana_logger_plugin.model import EventsModel

from async_hsm import Framework

log = LOLoggerClient(client_name="GrafanaLoggerService", verbose=True)


class GrafanaLoggerService(ServiceTemplate):
    def __init__(self):
        super().__init__()

    def setup_routes(self):
        self.app.router.add_route("GET", "/ws", self.websocket_handler)
        self.app.router.add_route('GET', '/stats', self.handle_stats)

    async def on_startup(self, app):
        log.info("GrafanaLoggerService is starting up")

        self.app["config"] = self.app["farm"].config.get_glogger_plugin_config()

        self.app["websockets"] = []
        self.tasks = []
        self.socket_stats = {"ws_connections": 0, "ws_disconnections": 0, "ws_open": 0}
        self.tasks.append(asyncio.create_task(self.listener(app)))

    async def on_shutdown(self, app):
        """
        description: Cancel all tasks and close all open websocket connections
        """
        for task in self.tasks:
            task.cancel()

        for ws in self.app["websockets"]:
            await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')

        log.info("GrafanaLoggerService is shutting down")

    async def on_cleanup(self, app):
        """
        description: Close DB Connection for graceful shutdown
        """
        # SQLiteInstance.close_connection()
        # TODO: Figure out a better way to do this
        pass

    async def handle_stats(self, request):
        """
        description: Fetch server statistics from PigssController

        tags:
            -   Controller
        summary: Fetch server statistics
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns statistics
        """
        controller = request.app['farm'].controller
        result = {
            "time": time.time(),
            "ws_open": self.socket_stats["ws_open"],
            "ws_connections": self.socket_stats["ws_connections"],
            "ws_disconnections": self.socket_stats["ws_disconnections"],
            "framework": Framework.get_info(),
            "errors": [e for e in controller.error_list]
        }
        return web.json_response(result)

    @log_async_exception(log_func=log.error, stop_loop=False)
    async def websocket_handler(self, request):

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.socket_stats['ws_connections'] += 1

        if "query_params" not in ws:
            ws["query_params"] = {}

        ws["query_params"]["columns"] = self.app["config"]["sqlite"]["columns"]

        if "limit" not in ws["query_params"]:
            ws["query_params"]["limit"] = self.app["config"]["limit"]

        if "interval" not in ws["query_params"]:
            ws["query_params"]["interval"] = self.app["config"]["interval"]

        self.app["websockets"].append(ws)

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == "CLOSE":
                    await ws.close()
                else:
                    i = self.app["websockets"].index(ws)
                    query_params = {}
                    if msg.data is not None:
                        query_params = loads(msg.data)
                    self.app["websockets"][i]['query_params'] = {**self.app["websockets"][i]['query_params'], **query_params}
            elif msg.type == WSMsgType.ERROR:
                ws.exception()
            elif msg.type == WSMsgType.CLOSE:
                self.app["websockets"].remove(ws)
                await ws.close(message="Server Shutdown Initiated from Client")

        self.app["websockets"].remove(ws)
        self.socket_stats['ws_open'] = len(self.app["websockets"])
        self.socket_stats['ws_disconnections'] += 1

        return ws

    async def get_logs(self, ws, query_params={}):
        """
        description: Returns logs as a json to caller
        params:
            query_params: dict
        returns:
            row of logs ["rowid", "ClientTimestamp", "ClientName", "LogMessage",
             "Level"]
        """
        query = None

        lologger_proxy = CmdFIFOServerProxy(f"http://localhost:{rpc_ports['logger']}", ClientName="GrafanaLoggerService")
        sqlite_path = lologger_proxy.get_sqlite_path()

        table_name = self.app["config"]["sqlite"]["table_name"]
        if len(query_params) > 0:
            query, values = EventsModel.build_sql_select_query(query_params, table_name, log)
        else:
            query = EventsModel.build_select_default(table_name, log)
        ws['query'] = query
        if query is not None:
            return EventsModel.execute_query(sqlite_path, query, values, table_name, log)

    async def send_task(self, ws, current_time):
        ws['next_run'] = current_time + \
            timedelta(seconds=ws['query_params']['interval'])
        await asyncio.sleep(ws['query_params']['interval'])

        logs = await self.get_logs(ws, ws["query_params"])
        if len(logs) > 0:
            ws["query_params"]["rowid"] = logs[-1][0]
            await ws.send_json(logs)
            await ws.drain()

    def should_send_task(self, ws, current_time):
        try:
            is_time = (ws['next_run'] <= current_time)
            if 'next_run' in ws:
                is_new_interval = current_time + timedelta(seconds=ws['query_params']['interval']) < ws['next_run']
            return is_time or is_new_interval
        except ValueError as ve:
            log.error(f"Error in should_send_task {ve}")

    @log_async_exception(log_func=log.error, stop_loop=True)
    async def listener(self, app, DEFAULT_INTERVAL=1.0):
        """
        The following code handles multiple clients connected to the server.
        It sends out the logs by reading query parameters.
        """
        while True:
            await asyncio.sleep(1)
            current_time = datetime.now()
            for ws in self.app["websockets"]:
                if 'next_run' not in ws:
                    ws['next_run'] = current_time
            try:
                if len(self.app["websockets"]) > 0:
                    asyncio.gather(*[
                        self.send_task(ws, current_time)
                        for ws in self.app["websockets"] if self.should_send_task(ws, current_time)
                    ])
            except ConnectionError as e:
                log.error(f"Error in Logger Service Listener {e}")
