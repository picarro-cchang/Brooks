"""
Copyright 2013 Picarro Inc.

Wrap the expected analysis results.
"""


class File6Analysis(object):

    EPOCH_TIME = [
        1376375290.57,
        1376375899.54,
        1376376506.24,
        1376377120.41,
        1376377725.24,
        1376378335.44,
        1376378945.19,
        1376379550.23]

    DISTANCE = [0.0] * len(EPOCH_TIME)

    GPS_ABS_LONG = [0.0] * len(EPOCH_TIME)

    GPS_ABS_LAT = [0.0] * len(EPOCH_TIME)

    CONC = [
        9.190,
        6.062,
        3.523,
        9.349,
        5.975,
        3.402,
        9.131,
        5.847]

    DELTA = [
        -39.60,
        -39.55,
        -40.37,
        -39.58,
        -38.88,
        -39.23,
        -39.45,
        -39.56]

    UNCERTAINTY = [
        0.15,
        0.28,
        0.71,
        0.15,
        0.28,
        0.72,
        0.15,
        0.28]

    REPLAY_MAX = [
        10.512,
        7.066,
        4.092,
        10.543,
        7.084,
        4.068,
        10.526,
        7.078]

    REPLAY_LMIN = [
        2.344,
        2.032,
        1.981,
        2.503,
        2.019,
        1.984,
        2.356,
        2.010]

    REPLAY_RMIN = [
        2.055,
        2.018,
        2.104,
        2.020,
        2.069,
        2.033,
        2.063,
        2.181]

    DISPOSITION = [0.0] * len(EPOCH_TIME)
