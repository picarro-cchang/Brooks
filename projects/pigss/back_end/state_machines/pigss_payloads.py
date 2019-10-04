#!/usr/bin/env python3
#
# FILE:
#   pigss_payloads.py
#
# DESCRIPTION:
#   Event payloads for hierarchical state machine framework
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-Oct-2019  sze Initial check in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
import attr


@attr.s
class PcSendPayload:
    message = attr.ib(str)
    timeout = attr.ib(1.0)


@attr.s
class PcResponsePayload:
    message = attr.ib(str)


@attr.s
class PlanError:
    error = attr.ib(False)
    message = attr.ib("OK")
    row = attr.ib(0)
    column = attr.ib(0)


@attr.s
class PigletRequestPayload:
    command = attr.ib(str)
    bank_list = attr.ib(factory=list)


@attr.s
class SystemConfiguration:
    bank_list = attr.ib(factory=list)
    mad_mapper_result = attr.ib(None)


@attr.s
class ValvePositionPayload:
    time = attr.ib(float)
    valve_pos = attr.ib(int)
    valve_mask = attr.ib(int)
    clean_mask = attr.ib(int)
