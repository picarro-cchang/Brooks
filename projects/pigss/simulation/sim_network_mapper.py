#!/usr/bin/env python3
#
# FILE:
#   sim_network_mapper.py
#
# DESCRIPTION:
#   Replaces NetworkMapper class for madmapper when the system is run in simulation mode.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-Oct-2019  sze Initial check in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
from back_end.madmapper.network.networkmapper import NetworkMapper


class SimNetworkMapper(NetworkMapper):
    pass
