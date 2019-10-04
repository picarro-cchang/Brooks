#!/usr/bin/env python3
#
# FILE:
#   pigss_runner.py
#
# DESCRIPTION:
#  Starts up the back end software consisting of a "farm" of Hierarchical
# State Machines and a collection of web services.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-Oct-2019  sze Initial check in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
import asyncio
import os
import traceback

import aiohttp_cors
import click
from aiohttp import web
from aiohttp_swagger import setup_swagger

from async_hsm import Framework
from back_end.lologger.lologger_client import LOLoggerClient
from back_end.servers.controller_service import ControllerService
from back_end.servers.port_history_service import PortHistoryService
from back_end.servers.supervisor_service import SupervisorService
from back_end.servers.time_aggregation_sevice import TimeAggregationService
from back_end.state_machines.pigss_farm import PigssFarm
from common.async_helper import log_async_exception

log = LOLoggerClient(client_name="PigssRunner", verbose=True)
my_path = os.path.dirname(os.path.abspath(__file__))


class PigssRunner:
    def __init__(self):
        self.tasks = []
        self.app = None
        self.runner = None
        self.port = None
        self.addr = None
        self.terminate_event = asyncio.Event()

    def set_host(self, port, addr='0.0.0.0'):
        self.port = port
        self.addr = addr

    async def on_startup(self, app):
        await app['farm'].startup()
        return

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        await app['farm'].shutdown()

    async def on_cleanup(self, app):
        print("PigssRunner is cleaning up")
        self.terminate_event.set()

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

        time_aggregation_service = TimeAggregationService()
        time_aggregation_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/time_aggregation/", time_aggregation_service.app)

        setup_swagger(self.app)

        for route in self.app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)
        await site.start()
        print(f"======== Running on http://{site._host}:{site._port} ========")

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


async def async_main(config_filename):
    try:
        config_filename = os.path.normpath(os.path.join(my_path, config_filename))
        log.info(f"Starting PigssRunner with configuration file {config_filename}")
        service = PigssRunner()
        # loop = asyncio.get_event_loop()
        # loop.set_exception_handler(service.handle_exception)
        await service.server_init(config_filename)
        await Framework.done()
    except Exception as e:
        log.error(f"Exception in main()\n{e}\n{traceback.format_exc()}")
    finally:
        if service.runner is not None:
            await service.runner.cleanup()
            await service.terminate_event.wait()
    log.info('PigssRunner stopped')


@click.command()
@click.option('--config', '-c', 'config_filename', default='pigss_config.yaml', help='Name of configuration file in yaml format')
def main(config_filename):
    asyncio.run(async_main(config_filename))


if __name__ == "__main__":
    main()
