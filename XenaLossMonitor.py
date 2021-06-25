# Copyright 2016-2021 Red Hat Inc & Xena Networks.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Contributors:
#   Christian Trautman, Red Hat Inc.
#   Flavio Leitner, Red Hat Inc.
#   Greg Dumas, Red Hat Inc.

import argparse
import locale
import logging
import re
import socket
import struct
import sys
import threading
import time

from xenalib.XenaSocket import XenaSocket
from xenalib.XenaManager import XenaManager
from xenalib.XenaPort import XenaPort

_LOGGER = logging.getLogger(__name__)
_LOCALE = locale.getlocale()[1]
_XENA_USER = 'Monitor'
_PYTHON_2 = sys.version_info[0] < 3

"""
Xena Socket API Driver module for communicating directly with Xena system
through socket commands and returning different statistics.
"""

_LOCALE = locale.getlocale()[1]
_LOGGER = logging.getLogger(__name__)

def main(args):
    _LOGGER.setLevel(logging.DEBUG if args.debug else logging.INFO)
    stream_logger = logging.StreamHandler(sys.stdout)
    stream_logger.setFormatter(logging.Formatter(
        '[%(levelname)-5s]  %(asctime)s : (%(name)s) - %(message)s'))
    _LOGGER.addHandler(stream_logger)
    xena_socket = XenaSocketDriver(args.chassis)
    xena_manager = XenaManager(xena_socket, 'Monitor', 'xena')
    port0 = xena_manager.add_module_port(args.module, args.ports[0])
    port1 = xena_manager.add_module_port(args.module, args.ports[1])
    totaltime = 0
    while totaltime < args.length:
        time.sleep(1)
        totaltime += 1
        total_lossport0 = 0
        total_lossport1 = 0
        if totaltime % args.interval == 0:
            rx_stats0 = port0.get_rx_stats()
            rx_stats1 = port1.get_rx_stats()
            for stat in rx_stats0._stats:
                match = re.match('\d+\/\d+\s+PR_TPLDERRORS\s+\[\d+\]\s+\d+\s+(\d+)\s+\d+\s+\d+\n', stat)
                if match:
                    total_lossport0 += int(match.group(1))
            for stat in rx_stats1._stats:
                match = re.match('\d+\/\d+\s+PR_TPLDERRORS\s+\[\d+\]\s+\d+\s+(\d+)\s+\d+\s+\d+\n', stat)
                if match:
                    total_lossport1 += int(match.group(1))
            _LOGGER.info('Port 0 total lost frames: {}'.format(total_lossport0))
            _LOGGER.info('Port 1 total lost frames: {}'.format(total_lossport1))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--chassis', type=str, required=True,
                        help='Xena Chassis IP')
    parser.add_argument('-m', '--module', type=int, required=True,
                        help='Module to use')
    parser.add_argument('-p', '--ports', nargs=2, type=int, required=False,
                        default=[0, 1], help='Ports to use, default = 0,1')
    parser.add_argument('-t', '--interval', type=int,
                        required=False, default=60, help='Interval to check ports')
    parser.add_argument('-d', '--debug', action='store_true', required=False,
                        help='Enable debug logging')
    parser.add_argument('-l', '--length', type=int,
                        required=False, default=3600, help='Duration of script')
    args = parser.parse_args()
    if args.debug:
        print("DEBUG ENABLED!!!")
    main(args)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

