from aiohttp import web, WSMsgType, WSCloseCode
import asyncio
from json import loads as json_to_dict
from datetime import datetime, timedelta

from db_connection import DBInstance
from db import QueryParser, EventsModel

from experiments.common.async_helper import log_async_exception


class LoggerServer:
    """
    """

    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/ws", self.websocket_handler)
        self.app.router.add_route("GET", "/getlogs", self.get_logs_handler)

        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)

        self.app.websockets = []
        self.tasks = []

    async def on_startup(self, app):
        """
        description: Start the websocket send task
        """
        self.tasks.append(asyncio.create_task(self.listener(app)))

    async def on_shutdown(self, app):
        """
        description: Cancel all tasks and close all open websocket connections
        """
        for task in self.tasks:
            task.cancel()

        for ws in self.app.websockets:
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

    @log_async_exception(stop_loop=True)
    async def websocket_handler(self, request):

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        ws['query_params'] = {'interval': 3, 'limit': 20}

        self.app.websockets.append(ws)

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == "close":
                    await ws.close()
                else:
                    i = self.app.websockets.index(ws)
                    query_params = json_to_dict(msg.data)
                    self.app.websockets[i]['query_params'] = {
                        **self.app.websockets[i]['query_params'],
                        **query_params
                    }
                    print(
                        f"query_params {self.app.websockets[i]['query_params']}")
            elif msg.type == WSMsgType.ERROR:
                ws.exception()
            elif msg.type == WSMsgType.CLOSE:
                print("Wbsocket connection closed")
                self.app.websockets.remove(ws)
                await ws.close(message="Server Shutdown Initiated from Client")

        print("websocket connection closed")
        self.app.websockets.remove(ws)

        return ws

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

    async def send_task(self, ws, current_time):
        print(f"sleeping for {ws['query_params']['interval']}")
        ws['next_run'] = current_time + \
            timedelta(seconds=ws['query_params']['interval'])
        await asyncio.sleep(ws['query_params']['interval'])
        print("inside send task")
        
        logs = await self.get_logs(ws, ws["query_params"])
        await ws.send_json(logs)
        await ws.drain()

    def should_send_task(self, ws, current_time):
        is_time = (ws['next_run'] <= current_time)
        is_new_interval = current_time + \
            timedelta(seconds=ws['query_params']['interval']) < ws['next_run']
        return is_time or is_new_interval

    @log_async_exception(stop_loop=True)
    async def listener(self, app, DEFAULT_INTERVAL=1.0):
        """
        The following code handles multiple clients connected to the server. It sends
        out the logs by reading query parameters.
        """
        while True:
            await asyncio.sleep(1)
            print(".", end="")
            print(f"{len(self.app.websockets)}", end=" ")
            current_time = datetime.now()

            for ws in self.app.websockets:
                interval = ws['query_params']['interval']
                if 'next_run' not in ws:
                    ws['next_run'] = current_time
            try:
                asyncio.gather(*[self.send_task(ws, current_time)
                                 for ws in self.app.websockets if self.should_send_task(ws, current_time)])
            except ConnectionError as e:
                print(f"{e} in listener")
