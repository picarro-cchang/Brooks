#!/usr/bin/env python3
"""
Starts up the "farm" of hierarchical state machines and the message queues
 for the web socket to and from the front end
"""
import asyncio
import traceback

from back_end.lologger.lologger_client import LOLoggerClient
from back_end.state_machines.piglet_manager import PigletManager
from back_end.state_machines.pigss_config import PigssConfig
from back_end.state_machines.pigss_controller import PigssController
from back_end.state_machines.pigss_error_manager import PigssErrorManager
from back_end.state_machines.pigss_supervisor import PigssSupervisor

log = LOLoggerClient(client_name="PigssFarm", verbose=True)


class PigssFarm:
    """Collection of Heirarchical State Machines for controlling PiGSS.
        The send_queue and receive_queue are used to transfer information
        to and from the UI via a web socket connection. These are passed
        to the controller, which runs the main HSM for interacting with
        the piglets.
    """
    def __init__(self, config_filename):
        self.config_filename = config_filename
        self.config = PigssConfig(config_filename)
        self.controller = PigssController(self)
        self.pigss_error_manager = PigssErrorManager(self)
        self.piglet_manager = PigletManager(self)
        self.pigss_supervisor = PigssSupervisor(self)
        self.send_queue = asyncio.Queue(maxsize=256)
        self.receive_queue = asyncio.Queue(maxsize=256)
        self.tasks = []
        self.RPC = {}

    async def shutdown(self):
        for task in self.tasks:
            task.cancel()

    async def startup(self):
        try:
            log.debug(f"Starting up farm of state machines")
            self.controller.set_queues(self.send_queue, self.receive_queue)
            # Uncomment the next lines to debug transitions in the state machines
            # from async_hsm.SimpleSpy import SimpleSpy
            # Spy.enable_spy(SimpleSpy)
            self.tasks.append(asyncio.create_task(self.controller.process_receive_queue_task()))
            self.piglet_manager.start(4)
            self.controller.start(3)
            self.pigss_supervisor.start(2)
            self.pigss_error_manager.start(1)
        except Exception:  # noqa
            # We want to catch and log any exception if we cannot set up the farm
            log.error(f"Error setting up farm\n{traceback.format_exc()}")
            raise
