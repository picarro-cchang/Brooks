#!/usr/bin/env python3
from grootilities.grootility import GROOTility


def build():
    with GROOTility('production') as GROOT:
        GROOT.build_plugins()
        GROOT._deploy_plugins()


if __name__ == '__main__':
    build()
