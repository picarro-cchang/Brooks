import asyncio
import aiohttp
import aiohttp_cors
from aiohttp_cors.mixin import CorsViewMixin
from aiohttp_swagger import setup_swagger
from aiohttp import web
import functools
import traceback


class AdminApi:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/method1", self.method1)
        self.app.router.add_route("GET", "/method2", self.method2)

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
