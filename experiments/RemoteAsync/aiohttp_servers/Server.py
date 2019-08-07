import asyncio
import aiohttp_cors
from aiohttp_cors.mixin import CorsViewMixin
from aiohttp_swagger import setup_swagger
from aiohttp import web
# Can replace AdminApiClass by AdminApiSimple
from SimpleApi import SimpleApi
from AdminApiClass import AdminApi
from aiohttp_network_settings_app import RackNetworkSettingsServer
import functools
import traceback


def exception(coroutine):
    """
    A decorator that wraps the passed in co-routine and logs 
    exceptions should one occur
    """

    @functools.wraps(coroutine)
    async def wrapper(*args, **kwargs):
        try:
            await coroutine(*args, **kwargs)
        except:
            # log the exception and stop everything
            print(traceback.format_exc())
            print(
                "Stopping event loop due to unexpected exception in coroutine")
            # re-raise the exception
            asyncio.get_event_loop().stop()
            raise

    return wrapper


class Server:
    def __init__(self, port, addr='0.0.0.0', data="unspecified"):
        self.tasks = []
        self.app = None
        self.runner = None
        self.port = port
        self.addr = addr
        self.data = data

    async def on_startup(self, app):
        print("Top level server is starting up")

    async def on_shutdown(self, app):
        print("Top level server is shutting down")

    @exception
    async def server_init(self):
        self.app = web.Application()
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)

        self.app['data'] = self.data
        cors = aiohttp_cors.setup(self.app,
                                  defaults={
                                      "*":
                                      aiohttp_cors.ResourceOptions(
                                          allow_credentials=True,
                                          expose_headers="*",
                                          allow_headers="*",
                                      )
                                  })

        simple = SimpleApi()
        simple.app['data'] = self.data
        self.app.add_subapp("/simple/", simple.app)

        admin = AdminApi()
        admin.app['data'] = self.data
        self.app.add_subapp("/admin/", admin.app)

        network = RackNetworkSettingsServer()
        network.app['data'] = self.data
        self.app.add_subapp("/network/", network.app)

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
    service2 = Server(port=8005, data="bar")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(service1.startup(), service2.startup()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Stop server begin')
    finally:
        loop.run_until_complete(
            asyncio.gather(service1.runner.cleanup(), service2.runner.cleanup()))
        loop.close()
    print('Stop server end')
