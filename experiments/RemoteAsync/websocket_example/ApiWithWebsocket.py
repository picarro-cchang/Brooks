from aiohttp import web
import aiohttp
import asyncio
from experiments.common.async_helper import log_async_exception


class ApiWithWebsocket:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/api1", self.api1)
        self.app.router.add_route("GET", "/api2", self.api2)
        self.app.router.add_route('GET', '/ws', self.websocket_handler)
        self.tasks = []
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)

    async def on_startup(self, app):
        app['websockets'] = []
        self.tasks.append(asyncio.create_task(self.websocket_send_task(app)))

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        for ws in app['websockets']:
            await ws.close(message='Server shutdown')

    async def api1(self, request):
        """
        ---
        description: Sample API method 1

        tags:
            -   withSocket
        summary: Sample API method 1
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.json_response({"message": f"Hello from simple method api1 where data is {request.app['data']}"})

    async def api2(self, request):
        """
        ---
        description: Sample API method 2

        tags:
            -   withSocket
        summary: Sample API method 2
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.json_response({"message": f"Hello from simple method api2 where data is {request.app['data']}"})

    @log_async_exception(stop_loop=True)
    async def websocket_handler(self, request):
        """
        Web socket handler for receiving information from connected client(s)
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        request.app['websockets'].append(ws)
        async for msg in ws:
            print(f"From websocket: {msg}")
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
            msg = await app['send_queue'].get()
            await asyncio.sleep(1.0)
            print(f"websocket_send_task: {msg}, {len(app['websockets'])}")
            for ws in app['websockets']:
                try:
                    await ws.send_str(msg)
                    await ws.drain()
                except ConnectionError as e:
                    print(f"{e} in websocket_send_task")
