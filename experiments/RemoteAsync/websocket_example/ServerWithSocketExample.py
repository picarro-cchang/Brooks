import asyncio

import aiohttp_cors
from aiohttp import web
from aiohttp_swagger import setup_swagger

from experiments.common.async_helper import log_async_exception
from SimpleApi import SimpleApi
from ApiWithWebsocket import ApiWithWebsocket


class Server:
    def __init__(self, port, addr='0.0.0.0', data="unspecified"):
        self.tasks = []
        self.app = None
        self.runner = None
        self.port = port
        self.addr = addr
        self.data = data
        self.ws_send_queue = asyncio.Queue(100)

    async def on_startup(self, app):
        self.tasks.append(asyncio.create_task(self.dotty()))
        print("Top level server is starting up")

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        print("Top level server is shutting down")

    async def on_cleanup(self, app):
        print("Top level server is cleaning up")

    @log_async_exception(stop_loop=True)
    async def dotty(self):
        i = 0
        while True:
            await asyncio.sleep(1.0)
            await self.ws_send_queue.put(f"Hello {i} via websocket")
            i += 1
            print(".", end="", flush=True)

    @log_async_exception(stop_loop=True)
    async def server_init(self):
        self.app = web.Application()
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)

        self.app['data'] = self.data
        cors = aiohttp_cors.setup(
            self.app, defaults={"*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )})

        simple = SimpleApi()
        simple.app['data'] = self.data
        self.app.add_subapp("/simple/", simple.app)

        apiWithSocket = ApiWithWebsocket()
        apiWithSocket.app['data'] = self.data
        apiWithSocket.app['send_queue'] = self.ws_send_queue
        self.app.add_subapp("/withSocket/", apiWithSocket.app)

        setup_swagger(self.app)

        for route in self.app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)
        await site.start()
        print(f"======== Running on http://{site._host}:{site._port} ========")

    async def startup(self):
        self.tasks.append(asyncio.create_task(self.server_init()))


if __name__ == "__main__":
    service1 = Server(port=8004, data="foo")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(service1.startup()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Stop server begin')
    finally:
        loop.run_until_complete(asyncio.gather(service1.runner.cleanup()))
        loop.close()
    print('Stop server end')
