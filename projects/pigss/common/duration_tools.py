#!/usr/bin/python3
#
# FILE:
#   duration_tools.py
#
# DESCRIPTION:
#   Helper functions for processing influxdb duration strings
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#     Sep-2019  petr Initial code
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
ms_map = {
    # "ns": 0.001*0.001*0.001,
    # "u": 0.001*0.001,
    # "ms":0.001, we are not going to support those for now
    "s": 1,
    "m": 1 * 60,
    "h": 1 * 60 * 60,
    "d": 1 * 60 * 60 * 24,
    "w": 1 * 60 * 60 * 24 * 7
}


def generate_duration_in_seconds(duration, ms=False):
    """Given duration time in literal form , translate it to seconds or ms"""
    last_cut = 0
    seconds = 0
    for char_pos in range(len(duration)):
        if duration[char_pos] in ms_map:
            sub_duration = duration[last_cut:char_pos + 1]
            last_cut = char_pos + 1
            seconds += int(sub_duration[:-1]) * ms_map[sub_duration[-1]]
    if ms:
        seconds *= 1000
    return seconds


def generate_duration_literal(duration):
    """Given duration as int of seconds, translate to literal form"""
    time_periods = [i for i, j in sorted(ms_map.items(), key=lambda kv: kv[1], reverse=True)]
    duration_left = duration
    literal = ""
    for time_period in time_periods:
        if duration_left >= ms_map[time_period]:
            literal += f"{int(duration_left/ms_map[time_period])}{time_period}"
            duration_left = duration_left % ms_map[time_period]
    return literal


def optimize_literal_duration(duration):
    """
        Create an optimal literal duration, like 300s -> 5m, or 55m300s -> 1h
    """
    return generate_duration_in_seconds(generate_duration_literal(duration))


def check_for_valid_literal_duration(duration):
    """Check if passed argument is a valid duration in a literal form"""
    if duration.lower() == "inf":
        return True
    last_cut = 0
    for char_pos in range(len(duration)):
        if duration[char_pos] in ms_map:
            sub_duration = duration[last_cut:char_pos + 1]
            # print(sub_duration)
            last_cut = char_pos + 1
            if not sub_duration[:-1].isdigit() and sub_duration[-1] in ms_map:
                return False
    if last_cut != len(duration):
        return False
    return True
