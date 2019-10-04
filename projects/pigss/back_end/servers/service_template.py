#!/usr/bin/env python3
#
# FILE:
#   service_template.py
#
# DESCRIPTION:
#   Base class for an async http server with exception handling
#    middleware that returns a text description of the error and
#    traceback to the requester, and optionally publishes the exception
#    as an Event of type Signal.ERROR to the async_hsm framework.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-Oct-2019  sze Initial check in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
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
                            "exc": e,
                            "traceback": traceback.format_exc(),
                            "location": self.__class__.__name__,
                            "request": request.url
                        }))
            raise HTTPInternalServerError(text=f"Error handling request {request.path_qs}\n{traceback.format_exc()}")
        return resp

    # Optionally override these handler coroutines in a subclass
    async def on_startup(self, app):
        return

    async def on_shutdown(self, app):
        return

    async def on_cleanup(self, app):
        return
