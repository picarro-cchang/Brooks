#!/usr/bin/env python3
#
# FILE:
#   pigss_payloads.py
#
# DESCRIPTION:
#   The pigss error manager is a sate machine which subscribes to events of type
#    Signal.ERROR and reports them to the logger and other interested parties
#    (for example the front-end GUI). Individual state machines are also free to
#    subscribe to these messages and do whatever recovery they see fit.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-Oct-2019  sze Initial check in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
from collections import deque

import common.timeutils as timeutils
from async_hsm import Ahsm, Framework, Signal, state
from back_end.lologger.lologger_client import LOLoggerClient

log = LOLoggerClient(client_name="PigssErrorManager", verbose=True)


class PigssErrorManager(Ahsm):
    def __init__(self, farm):
        super().__init__()
        self.farm = farm
        self.tasks = []
        self.error_deque = deque(maxlen=32)

    @state
    def _initial(self, e):
        self.publish_errors = True
        Framework.subscribe("ERROR", self)
        Framework.subscribe("TERMINATE", self)
        return self.tran(self._handle_errors)

    @state
    def _handle_errors(self, e):
        sig = e.signal
        if sig == Signal.TERMINATE:
            return self.tran(self._exit)
        elif sig == Signal.ERROR:
            msg = f"Exception {e.value['exc']} raised in {e.value['location']}\n{e.value['traceback']}"
            self.error_deque.append(f"{timeutils.get_local_timestamp()} {msg}")
            log.error(msg)
            return self.handled(e)
        return self.super(self.top)
