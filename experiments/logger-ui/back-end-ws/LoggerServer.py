from aiohttp import web, WSMsgType, WSCloseCode
import asyncio
import aiohttp_cors
from aiohttp_swagger import setup_swagger
from json import loads as json_to_dict
import traceback
from experiments.common.async_helper import log_async_exception

from db_connection import DBInstance
from db import QueryParser, EventsModel


class LoggerServer:

    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/getlogs", self.get_logs_handler)
        self.app.router.add_route("GET", "/ws", self.websocket_handler)
        self.tasks = []
        self.websockets = []
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)

    async def on_startup(self, app):
        """
        description: Start the websocket send task
        """
        self.tasks.append(asyncio.create_task(self.websocket_send_task(app)))

    async def on_shutdown(self, app):
        """
        description: Cancel all tasks and close all open websocket connections
        """
        for task in self.tasks:
            task.cancel()

        for ws in self.websockets:
            await ws.close(code=WSCloseCode.GOING_AWAY,
                           message='Server shutdown')

    async def on_cleanup(self, app):
        """
        description: Close DB Connection for graceful shutdown
        """
        DBInstance.close_db_connection()

    async def get_logs_handler(self, request):
        """
        description: API for getting logs

        tags:
            -   HTTP GET
        summary: API for getting logs
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        parsed = None
        if request.query_string:
            parsed = QueryParser.parse(request.query_string)
        return web.json_response(await self.get_logs(parsed))

    async def get_logs(self, ws, query_params={}):
        """
        description: Returns logs as a json to caller
        params:
            query_params: dict
        returns:
            row of logs ["rowid", "ClientTimestamp", "ClientName", "LogMessage", "Level"]
        """
        print("ws here", ws)
        query = None
        if len(query_params) > 0:
            query = EventsModel.build_sql_select_query(query_params)
        else:
            query = EventsModel.build_select_default()
        print(f"\n{query}\n")
        ws['query'] = query
        if query is not None:
            return EventsModel.execute_query(query)
        # return []

    @log_async_exception(stop_loop=True)
    async def websocket_handler(self, request):
        """
        Web socket handler for receiving information from connected client(s)
        """
        print("Inside Websocket handler")

        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.append(ws)

        async for msg in ws:
            # print(f"From websocket: {msg}")
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'CLOSE':
                    print("Wbsocket connection closed")
                    self.websockets.remove(ws)
                    await ws.close(message="Server Shutdown Initiated from Client")
                else:
                    i = self.websockets.index(ws)
                    self.websockets[i]["query_params"] = json_to_dict(
                        msg.data)
            elif msg.type == WSMsgType.ERROR:
                self.websockets.remove(ws)
                print("ws connection failed with exception %s ", ws.exception())
            elif msg.type == WSMsgType.CLOSE:
                print("Wbsocket connection closed")
                self.websockets.remove(ws)
                await ws.close(message="Server Shutdown Initiated from Client")

    @log_async_exception(stop_loop=True)
    async def websocket_send_task(self, app, interval=2.0):
        """
        The following code handles multiple clients connected to the server. It sends
        out the logs by reading query parameters.
        """
        while True:
            await asyncio.sleep(interval)
            if len(self.websockets) > 0:
                print(f"Number of Open connections: {len(self.websockets)}")
                for ws in self.websockets:
                    try:
                        if "query_params" not in ws:
                            ws["query_params"] = {}
                        logs = await self.get_logs(ws, ws["query_params"])
                        if len(logs) > 0:
                            # 0th entry contains the rowid for the logs
                            ws["query_params"]["rowid"] = logs[-1][0]
                            await ws.send_json(logs)
                            await ws.drain()
                    except ConnectionError as e:
                        print(f"{e} in websocket_send_task")
