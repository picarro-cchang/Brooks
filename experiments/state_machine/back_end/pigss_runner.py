import asyncio
import os

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
from experiments.state_machine.back_end.port_history_service import \
    PortHistoryService
from experiments.state_machine.back_end.supervisor_service import \
    SupervisorService
import traceback

log = LOLoggerClient(client_name="PigssRunner", verbose=True)
my_path = os.path.dirname(os.path.abspath(__file__))


class PigssRunner:
    def __init__(self):
        self.tasks = []
        self.app = None
        self.runner = None
        self.port = None
        self.addr = None

    def set_host(self, port, addr='0.0.0.0'):
        self.port = port
        self.addr = addr

    async def on_startup(self, app):
        await app['farm'].startup()

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        await app['farm'].shutdown()

    async def on_cleanup(self, app):
        print("Top level server is cleaning up")
        pass

    @log_async_exception(log_func=log.error, stop_loop=True)
    async def server_init(self, config_filename):
        self.app = web.Application()
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)
        farm = PigssFarm(config_filename)
        nsim = len(farm.config.get_simulation_analyzers())
        if nsim > 0:
            await setup_dummy_interfaces(nsim)
            await asyncio.sleep(2.0)
        self.app['farm'] = farm
        self.set_host(farm.config.get_http_server_port(), farm.config.get_http_server_listen_address())

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

        port_history_service = PortHistoryService()
        port_history_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/port_history/", port_history_service.app)

        setup_swagger(self.app)

        for route in self.app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)
        await site.start()
        print(f"======== Running on http://{site._host}:{site._port} ========")

    async def startup(self, config_filename):
        self.tasks.append(asyncio.create_task(self.server_init(config_filename)))
        1 / 0

    def handle_exception(self, loop, context):
        msg = context.get("exception", context["message"])
        log.error(f"Unhandled exception:\n{msg}\n{traceback.format_exc()}")
        asyncio.create_task(self.on_shutdown)
        loop.stop()


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode() if stdout else "", stderr.decode() if stderr else ""


async def run_and_raise(cmd):
    retcode, out, err = await run(cmd)
    if retcode:
        raise RuntimeError(f'Running {cmd} gave return code {retcode}\n{err}')
    return retcode, out, err


async def setup_dummy_interfaces(num_interfaces):
    # Get rid of existing dummy interfaces
    retcode, out, err = await run_and_raise('sudo ip link show type dummy')
    for line in out.splitlines():
        atoms = line.split(":", 3)
        if atoms[0].isnumeric():
            retcode, out, err = await run_and_raise(f'sudo ip link delete {atoms[1]}')
    # Create "num_interfaces" new dummy interfaces
    for i in range(num_interfaces):
        retcode, out, err = await run_and_raise(f'sudo ip link add dummy{i} type dummy')
        retcode, out, err = await run_and_raise(f'sudo ip addr add 192.168.10.{101 + i}/24 brd + dev dummy{i}')
        # retcode, out, err = await run_and_raise(f'sudo ip link set dummy{i} up')


@click.command()
@click.option('--config', '-c', 'config_filename', default='pigss_config.yaml', help='Name of configuration file in yaml format')
def main(config_filename):
    try:
        config_filename = os.path.normpath(os.path.join(my_path, config_filename))
        log.info(f"Starting PigssRunner with configuration file {config_filename}")
        service = PigssRunner()
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(service.handle_exception)
        loop.run_until_complete(asyncio.gather(service.startup(config_filename)))
        loop.run_forever()
    except Exception as e:
        log.error(f"Exception in main()\n{e}\n{traceback.format_exc()}")
    finally:
        if service.runner is not None:
            loop.run_until_complete(asyncio.gather(service.runner.cleanup()))
        Framework.stop()
    log.info('PigssRunner stopped')


if __name__ == "__main__":
    main()
