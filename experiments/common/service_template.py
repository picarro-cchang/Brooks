#!/usr/bin/env python3
import asyncio
import traceback

from aiohttp import web
from aiohttp.web import HTTPInternalServerError, middleware

from async_hsm import Event, Framework, Signal


class ServiceTemplate:
    def __init__(self):
        self.app = web.Application(middlewares=[self.exception_middleware])
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)
        self.setup_routes()
        self.publish_errors = True

    def setup_routes(self):
        # Must be overridden in subclass
        raise NotImplementedError

    @middleware
    async def exception_middleware(self, request, handler):
        try:
            resp = await handler(request)
        except Exception as e:
            if self.publish_errors:
                Framework.publish(
                    Event(
                        Signal.ERROR, {
                            "type": "service",
                            "exc": str(e),
                            "traceback": traceback.format_exc(),
                            "location": self.__class__.__name__,
                            "request": request.url
                        }))
            raise HTTPInternalServerError(text=f"Error handling request {request.path_qs}\n{traceback.format_exc()}")
        return resp

    async def on_startup(self, app):
        return

    async def on_shutdown(self, app):
        return

    async def on_cleanup(self, app):
        return
