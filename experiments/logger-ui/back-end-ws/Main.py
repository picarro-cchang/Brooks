from aiohttp import web
import asyncio
import aiohttp_cors
from aiohttp_swagger import setup_swagger

from experiments.common.async_helper import log_async_exception

from LoggerServer import LoggerServer


class Main:

    """
    This class will create a top level server for logger application. It will
    create a top level web application, that will have a logger server as 
    subapp.
    """

    def __init__(self, port=9090, addr="0.0.0.0", identifier="Logger"):
        self.tasks = []
        self.ws_send_queue = asyncio.Queue(100)
        self.port = port
        self.addr = addr
        self.runner = None
        self.identifier = identifier
        self.ws_send_queue = asyncio.Queue(256)

    async def on_startup(self, app):
        print(f"Top Level Server is Starting Up {self.addr}:{self.port}")

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        print("Top level server is shutting down")

    async def on_cleanup(self, app):
        print("TODO: Implement cleanup")
        pass

    async def server_init(self):
        self.app = web.Application()
        self.app.on_startup.append((self.on_startup))
        self.app.on_shutdown.append((self.on_shutdown))
        self.app.on_cleanup.append((self.on_cleanup))

        cors = aiohttp_cors.setup(
            self.app, defaults={"*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )})

        api_ws_server = LoggerServer()
        api_ws_server.app['send_queue'] = self.ws_send_queue
        self.app.add_subapp("/api_ws/", api_ws_server.app)
        setup_swagger(self.app)

        for route in self.app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, host=self.addr, port=self.port)
        await site.start()
        print(f"\n>_ Running on http://{site._host}:{site._port} ...\n")

    async def startup(self):
        self.tasks.append(asyncio.create_task(self.server_init()))

    async def cleanup(self):
        self.tasks.append(asyncio.create_task(self.on_cleanup()))


if __name__ == "__main__":
    service = Main(port=8004)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(service.startup()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Stop Server Begin...")
    finally:
        loop.run_until_complete(asyncio.gather(service.runner.cleanup()))
        loop.close()
    print("Stop Server Ended")
