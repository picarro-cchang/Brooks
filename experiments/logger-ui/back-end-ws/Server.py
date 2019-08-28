from aiohttp import web, WSMsgType
import asyncio
import aiohttp_cors
from aiohttp_swagger import setup_swagger
from json import loads as json_to_dict

from experiments.common.async_helper import log_async_exception

from db import QueryParser, EventsModel


class Server:

    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/getlogs", self.get_logs_handler)
        self.app.router.add_route("GET", "/ws", self.websocket_handler)
        self.tasks = []
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)
        self.rowid = 0
        self.current_query_params = {"limit": 20}
        self.counter = 0

    async def on_startup(self, app):
        app['websockets'] = []
        self.tasks.append(asyncio.create_task(self.websocket_send_task(app)))

    async def on_shutdown(self, app):
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Close DB Connection

        # Close web socket connections
        for ws in app['websockets']:
            await ws.close(message="Server Shutdown")

    async def on_cleanup(self, app):
        print("TODO: on_cleanup")
        pass

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
        parsed =  None
        if request.query_string:
            parsed = QueryParser.parse(request.query_string)
        return web.json_response(await self.get_logs(parsed))

    async def get_logs(self, query_params={}):
        """
        Returns logs as a json to caller
        """
        query = None
        if len(query_params) > 0:
            query = EventsModel.build_sql_select_query(query_params)
        else:
            query = EventsModel.build_select_default()
        return EventsModel.execute_query(query)

    @classmethod
    def print_query_params(cls, query_params):
        print("--> Check Query Params", query_params)

    @log_async_exception(stop_loop=True)
    async def websocket_handler(self, request):
        """
        Web socket handler for receiving information from connected client(s)
        """
        print("Inside Websocket handler")
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        ws["counter"] = self.counter
        self.counter += 1
        request.app['websockets'].append(ws)
        async for msg in ws:
            print(f"From websocket: {msg}")
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close(message="Server Shutdown Initiated from Client")
                else:
                    i = request.app['websockets'].index(ws)
                    request.app['websockets'][i]["query_params"] = json_to_dict(msg.data)
            elif msg.type == WSMsgType.ERROR:
                request.app['websockets'].remove(ws)
                print("ws connection failed with exception %s ", ws.exception())
        print('websocket connection closed')
        return ws

    @log_async_exception(stop_loop=True)
    async def websocket_send_task(self, app):
        """
        The following code handles multiple clients connected to the server. A single send task is
         used to send queue entries to all connected clients so that their UIs remain consistent.
         Commands from all clients go into a single receive queue so that any GUI may be used to
         affect the system.
        """
        while True:

            await asyncio.sleep(1.0)
            if len(self.app['websockets']) > 0:
                for i, ws in enumerate(app['websockets']):
                    try:
                        if "query_params" not in ws:
                            ws["query_params"] = {}
                        logs = await self.get_logs(ws["query_params"])
                        if len(logs) > 0:
                            ws["query_params"]["rowid"] = logs[-1][0]
                            await ws.send_json(logs)
                            await ws.drain()
                    except ConnectionError as e:
                        print(f"{e} in websocket_send_task")
