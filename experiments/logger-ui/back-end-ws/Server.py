from aiohttp import web, WSMsgType
import asyncio
import aiohttp_cors
from aiohttp_swagger import setup_swagger

from experiments.common.async_helper import log_async_exception

from db import QueryParser, EventsModel

class Server:

    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/getlogs", self.get_logs)
        self.app.router.add_route("GET", "/ws", self.websocket_handler)
        self.tasks = []
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)
        self.rowid = 0
        self.current_query_params = {"limit": 20}

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

    async def get_logs(self, request):
        """
        ---
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
        parsed = query = None
        if request.query_string:
            parsed = QueryParser.parse(request.query_string)
            query = EventsModel.build_sql_select_query(parsed)
            self.current_query_params = parsed
        else:
            query = EventsModel.build_select_default()
        logs = EventsModel.execute_query(query)
        # print(logs[0][0])
        self.rowid = logs[-1][0]
        return web.json_response(logs)


    async def get_logs_by_last_accessed_rowid(self):
        logs = []
        self.current_query_params['rowid'] = self.rowid
        query = EventsModel.build_sql_select_query(self.current_query_params)
        # print(self.rowid, query)
        logs = EventsModel.execute_query(query)
        if len(logs) > 0:
            self.rowid = logs[-1][0]
        return logs

    @log_async_exception(stop_loop=True)
    async def websocket_handler(self, request):
        """
        Web socket handler for receiving information from connected client(s)
        """
        print("Inside Websocket handler")
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        request.app['websockets'].append(ws)
        async for msg in ws:
            print(f"From websocket: {msg}")
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close(message="Server Shutdown Initiated from Client")
                    # request.app['websockets'].remove(ws)
                else:
                    # Need to do something with the data here
                    print("Data received", msg.data)
                    # await self.app['send_queue'].put("We will send new data")
            elif msg.type == WSMsgType.ERROR:
                # request.app['websockets'].remove(ws)
                print("ws connection failed with exception %s ", ws.exception())
        print('websocket connection closed')
        request.app['websockets'].remove(ws)
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
            # await self.app['send_queue'].put(await self.get_logs())
            # Get all the logs in a msg object and send as json
            # logs = await app['send_queue'].get()
            logs = None
            # print("Logs before:", logs)
            # print('---> Check', self.app['websockets'])
            if len(self.app['websockets']) > 0:
                # print('---> Check', self.app['websockets'])
                logs = await self.get_logs_by_last_accessed_rowid()
            await asyncio.sleep(1.0)
            # print(f"websocket_send_task: {logs}, {len(app['websockets'])}")

            for ws in app['websockets']:
                try:
                    if logs is not None:
                        await ws.send_json(logs)
                    await ws.drain()
                except ConnectionError as e:
                    print(f"{e} in websocket_send_task")
