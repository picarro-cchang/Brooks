import aiohttp_cors
from aiohttp_cors.mixin import CorsViewMixin
from aiohttp import web


class MyView1(web.View, CorsViewMixin):
    async def get(self):
        """
        ---
        description: administrative method 1

        tags:
            -   admin (nested)
        summary: administrative method 1
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.json_response({"message": f"Hello from first administrative method, data is {self.request.app['data']}"})


class MyView2(web.View, CorsViewMixin):
    async def get(self):
        """
        ---
        description: administrative method 2

        tags:
            -   admin (nested)
        summary: administrative method 2
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.json_response({"message": f"Hello from second administrative method, data is {self.request.app['data']}"})


class AdminApi:
    def __init__(self):
        self.app = web.Application()
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.router.add_routes([web.view("/method1", MyView1)])
        self.app.router.add_routes([web.view("/method2", MyView2)])
        aiohttp_cors.setup(
            self.app, defaults={"*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )})

    async def on_shutdown(self, app):
        print("AdminApi server is shutting down")
