#!/usr/bin/env python3
"""
Starts up the back end software consisting of a "farm" of Hierarchical State Machines
 and a collection of web services.
"""
import asyncio
import os
import traceback

import aiohttp_cors
import click
import yamale
from aiohttp import web
from aiohttp_swagger import setup_swagger

from async_hsm import Framework, Event, Signal
from back_end.lologger.lologger_client import LOLoggerClient
from back_end.servers.controller_service import ControllerService
from back_end.servers.customer_api_server import CustomerAPIService
from back_end.servers.grafana_data_generator_service import GrafanaDataGeneratorService
from back_end.servers.grafana_logger_service import GrafanaLoggerService
from back_end.servers.port_history_service import PortHistoryService
from back_end.servers.supervisor_service import SupervisorService
from back_end.servers.system_status_service import SystemStatusService
from back_end.servers.time_aggregation_sevice import TimeAggregationService
from back_end.servers.species_type_service import SpeciesTypeService
from back_end.servers.plan_service import PlanService
from back_end.state_machines.pigss_farm import PigssFarm
from common.async_helper import log_async_exception

log = LOLoggerClient(client_name="AppRunner", verbose=True)

# Get a prioritized list of places to look for the config file
config_path = [
    os.getenv("PIGSS_CONFIG"),
    os.path.join(os.getenv("HOME"), ".config", "pigss"),
    os.path.dirname(os.path.abspath(__file__))
]
config_path = [p for p in config_path if p is not None and os.path.exists(
    p) and os.path.isdir(p)]


class PigssRunner:
    def __init__(self):
        self.tasks = []
        self.app = None
        self.runner = None
        self.port = None
        self.addr = None
        self.terminate_event = None
        self.publish_errors = True

    def set_host(self, port, addr='0.0.0.0'):
        self.port = port
        self.addr = addr

    async def on_startup(self, app):
        await app['farm'].startup()
        self.terminate_event = asyncio.Event()
        return

    async def on_shutdown(self, app):
        for task in self.tasks:
            task.cancel()
        await app['farm'].shutdown()

    async def on_cleanup(self, app):
        log.debug("PigssRunner is cleaning up")
        self.terminate_event.set()

    @log_async_exception(log_func=log.error, publish_terminate=True)
    async def server_init(self, config_filename):
        self.app = web.Application(middlewares=[self.error_middleware])
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.app.on_cleanup.append(self.on_cleanup)
        farm = PigssFarm(config_filename)
        nsim = len(farm.config.get_simulation_analyzers())
        if nsim > 0:
            await setup_dummy_interfaces(nsim)
            await asyncio.sleep(2.0)
        self.app['farm'] = farm
        self.set_host(farm.config.get_http_server_port(),
                      farm.config.get_http_server_listen_address())

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

        system_status_service = SystemStatusService()
        system_status_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/system_status/", system_status_service.app)

        port_history_service = PortHistoryService()
        port_history_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/port_history/", port_history_service.app)

        time_aggregation_service = TimeAggregationService()
        time_aggregation_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/time_aggregation/", time_aggregation_service.app)

        grafana_logger_service = GrafanaLoggerService()
        grafana_logger_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/grafana_logger/", grafana_logger_service.app)

        grafana_data_generator_service = GrafanaDataGeneratorService()
        grafana_data_generator_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/grafana_data_generator/",
                            grafana_data_generator_service.app)

        customer_api_service = CustomerAPIService()
        customer_api_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/public/", customer_api_service.app)

        species_type_service = SpeciesTypeService()
        species_type_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/species/", species_type_service.app)


        log = LOLoggerClient(client_name="PlanService", verbose=True)
        # Get DB file path from config, and pass in instance as db_file
        db_file = os.path.join(os.getenv("HOME"), ".config", "pigss", "data", "sam_data.db")
        manage_plan_service = PlanService(log, db_file)
        manage_plan_service.app['farm'] = self.app['farm']
        self.app.add_subapp("/manage_plan/", manage_plan_service.app)

        setup_swagger(self.app)

        for route in self.app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)
        await site.start()
        log.info(
            f"======== Running on http://{site._host}:{site._port} ========")

    @web.middleware
    async def error_middleware(self, request, handler):
        try:
            resp = await handler(request)
        except web.HTTPNotFound:
            return web.HTTPBadRequest(
                reason="Bad Request",
                text="Please check for incorrect use of API. The API requested, could not be found."
            )
        except Exception as e:
            # noqa
            # Handle unexpected exception by replying with a traceback and optionally publishing an event
            if self.publish_errors:
                Framework.publish(
                    Event(
                        Signal.ERROR, {
                            "type": "service",
                            "exc": str(e),
                            "traceback": traceback.format_exc(),
                            "location": self.__class__.__name__,
                            "request": str(request.url)
                        }))
                log.debug(
                    f"Error hanadling the request {str(request.url)}. \n{traceback.format_exc()}")
            raise web.HTTPInternalServerError(
                text=f"Error handling request {request.path_qs}\n{traceback.format_exc()}")
        return resp

    def handle_exception(self, loop, context):
        msg = context.get("exception", context["message"])
        log.critical(f"Unhandled exception:\n{msg}\n{traceback.format_exc()}")
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


async def async_main(config_filename, validate):
    try:
        service = None
        schema_filename = "config_schema.yaml"
        config_found = False
        schema_found = False
        for p in config_path:
            config_full_filename = os.path.normpath(
                os.path.join(p, config_filename))
            if os.path.exists(config_full_filename):
                config_found = True
                break
        for p in config_path:
            schema_full_filename = os.path.normpath(
                os.path.join(p, schema_filename))
            if os.path.exists(schema_full_filename):
                schema_found = True
                break
        if config_found:
            ok = True
            if validate:
                if schema_found:
                    try:
                        yamale.validate(yamale.make_schema(schema_full_filename, parser='ruamel'),
                                        yamale.make_data(
                                            config_full_filename, parser='ruamel'),
                                        strict=True)
                    except ValueError as ve:
                        log.error(
                            f"Configuration file {config_filename} fails validation: {ve}")
                        ok = False
                else:
                    log.error(
                        f"Cannot find schema for validating configuration")
                    ok = False
            if ok:
                log.info(
                    f"Starting application with configuration file {config_full_filename}.")
                service = PigssRunner()
                await service.server_init(config_full_filename)
                await Framework.done()
        else:
            log.error(f"Configuration file {config_filename} was not found")
    except Exception as e:  # noqa
        # Catch unhandled exceptions to be logged
        log.critical(f"Exception in main()\n{e}\n{traceback.format_exc()}")
    finally:
        if service and service.runner is not None:
            await service.runner.cleanup()
            if service.terminate_event is not None:
                try:
                    await asyncio.wait_for(service.terminate_event.wait(), timeout=2)
                except asyncio.TimeoutError:
                    pass  # We have timed out waiting for all processes to terminate cleanly
    log.info('Application stopped.')


@click.command()
@click.option('--config', '-c', 'config_filename', default='pigss_config.yaml', help='Name of configuration file in yaml format')
@click.option('--validate/--no-validate', default=True, help='Use schema for validating configuration')
def main(config_filename, validate):
    asyncio.run(async_main(config_filename, validate))


if __name__ == "__main__":
    main()
