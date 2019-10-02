# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import logging
import datetime

import asyncio
import aiohttp
import aiohttp_cors
from aiohttp_swagger import setup_swagger
from aiohttp import web
import functools
import traceback

my_path = os.path.dirname(os.path.abspath(__file__))


def exception(coroutine):
    """
    A decorator that wraps the passed in co-routine logging 
    an exception and stopping the event loop if one should occur
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


class AsyncWrapper:
    """Returns asynchronous version of a method by wrapping it in an executor"""

    def __init__(self, proxy):
        self.proxy = proxy

    def __getattr__(self, attr):
        return AsyncWrapper(getattr(self.proxy, attr))

    async def __call__(self, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(None, self.proxy, *args, **kwargs)


class RequestObj:
    def __init__(self, data):
        self.data = data

    def get_json(self):
        return self.data


class RackNetworkSettingsServer:
    def __init__(self, port, addr='0.0.0.0'):
        self.tasks = []
        self.app = None
        self.runner = None
        self.port = port
        self.addr = addr
        self.afuncs = AsyncWrapper(SyncInterface())

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

        self.app.add_routes([
            web.get('/get_instruments', self.end_point_get_instruments),
            web.post('/apply_changes', self.end_point_apply_changes),
            web.post('/destroy_instrument', self.end_point_destroy_instrument),
            web.post('/restart_instrument', self.end_point_restart_instrument),
            web.post('/resolve_warning', self.end_point_resolve_warning),
            web.get('/get_network_settings', self.end_point_get_network_settings),
            web.post('/set_network_settings', self.end_point_set_network_settings)
        ])
        setup_swagger(self.app)

        for route in self.app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)
        await site.start()
        print(f"======== Running on http://{site._host}:{site._port} ========")

    async def end_point_get_instruments(self, request):
        """
        ---
        description: get data about connected instruments

        tags:
            -   diagnostics
        summary: get data about connected instruments
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.Response(text=await self.afuncs.get_instruments())

    async def end_point_apply_changes(self, request):
        data = await request.json()
        return web.Response(text=await self.afuncs.apply_changes(RequestObj(data)))

    async def end_point_destroy_instrument(self, request):
        """
        ---
        description: destroys instrument specified by ip

        tags:
            -   diagnostics
        summary: destroys an instrument
        consumes:
            -   application/json
        produces:
            -   text/plain
        parameters:
            -   in: body
                name: data
                description: Specify data
                required: true
                schema:
                    type: object
                    properties:
                        ip:
                            type:   string
                            required:   true
        responses:
            "200":
                description: successful operation
            "400":
                description: error."
        """
        data = await request.json()
        return web.Response(text=await self.afuncs.destroy_instrument(RequestObj(data)))

    async def end_point_restart_instrument(self, request):
        """
        ---
        description: restarts instrument specified by ip

        tags:
            -   diagnostics
        summary: restarts an instrument
        consumes:
            -   application/json
        produces:
            -   text/plain
        parameters:
            -   in: body
                name: data
                description: Specify data
                required: true
                schema:
                    type: object
                    properties:
                        ip:
                            type:   string
                            required:   true
        responses:
            "200":
                description: successful operation
            "400":
                description: error."
        """
        data = await request.json()
        return web.Response(text=await self.afuncs.restart_instrument(RequestObj(data)))

    async def end_point_resolve_warning(self, request):
        data = await request.json()
        return web.Response(text=await self.afuncs.resolve_warning(RequestObj(data)))

    async def end_point_get_network_settings(self, request):
        """
        ---
        description: get network settings

        tags:
            -   diagnostics
        summary: get network settings
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        return web.Response(text=await self.afuncs.get_network_settings())

    async def end_point_set_network_settings(self, request):
        """
        ---
        description: sets network settings from JSON payload

        tags:
            -   diagnostics
        summary: restarts an instrument
        consumes:
            -   application/json
        produces:
            -   text/plain
        parameters:
            -   in: body
                name: settings
                description: Network settings
                required: true
                schema:
                    type: object
                    properties:
                        dns:
                            type: string
                        gateway:
                            type: string
                        ip:
                            type:   string
                            required:   true
                        netmask:
                            type: string
                        networkType:
                            type: string
        responses:
            "200":
                description: successful operation
            "400":
                description: error."
        """
        data = await request.json()
        return web.Response(text=await self.afuncs.set_network_settings(RequestObj(data)))


class SyncInterface:
    def __init__(self):
        with open("./instruments_backend_meta_master.json", "r") as fp:
            self.instruments = json.load(fp) 

    def get_instruments(self):
        return json.dumps(self.instruments)

    def apply_changes(self, request):
        data = request.get_json()
        with open("instruments_backend_meta.json", "w") as f:
            f.write(json.dumps(data, indent=4, sort_keys=True))
        self.instruments = data
        return ""

    def destroy_instrument(self, request):
        ip = request.get_json()["ip"]
        with open("./img/explosion.txt", "r") as f:
            exp = f.read()
        print(exp.format(ip))
        for instrument in self.instruments:
            if instrument["ip"] == ip:
                instrument["warnings"] = []
                instrument["warnings"].append("instrument received a destroy warning at {}".format(datetime.datetime.now()))
        return ""

    def restart_instrument(self, request):
        ip = request.get_json()["ip"]
        print("instrument by {} will be restarted now".format(ip))
        return ""

    def resolve_warning(self, request):
        ip, resolved_warning = request.get_json()["warning"].split("@")
        print("instruments by {} warning '{}' is resolved".format(ip, resolved_warning))
        for instrument in self.instruments:
            if instrument["ip"] == ip:
                for warning in instrument["warnings"]:
                    if warning == resolved_warning:
                        instrument["warnings"].remove(warning)
        return ""

    def get_network_settings(self):
        with open(my_path + "/network_settings.json", "r") as f:
            settings = f.read()
            json_settings = json.dumps(settings)
        """
        settings = {
        'networkType': 'Static',
        'ip': '192.168.1.148',
        'gateway': '192.168.1.1',
        'netmask': '255.255.255.0',
        'dns': '8.8.8.8'
        }"""
        return settings

    def set_network_settings(self, request):
        settings = request.get_json()
        with open(my_path + "/network_settings.json", "w") as f:
            f.write(json.dumps(settings, indent=4, sort_keys=True))
            f.write('\n')
        print(settings)
        return ""


if __name__ == "__main__":
    service = RackNetworkSettingsServer(port=8004)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(service.startup()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Stop server begin')
    finally:
        loop.run_until_complete(asyncio.gather(service.shutdown()))
        loop.close()
    print('Stop server end')
