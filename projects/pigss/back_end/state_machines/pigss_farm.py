#!/usr/bin/env python3
#
# FILE:
#   pigss_farm.py
#
# DESCRIPTION:
#   Starts up the "farm" of hierarchical state machines and the message queues
#  for the web socket to and from the front end
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
        the piglets. The comms state machine is used to communicate with
        the serial ports and to handle errors.
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
        # Framework.publish(Event(Signal.TERMINATE, None))

    async def startup(self):
        try:
            log.info(f"Starting up farm of state machines")
            self.controller.set_queues(self.send_queue, self.receive_queue)
            # from async_hsm.SimpleSpy import SimpleSpy
            # Spy.enable_spy(SimpleSpy)
            self.tasks.append(asyncio.create_task(self.controller.process_receive_queue_task()))
            self.piglet_manager.start(4)
            self.controller.start(3)
            self.pigss_supervisor.start(2)
            self.pigss_error_manager.start(1)
        except Exception:
            log.error(f"Error setting up farm\n{traceback.format_exc()}")
            raise
