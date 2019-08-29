import asyncio

import aiohttp_cors
import click
from aiohttp import web
from aiohttp_swagger import setup_swagger

from async_hsm import Framework
from experiments.common.async_helper import log_async_exception
from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from experiments.state_machine.back_end.controller_service import \
    ControllerService
from experiments.state_machine.back_end.pigss_farm import PigssFarm
from experiments.state_machine.back_end.supervisor_service import \
    SupervisorService

log = LOLoggerClient(client_name="PigssServer", verbose=True)


class Server:
    def __init__(self, port, addr='0.0.0.0', data="unspecified"):
        self.tasks = []
        self.app = None
        self.runner = None
        self.port = port
        self.addr = addr
        self.data = data

    async def on_startup(self, app):
        await app['farm'].startup()

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        await app['farm'].shutdown()

    async def on_cleanup(self, app):
        print("Top level server is cleaning up")
        pass

    @log_async_exception(log_func=log.warning, stop_loop=True)
    async def server_init(self, simulation=False):
        self.app = web.Application()
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)

        self.app['farm'] = PigssFarm(simulation=simulation)
        cors = aiohttp_cors.setup(
            self.app, defaults={"*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )})

        controller_service = ControllerService()
        controller_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/controller/", controller_service.app)

        supervisor_service = SupervisorService()
        supervisor_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/supervisor/", supervisor_service.app)

        setup_swagger(self.app)

        for route in self.app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)
        await site.start()
        print(f"======== Running on http://{site._host}:{site._port} ========")

    async def startup(self, simulation=False):
        self.tasks.append(asyncio.create_task(self.server_init(simulation)))

    def handle_exception(self, loop, context):
        msg = context.get("exception", context["message"])
        log.error(f"Unhandled exception:\n{msg}")
        asyncio.create_task(self.on_shutdown)
        loop.stop()


@click.command()
@click.option('--simulation/--no-simulation', '-s/ ', is_flag=True, help="Use simulation")
def main(simulation):
    service = Server(port=8000)
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(service.handle_exception)
    loop.run_until_complete(asyncio.gather(service.startup(simulation)))
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(asyncio.gather(service.runner.cleanup()))
        Framework.stop()
        # log_process.kill()
    log.info('Server stopped')


if __name__ == "__main__":
    main()
