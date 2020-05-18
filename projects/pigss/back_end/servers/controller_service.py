#!/usr/bin/env python3
"""
Provides an API for interacting with and querying the pigss_controller
 and the pigss_error_manager state machines. It is used by the flow setup
 front-end UI to fetch the bank and button status, the plan, and modal
 messages.
"""
import asyncio
import time
from traceback import format_exc

from aiohttp import web

from async_hsm import Event, Framework, Signal
from back_end.lologger.lologger_client import LOLoggerClient
from back_end.servers.service_template import ServiceTemplate
from common.async_helper import log_async_exception

log = LOLoggerClient(client_name="ControllerService", verbose=True)


class ControllerService(ServiceTemplate):
    def __init__(self):
        super().__init__()

    def setup_routes(self):
        self.app.router.add_route('GET', '/errors', self.handle_errors)
        self.app.router.add_route('POST', '/event', self.handle_event)
        self.app.router.add_route('POST', '/auto_setup_flow', self.handle_auto_setup_flow)
        self.app.router.add_route('GET', '/modal_info', self.handle_modal_info)
        self.app.router.add_route('GET', '/plan', self.handle_plan)
        self.app.router.add_route('GET', '/stats', self.handle_stats)
        self.app.router.add_route('GET', '/uistatus', self.handle_uistatus)
        self.app.router.add_route('GET', '/ws', self.websocket_handler)

    @log_async_exception(log_func=log.error, publish_terminate=True)
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
            for ws in app['websockets']:
                try:
                    await ws.send_str(msg)
                except ConnectionError as e:
                    log.warning(f"{e} in websocket_send_task")
                    pass

    async def on_startup(self, app):
        log.debug("Controller service is starting up")
        self.tasks = []
        self.app['websockets'] = []
        self.socket_stats = {"ws_connections": 0, "ws_disconnections": 0, "ws_open": 0}
        self.tasks.append(asyncio.create_task(self.websocket_send_task(app)))

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        for ws in app['websockets']:
            await ws.close(code=1001, message='Server shutdown')
        log.debug("Controller service is shutting down")

    async def handle_errors(self, request):
        """
        description: Retrieve recent errors from PigssErrorManager

        tags:
            -   Controller
        summary: Retrieve recent errors from PigssErrorManager
        produces:
            -   text/plain
        responses:
            "200":
                description: successful operation."
        """
        farm = request.app['farm']
        errors = farm.pigss_error_manager.error_deque
        return web.Response(text="\n\n".join(errors))

    async def handle_auto_setup_flow(self, request):
        """
        description: Performs channel identify and optionally starts plan from a file

        tags:
            -   Controller
        summary: Performs channel identify and optionally starts plan from a file
        consumes:
            -   application/json
        produces:
            -   text/plain
        parameters:
            -   in: body
                name: plan_filename
                description: Specify plan filename (without extension) in quotes
                required: false
                schema:
                    type: string

        responses:
            "200":
                description: successful operation.
        """
        body = await request.json()
        if not body:  # Missing argument gives an empty dictionary
            body = None
        log.debug(f"Handling /auto_setup_flow: {body}")
        plan_filename = body

        controller = request.app['farm'].controller
        try:
            result = await controller.auto_setup_flow(plan_filename)
            return web.Response(text=result)
        except Exception as e:  # noqa
            # Report unexpected exception with traceback back to initiator
            return web.Response(text=f"{e}\n{format_exc()}")

    async def handle_event(self, request):
        """
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
        log.debug(f"Handling /event: {body}")
        payload = body.get("value", None)
        try:
            event = Event(getattr(Signal, body["signal"]), payload)
            Framework.publish(event)
            return web.Response(text="OK")
        except KeyError:
            raise web.HTTPBadRequest()

    async def handle_modal_info(self, request):
        """
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
        await controller.get_available_plans()
        return web.json_response(controller.get_plan())

    async def handle_stats(self, request):
        """
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
        try:
            async for msg in ws:
                if msg.data == "CLOSE":
                    await ws.close()
                else:
                    farm.receive_queue.put_nowait(msg.data)
        except asyncio.queues.QueueFull:
            log.debug(f"Farm receive queue full.\n{format_exc()}")
            log.error(f"Recieve Queue Full. Please Report.")
        except asyncio.CancelledError:
            log.error("Web socket disconnection caused coroutine cancellation in handler.")
            log.debug(f"Web socket disconnection caused coroutine cancellation in handler.\n{format_exc()}")
        request.app['websockets'].remove(ws)
        self.socket_stats['ws_open'] = len(request.app['websockets'])
        self.socket_stats['ws_disconnections'] += 1
        return ws
