import asyncio
import aiohttp
import aiohttp_cors
from aiohttp_swagger import setup_swagger
from aiohttp import web
import functools
import traceback

routes = web.RouteTableDef()

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
            print("Stopping event loop due to unexpected exception in coroutine")
            # re-raise the exception
            asyncio.get_event_loop().stop()
            raise
    return wrapper


class Handler:
    @routes.get("/")
    @routes.get("/{name}")
    async def handle(request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    @routes.get("/api")
    async def api(request):
        """
        ---
        description: api demo

        tags:
            -   diagnostics
        summary: fetch UI modal info
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.json_response({"message": "Hello from API"})


class SimpleApi:
    def __init__(self, port, addr='0.0.0.0'):
        self.tasks = []
        self.app = None
        self.runner = None
        self.port = port
        self.addr = addr

    @exception
    async def server_init(self):
        self.app = web.Application()
        self.app.on_shutdown.append(self.on_shutdown)
        cors = aiohttp_cors.setup(
            self.app, defaults={"*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )})

        self.app.add_routes(routes)
        setup_swagger(self.app)

        for route in self.app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)
        await site.start()
        print(f"======== Running on http://{site._host}:{site._port} ========")


    async def on_shutdown(self, app):
        return

    async def shutdown(self):
        for task in self.tasks:
            task.cancel()
        if self.runner is not None:
            await self.app.shutdown()
            await self.app.cleanup()
            await self.runner.cleanup()

    async def startup(self):
        self.tasks.append(asyncio.create_task(self.server_init()))

if __name__ == "__main__":
    service1 = SimpleApi(port=8004)
    service2 = SimpleApi(port=8005)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(service1.startup(), service2.startup()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Stop server begin')
    finally:
        loop.run_until_complete(asyncio.gather(service1.shutdown(), service2.shutdown()))
        loop.close()
    print('Stop server end')
