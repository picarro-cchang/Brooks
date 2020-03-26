#!/usr/bin/env python3
""" Provides an API for sending logs to grafana logger plugin using websockets
"""

import asyncio
import time
import datetime
from json import loads
from urllib.parse import parse_qs
from traceback import format_exc
from calendar import monthrange
from sqlite3 import OperationalError

from aiohttp import web, WSMsgType, WSCloseCode
import click

from back_end.lologger.lologger_client import LOLoggerClient
from common.CmdFIFO import CmdFIFOServerProxy
from common.rpc_ports import rpc_ports
from back_end.servers.service_template import ServiceTemplate
from common.async_helper import log_async_exception
from back_end.grafana_logger_plugin.model import EventsModel

from async_hsm import Framework

log = LOLoggerClient(client_name="GrafanaLoggerService", verbose=True)


class GrafanaLoggerService(ServiceTemplate):
    def __init__(self, farm=None, lologger_proxy=None, log=None):
        super().__init__()
        self.app['farm'] = farm
        self.lologger_proxy = lologger_proxy
        self.log = log

        # This would not be required once PigssRunner is modified to pass these Objects
        if self.lologger_proxy is None:
            self.lologger_proxy = CmdFIFOServerProxy(f"http://localhost:{rpc_ports['logger']}", ClientName="GrafanaLoggerService")
        if self.log is None:
            self.log = LOLoggerClient(client_name="GrafanaLoggerService", verbose=True)

    def setup_routes(self):
        self.app.router.add_route('GET', '/ping', self.handle_ping)
        self.app.router.add_route('GET', '/ws', self.websocket_handler)
        self.app.router.add_route('GET', '/stats', self.handle_stats)
        self.app.router.add_route('GET', '/getlogs', self.handle_getlogs)
        self.app.router.add_route('POST', '/writelog', self.handle_write_log)

    async def on_startup(self, app):
        self.log.debug("GrafanaLoggerService is starting up")
        self.app["config"] = self.app["farm"].config.get_glogger_plugin_config()
        self.app["websockets"] = []
        self.tasks = []
        self.sqlite_path = None
        self.socket_stats = {"ws_connections": 0,
                             "ws_disconnections": 0, "ws_open": 0}
        self.tasks.append(asyncio.create_task(self.set_latest_db(app)))
        self.tasks.append(asyncio.create_task(self.listener(app)))

    async def on_shutdown(self, app):
        """
        description: Cancel all tasks and close all open websocket connections
        """
        for task in self.tasks:
            task.cancel()

        for ws in app["websockets"]:
            await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')

        self.log.debug("GrafanaLoggerService is shutting down")

    async def on_cleanup(self, app):
        """
        description: Close DB Connection for graceful shutdown
        """
        EventsModel.close_connection()

    async def handle_ping(self, request):
        """ Handle ping-pong messages from client
        """
        return web.Response(text="OK")

    async def handle_stats(self, request):
        """
        description: Fetch server statistics from GrafanaLoggerServer

        tags:
            -   Grafana Logger
        summary: Fetch server statistics
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation returns statistics
        """
        controller = request.app['farm'].controller
        result = {
            "time": time.time(),
            "ws_open": self.socket_stats["ws_open"],
            "ws_connections": self.socket_stats["ws_connections"],
            "ws_disconnections": self.socket_stats["ws_disconnections"]
        }
        return web.json_response(result)

    def get_latest_db(self):
        """ Fetches latest db file being written into by lologger.
        """
        return self.lologger_proxy.get_sqlite_path()

    async def set_latest_db(self, app):
        """ LoLogger creates new sqlite file beginning of a month. This method will ask lologger for latest db file once every day.
        """
        while True:
            current_date = datetime.datetime.now()
            last_date = monthrange(current_date.year, current_date.month)[1]
            tomorrow = current_date + datetime.timedelta(days=1)
            seconds_till_midnight = (datetime.datetime.combine(tomorrow, datetime.time.min) - current_date).seconds + 1
            await asyncio.sleep(seconds_till_midnight)

            try:
                current_sqlite_path = self.get_latest_db()
            except Exception as ex:
                # ignore exceptions while trying to fetch new database file
                log.debug(
                    f"Exception occurred while fetching latest db {ex}")
            if self.sqlite_path is not None and self.sqlite_path != current_sqlite_path:
                self.sqlite_path = current_sqlite_path

                # Reset all websocket connections to use newly created database file
                for ws in self.app["websockets"]:
                    ws["query_params"]["reset"] = True
                    await ws.send_json({"type": "RESET"})

    def set_predefined_config(self):
        self.sqlite_path = self.get_latest_db()
        query_dict = {}
        query_dict["columns"] = self.app["config"]["sqlite"]["columns"]
        query_dict["limit"] = self.app["config"]["limit"]
        query_dict["interval"] = self.app["config"]["interval"]
        query_dict["level"] = self.app["config"]["level"]
        query_dict["reset"] = False
        return query_dict

    async def get_logs(self, query_params):
        """
        description: Returns logs as a json to caller
        params:
            query_params: dict
        returns:
            row of logs ["rowid", "ClientTimestamp", "ClientName", "LogMessage",
             "Level"]
        """
        try:
            query, values = EventsModel.build_sql_select_query(query_params, self.app["config"]["sqlite"]["table_name"], self.log)
            if query is None or values is None:
                return None
            if __debug__:
                print(
                    f"\nFile: {self.sqlite_path} , \nQueryParams: {query_params}, \nWS: {len(self.app['websockets'])}\n")
            return EventsModel.execute_query(self.sqlite_path, query, values, self.app["config"]["sqlite"]["table_name"], self.log)
        except TypeError as te:
            self.log.error(f"Error in GrafanaLoggerService {te}")
            self.log.debug(f"Error in GrafanaLoggerService {te} {format_exc()}")
        except OperationalError:
            self.log.debug(f"Unable to process query Query: {query} Values: {values}")
        return None

    async def handle_getlogs(self, request):
        """
        description: Fetch Logs from database

        tags:
            -   Grafana Logger
        summary: Fetch server statistics
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation returns logs
        """
        parsed_query_params = parse_qs(request.query_string)
        query_params = {}
        for key, val in parsed_query_params.items():
            if key == 'level':
                query_params[key] = val
            elif len(val) == 1:
                query_params[key] = int(val[0])
        predefined_params = self.set_predefined_config()
        query_params = {**predefined_params, **query_params}
        logs = await self.get_logs(query_params)
        return web.json_response(logs) if logs is not None else web.json_response({"message":"Error in fetching logs."})

    @log_async_exception(log_func=log.error, stop_loop=False, publish_terminate=False)
    async def websocket_handler(self, request):
        """
        description: Websocket communication for fetching logs from GrafanaLoggerServer

        tags:
            -   Grafana Logger
        summary: Fetch server statistics
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation returns logs in websocket messages
        """

        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.socket_stats['ws_connections'] += 1

        if "query_params" not in ws:
            ws["query_params"] = {}
        predefined_params = self.set_predefined_config()
        ws["query_params"] = {**predefined_params, **ws["query_params"]}
        self.app["websockets"].append(ws)
        self.socket_stats["ws_open"] = len(self.app["websockets"])
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data == "CLOSE":
                        await ws.close()
                    else:
                        i = self.app["websockets"].index(ws)
                        query_params = ws["query_params"]
                        if msg.data is not None:
                            query_params = loads(msg.data)
                            self.app["websockets"][i]['query_params'] = {
                                **self.app["websockets"][i]['query_params'],
                                **query_params
                            }
                elif msg.type == WSMsgType.ERROR:
                    ws.exception()
                elif msg.type == WSMsgType.CLOSE:
                    self.log.warning(message="Client terminated websocket connection.")
                    self.app["websockets"].remove(ws)
                    await ws.close(code=1000, message="Client terminated websocket connection.")
        except asyncio.CancelledError:
            self.log.error("Web socket disconnection caused coroutine cancellation in handler.")
            self.log.debug(f"Web socket disconnection caused coroutine cancellation in handler.\n{format_exc()}")
        finally:
            self.app["websockets"].remove(ws)
            self.socket_stats['ws_open'] = len(self.app["websockets"])
            self.socket_stats['ws_disconnections'] += 1
            return ws

    async def send_task(self, ws, current_time):
        ws['next_run'] = current_time + \
            datetime.timedelta(seconds=ws['query_params']['interval'])
        await asyncio.sleep(ws['query_params']['interval'])

        # Check if database changed, and query needs to reset
        if ws["query_params"]["reset"]:
            ws["query_params"]["rowid"] = -1
            ws["query_params"]["reset"] = False

        logs = await self.get_logs(ws["query_params"])
        if logs is not None and len(logs) > 0:
            ws["query_params"]["rowid"] = logs[-1][0]
            await ws.send_json({"type": "LOGS", "logs": logs})
            await ws.drain()

    def should_send_task(self, ws, current_time):
        try:
            is_time = (ws['next_run'] <= current_time)
            if 'next_run' in ws:
                is_new_interval = current_time + \
                    datetime.timedelta(seconds=ws['query_params']['interval']) < ws['next_run']
            return is_time or is_new_interval
        except ValueError as ve:
            self.log.error(f"Error in should_send_task {ve}")

    @log_async_exception(log_func=log.error, publish_terminate=False)
    async def listener(self, app):
        """
        The following code handles multiple clients connected to the server.
        It sends out the logs by reading query parameters.
        """
        while True:
            await asyncio.sleep(1)
            current_time = datetime.datetime.now()
            for ws in self.app["websockets"]:
                if 'next_run' not in ws:
                    ws['next_run'] = current_time
            try:
                if len(self.app["websockets"]) > 0:
                    asyncio.gather(*[
                        self.send_task(ws, current_time)
                        for ws in self.app["websockets"] if self.should_send_task(ws, current_time)
                    ],
                        return_exceptions=True)
            except ConnectionError:
                self.log.error(f"Error in Logger Service Listener \n{format_exc()}")

    async def handle_write_log(self, request):
        """
        description: Write log in Event table
        tags:
            -   Grafana Logger
        summary: Write log in Event table
        responses:
            "200":
                description: successful operation returns True/False
        """
        body = await request.json()
        message = level = None
        try:
            message = body.get("message")
            level = int(body.get("level"))
        except TypeError:
            self.log.debug(format_exc())
        except ValueError:
            self.log.debug(format_exc())
        if level is None or message is None or level not in range(10, 50, 10):
            return web.json_response({
                "text": "Invalid input parameters",
                "status": 200
            })

        self.log.Log(message, level)
        return web.json_response({
            "text": "Message sent for logging.",
            "status": 200
        })
