"""
Copyright 2013, Picarro Inc.
"""

import optparse
import time

from Host.Common import Win32


def main(opts):
    time.sleep(opts.delayTime)
    Win32.User32.lockWorkStation()


if __name__ == '__main__':
    usage = """
%prog [options]

Lock the workstation and require valid credentials to be entered to login.
"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--time', dest='delayTime', default=5.0, type='float',
                      metavar='DELAY_TIME',
                      help='The amount of time to delay before locking the '
                      'workstation.')

    options, _ = parser.parse_args()

    main(options)
