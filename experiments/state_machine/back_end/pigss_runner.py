import asyncio
import time

import aiohttp
import aiohttp_cors
import attr
from aiohttp import web
from aiohttp_swagger import setup_swagger

from async_hsm import Event, Framework, Signal
from pigss_farm import PigssFarm


@attr.s
class HttpHandlers:
    farm = attr.ib(factory=PigssFarm)
    app = attr.ib(None)
    runner = attr.ib(None)
    tasks = attr.ib(factory=list)
    socket_stats = attr.ib(factory=lambda:{"ws_connections": 0, "ws_disconnections": 0, "ws_open": 0})

    async def handle(self, request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    async def handle_event(self, request):
        """
        ---
        description: issues an event to the HSM

        tags:
            -   diagnostics
        summary: Issues an event
        consumes:
            -   application/json
        produces:
            -   text/plain
        parameters:
            -   in: body
                name: event
                description: Specify event
                required: true
                schema:
                    type: object
                    properties:
                        signal:
                            type:   string
                            required:   true
                        value:
                            type:   object
                            required:   false
        responses:
            "200":
                description: successful operation. Returns "OK"
            "400":
                description: unrecognized event."
        """
        print(f"Post {request}")
        body = await request.json()
        payload = body.get("value", None)
        try:
            event = Event(getattr(Signal, body["signal"]), payload)
            Framework.publish(event)
            return web.Response(text="OK")
        except KeyError:
            raise web.HTTPBadRequest()

    async def handle_modal_info(self, request):
        """
        ---
        description: fetch UI modal info

        tags:
            -   diagnostics
        summary: fetch UI modal info
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns UI modal info
        """
        controller = self.farm.controller
        return web.json_response(controller.get_modal_info())

    async def handle_plan(self, request):
        """
        ---
        description: fetch plan

        tags:
            -   diagnostics
        summary: fetch UI plan
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns plan info
        """
        controller = self.farm.controller
        return web.json_response(controller.get_plan())

    async def handle_uistatus(self, request):
        """
        ---
        description: fetch status of UI elements

        tags:
            -   diagnostics
        summary: fetch UI status
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns status info
        """
        controller = self.farm.controller
        return web.json_response(controller.get_status())

    async def handle_stats(self, request):
        """
        ---
        description: fetch server statistics for diagnostics

        tags:
            -   diagnostics
        summary: fetch UI status
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns statistics
        """
        controller = self.farm.controller
        result = {
            "time": time.time(),
            "ws_open": self.socket_stats["ws_open"],
            "ws_connections": self.socket_stats["ws_connections"],
            "ws_disconnections": self.socket_stats["ws_disconnections"],
            "framework": Framework.get_info(),
            "errors": [e for e in controller.error_list]
        }
        return web.json_response(result)

    # The following code handles multiple clients connected
    #  to the server. A single send task is used to send
    #  queue entries to all connected clients so that their
    #  UIs remain consistent. Commands from all clients go into
    #  a single receive queue so that any GUI may be used to
    #  affect the system.

    async def websocket_send_task(self, app):
        while True:
            msg = await self.farm.send_queue.get()
            # print(f"Websocket send: {msg}")
            for ws in app['websockets']:
                await ws.send_str(msg)

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.socket_stats['ws_connections'] += 1
        request.app['websockets'].append(ws)
        self.socket_stats['ws_open'] = len(request.app['websockets'])
        async for msg in ws:
            # print(f"Websocket receive: {msg}")
            await self.farm.receive_queue.put(msg.data)
        request.app['websockets'].remove(ws)
        self.socket_stats['ws_open'] = len(request.app['websockets'])
        self.socket_stats['ws_disconnections'] += 1
        return ws

    async def server_init(self, port):
        app = web.Application()
        self.app = app
        app['websockets'] = []
        app.on_shutdown.append(self.on_shutdown)
        cors = aiohttp_cors.setup(
            app, defaults={"*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )})

        app.add_routes([
            web.get('/', self.handle),
            web.post('/event', self.handle_event),
            web.get('/uistatus', self.handle_uistatus),
            web.get('/plan', self.handle_plan),
            web.get('/modal_info', self.handle_modal_info),
            web.get('/stats', self.handle_stats),
            web.get('/ws', self.websocket_handler),
        ])
        setup_swagger(app)

        for route in app.router.routes():
            cors.add(route)

        self.tasks.append(asyncio.create_task(self.websocket_send_task(app)))

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', port)
        await site.start()
        return app

    async def on_shutdown(self, app):
        for ws in app['websockets']:
            await ws.close(code=1001, message='Server shutdown')

    async def shutdown(self):
        for task in self.tasks:
            task.cancel()
        await self.app.shutdown()
        await self.app.cleanup()
        await self.runner.cleanup()
        await self.farm.shutdown()

    async def startup(self):
        await self.farm.startup()
        self.tasks.append(asyncio.create_task(self.server_init(8000)))


if __name__ == "__main__":
    handlers = HttpHandlers()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(handlers.startup())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Stop server begin')
    finally:
        loop.run_until_complete(handlers.shutdown())
        loop.close()
    print('Stop server end')
