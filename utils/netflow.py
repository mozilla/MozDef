#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

import socket, struct, sys

from socket import inet_ntoa

SIZE_OF_HEADER = 24
SIZE_OF_RECORD = 48

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
if len(sys.argv) == 4:
    sock.bind((sys.argv[1], int(sys.argv[2])))
else:
    print "Usage: python ./netflow.py <listening_addr> <listening_udp_port> <log_file>"
    sys.exit(1)

# doc: http://www.plixer.com/support/netflow_v5.html

f = file(sys.argv[3], 'a')

fields = [
    'version',              # 0
    'count',                # 1
    'sys_uptime',           # 2
    'unix_secs',            # 3
    'unix_nsecs',           # 4
    'flow_sequence',        # 5
    'engine_type',          # 6
    'engine_id',            # 7
    'sampling_interval',    # 8
    'srcaddr',              # 9
    'dstaddr',              # 10
    'nexthop',              # 11
    'dPkts',                # 12
    'dOctets',              # 13
    'first',                # 14
    'last',                 # 15
    'srcport',              # 16
    'dstport',              # 17
    'tcp_flags',            # 18
    'prot',                 # 19
    'tos',                  # 20
    'src_as',               # 21
    'dst_as',               # 22
    'src_mask',             # 23
    'dst_mask',             # 24
]
for h in fields:
    f.write("%s\t" % h)
f.write("\n")

while True:
    buf, addr = sock.recvfrom(1500)

    header = {}
    # NetFlow export format version number
    # Number of flows exported in this packet (1-30)
    (header['version'], header['count']) = struct.unpack('!HH',buf[0:4])
    if header['version'] != 5:
        print "Not NetFlow v5!"
        continue

    # It's pretty unlikely you'll ever see more then 1000 records in a 1500 byte UDP packet
    if header['count'] <= 0 or header['count'] >= 1000:
        print "Invalid count %s" % header['count']
        continue

    # Current time in milliseconds since the export device booted
    header['sys_uptime'] = socket.ntohl(struct.unpack('I', buf[4:8])[0])
    # Current count of seconds since 0000 UTC 1970
    header['unix_secs'] = socket.ntohl(struct.unpack('I', buf[8:12])[0])
    # Residual nanoseconds since 0000 UTC 1970
    header['unix_nsecs'] = socket.ntohl(struct.unpack('I', buf[12:16])[0])
    # Sequence counter of total flows seen
    header['flow_sequence'] = socket.ntohl(struct.unpack('I', buf[16:20])[0])
    # Type of flow-switching engine
    header['engine_type'] = socket.ntohl(struct.unpack('B', buf[20])[0])
    # Slot number of the flow-switching engine
    header['engine_id'] = socket.ntohl(struct.unpack('B', buf[21])[0])
    # First two bits hold the sampling mode; remaining 14 bits hold value of sampling interval
    header['sampling_interval'] = struct.unpack('!H', buf[22:24])[0] & 0b0011111111111111

    #print header

    for i in range(0, header['count']):
        try:
            base = SIZE_OF_HEADER+(i*SIZE_OF_RECORD)

            data = struct.unpack('!IIIIHH',buf[base+16:base+36])
            data2 = struct.unpack('!BBBHHBB',buf[base+37:base+46])

            record = header
            # Source IP address
            record['srcaddr'] = inet_ntoa(buf[base+0:base+4])
            # Destination IP address
            record['dstaddr'] = inet_ntoa(buf[base+4:base+8])
            # IP address of next hop router
            record['nexthop'] = inet_ntoa(buf[base+8:base+12])
            # Packets in the flow
            record['dPkts'] = data[0]
            # Total number of Layer 3 bytes in the packets of the flow
            record['dOctets'] = data[1]
            # SysUptime at start of flow
            record['first'] = data[2]
            # SysUptime at the time the last packet of the flow was received
            record['last'] = data[3]
            # TCP/UDP source port number or equivalent
            record['srcport'] = data[4]
            # TCP/UDP destination port number or equivalent
            record['dstport'] = data[5]
            # Cumulative OR of TCP flags
            record['tcp_flags'] = data2[0]
            # IP protocol type (for example, TCP = 6; UDP = 17)
            record['prot'] = data2[1]
            # IP type of service (ToS)
            record['tos'] = data2[2]
            # Autonomous system number of the source, either origin or peer
            record['src_as'] = data2[3]
            # Autonomous system number of the destination, either origin or peer
            record['dst_as'] = data2[4]
            # Source address prefix mask bits
            record['src_mask'] = data2[5]
            # Destination address prefix mask bits
            record['dst_mask'] = data2[6]

            for h in fields:
                f.write("%s\t" % record[h])
            f.write("\n")

            #print record
        except:
            continue

    # Do something with the netflow record..
    #print "%s:%s -> %s:%s" % (record['srcaddr'],record['srcport'],record['dstaddr'],record['dstport'])


f.close()

