from aiohttp import web


class AdminApi:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/method1", self.method1)
        self.app.router.add_route("GET", "/method2", self.method2)
        self.app.on_shutdown.append(self.on_shutdown)

    async def method1(self, request):
        """
        ---
        description: administrative method

        tags:
            -   admin (nested)
        summary: administrative method
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.json_response({"message": f"Hello from administrative method 1, data is {request.app['data']}"})

    async def method2(self, request):
        """
        ---
        description: administrative method

        tags:
            -   admin (nested)
        summary: administrative method
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.json_response({"message": f"Hello from administrative method 2, data is {request.app['data']}"})

    async def on_shutdown(self, app):
        print("AdminApi server is shutting down")
