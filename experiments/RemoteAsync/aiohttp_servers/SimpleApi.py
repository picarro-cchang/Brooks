from aiohttp import web


class SimpleApi:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/api1", self.api1)
        self.app.router.add_route("GET", "/api2", self.api2)
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)

    async def on_startup(self, app):
        print("SimpleApi server is starting up")

    async def on_shutdown(self, app):
        print("SimpleApi server is shutting down")

    async def api1(self, request):
        """
        ---
        description: Sample API method 1

        tags:
            -   simple
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
            -   simple
        summary: Sample API method 2
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.json_response({"message": f"Hello from simple method api2 where data is {request.app['data']}"})
