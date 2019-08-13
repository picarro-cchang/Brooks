import asyncio
import time

from aiohttp import web

from async_hsm import Event, Framework, Signal
from experiments.common.async_helper import log_async_exception
from experiments.LOLogger.LOLoggerClient import LOLoggerClient

log = LOLoggerClient(client_name="ControllerService", verbose=True)


class ControllerService:
    def __init__(self):
        self.tasks = []
        self.app = web.Application()
        self.app.router.add_route('POST', '/event', self.handle_event)
        self.app.router.add_route('GET', '/modal_info', self.handle_modal_info)
        self.app.router.add_route('GET', '/plan', self.handle_plan)
        self.app.router.add_route('GET', '/stats', self.handle_stats)
        self.app.router.add_route('GET', '/uistatus', self.handle_uistatus)
        self.app.router.add_route('GET', '/ws', self.websocket_handler)
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)
        self.app['websockets'] = []
        self.socket_stats = {"ws_connections": 0, "ws_disconnections": 0, "ws_open": 0}

    @log_async_exception(log_func=log.error, stop_loop=True)
    async def websocket_send_task(self, app):
        """
        The following code handles multiple clients connected to the server. A single send task is
         used to send queue entries to all connected clients so that their UIs remain consistent.
         Commands from all clients go into a single receive queue so that any GUI may be used to
         affect the system.
        """
        farm = app['farm']
        while True:
            msg = await farm.send_queue.get()
            # print(f"Websocket send: {msg}")
            for ws in app['websockets']:
                await ws.send_str(msg)

    async def on_startup(self, app):
        self.tasks.append(asyncio.create_task(self.websocket_send_task(app)))

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        for ws in app['websockets']:
            await ws.close(code=1001, message='Server shutdown')

    async def on_cleanup(self, app):
        print("ControllerService is cleaning up")

    async def handle_event(self, request):
        """
        ---
        description: Publishes specified event to the AHSM framework

        tags:
            -   Controller
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
        body = await request.json()
        log.info(f"Handling /event: {body}")
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
        description: Fetch UI modal info from PigssController

        tags:
            -   Controller
        summary: fetch UI modal info
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns UI modal info
        """
        controller = request.app['farm'].controller
        return web.json_response(controller.get_modal_info())

    async def handle_plan(self, request):
        """
        ---
        description: fetch plan

        tags:
            -   Controller
        summary: fetch UI plan
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns plan info
        """
        controller = request.app['farm'].controller
        controller.get_plan_filenames()
        return web.json_response(controller.get_plan())

    async def handle_stats(self, request):
        """
        ---
        description: Fetch server statistics from PigssController

        tags:
            -   Controller
        summary: Fetch server statistics
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns statistics
        """
        controller = request.app['farm'].controller
        result = {
            "time": time.time(),
            "ws_open": self.socket_stats["ws_open"],
            "ws_connections": self.socket_stats["ws_connections"],
            "ws_disconnections": self.socket_stats["ws_disconnections"],
            "framework": Framework.get_info(),
            "errors": [e for e in controller.error_list]
        }
        return web.json_response(result)

    async def handle_uistatus(self, request):
        """
        ---
        description: Fetch status of UI elements from PigssController

        tags:
            -   Controller
        summary: fetch UI status
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation. Returns status info
        """
        controller = request.app['farm'].controller
        return web.json_response(controller.get_status())

    async def websocket_handler(self, request):
        """
        Web socket handler for receiving information from connected client(s)
        """
        farm = request.app['farm']
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.socket_stats['ws_connections'] += 1
        request.app['websockets'].append(ws)
        self.socket_stats['ws_open'] = len(request.app['websockets'])
        async for msg in ws:
            # print(f"Websocket receive: {msg}")
            await farm.receive_queue.put(msg.data)
        request.app['websockets'].remove(ws)
        self.socket_stats['ws_open'] = len(request.app['websockets'])
        self.socket_stats['ws_disconnections'] += 1
        return ws
