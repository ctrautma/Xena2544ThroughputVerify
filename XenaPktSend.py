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

_LOGGER = logging.getLogger(__name__)
_LOCALE = locale.getlocale()[1]
_XENA_USER = 'Monitor'
_PYTHON_2 = sys.version_info[0] < 3

pkthdr1 = '0x525400C61010525400C6102008004500001400000000' \
          '7FFF25EA0A0001010A000001'
pkthdr2 = '0x04F4BC2FA98100000000000008004500002E00000000' \
          '7FFF26CF0A0000020A000001'

"""
Xena Socket API Driver module for communicating directly with Xena system
through socket commands and returning different statistics.
"""

_LOCALE = locale.getlocale()[1]
_LOGGER = logging.getLogger(__name__)

def main(args):
    _LOGGER.setLevel(logging.INFO)
    stream_logger = logging.StreamHandler(sys.stdout)
    stream_logger.setFormatter(logging.Formatter(
        '[%(levelname)-5s]  %(asctime)s : (%(name)s) - %(message)s'))
    _LOGGER.addHandler(stream_logger)
    xena_socket = XenaSocket(args.chassis)
    xena_socket.connect()
    time.sleep(1)

    # create the manager session
    xm = XenaManager(xena_socket, 'TestUser')
    time.sleep(1)
    try:
        # add port 0 and configure
        port0 = xm.add_port(args.module, args.ports[0])
        port0.reserve()
        port0.clear_all_rx_stats()
        port0.clear_all_tx_stats()
        # add port 1 and configure
        port1 = xm.add_port(args.module, args.ports[1])
        port1.reserve()
        port1.clear_all_rx_stats()
        port1.clear_all_tx_stats()
    except Exception as e:
        print('An exception occurred while attempting to add and configure ports')
        print(e)
    try:
        # add a single stream and configure
        s1_p0 = port0.add_stream(0)
        s1_p0.set_packet_limit(args.duration * args.pps)
        s1_p0.set_stream_on()
        s1_p0.set_rate_pps(args.pps)
        s1_p0.set_packet_header(pkthdr1)
        s1_p0.set_packet_length_fixed(args.pkt_size, 1518)
        s1_p0.set_packet_payload_incrementing('0x00')
        s1_p0.set_packet_protocol('ETHERNET', 'IP')
        s1_p0.set_test_payload_id(1)
        
        # enable multistream
        if args.number_streams:
            m1_s1_p0 = s1_p0.add_modifier()
            m1_s1_p0.set_modifier(32, 0xffff0000, 'inc', 1)
            m1_s1_p0.set_modifier_range(0, 1, args.number_streams)
        
        # begin network traffic
        port0.start_traffic()
        time.sleep(args.duration + 2)
        port0.stop_traffic()
        
        # retrieve traffic statistics
        port1.grab_all_rx_stats()
        grab_stats = port1.dump_all_rx_stats()
        
        # reorganize stats dict
        stats = {}
        for timestamp, stat in grab_stats.items():
            for key in stat:
                stats[key] = stat[key]

        # packets sent
        pkt_sent = args.duration * args.pps
        print('Packets sent: {}'.format(pkt_sent))
        
        # packets received
        pr_total = stats.get('pr_total')
        pkt_rec = pr_total.get('packets')
        
        # latency
        pr_tpldlatency = stats.get('pr_tpldlatency')
        tmp = pr_tpldlatency.get('1')
        pkt_latency_avg = tmp.get('avg')
        print('Packet latency: {} ns'.format(pkt_latency_avg))
        
        # packets lost
        pkt_lost = pkt_sent - pkt_rec # sometimes returns negative loss, TODO: find out why
        print('Packets received: {}'.format(pkt_rec))
        print('Packets lost: {}'.format(pkt_lost))
    except Exception as e:
        print('An exception occurred while attempting to add and configure stream')
        print(e)
    finally:
        # disconnect from Xena
        print('Disconnecting from Xena chassis...')
        del xm
        del xena_socket
        print('Connection severed')

if __name__ == '__main__':
    import sys
    if sys.version[0] != '3':
        print('Python 2 not supported')
        sys.exit(1)
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--chassis', type=str, required=True,
                        help='Xena Chassis IP')
    parser.add_argument('-m', '--module', type=int, required=True,
                        help='Module to use')
    parser.add_argument('-p', '--ports', nargs=2, type=int, required=False,
                        default=[0, 1], help='Ports to use, default = 0,1')
    parser.add_argument('-d', '--duration', type=int,
                        required=False, default=60, help='Duration to run')
    parser.add_argument('-s', '--pkt_size', type=int, required=False,
                        default=1500, help='pkt size to send')
    parser.add_argument('-f', '--pps', type=int, required=False,
                        default=1000, help='pkt per second')
    parser.add_argument('-n', '--number_streams', type=int,
                        required=False, default=1024,
                        help='Number of streams for multistream')
    args = parser.parse_args()
    main(args)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

