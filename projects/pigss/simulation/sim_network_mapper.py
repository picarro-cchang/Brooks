#!/usr/bin/env python3
"""
Replaces NetworkMapper class for madmapper when the system is run in simulation mode.
"""
from back_end.madmapper.network.networkmapper import NetworkMapper


class SimNetworkMapper(NetworkMapper):
    pass
