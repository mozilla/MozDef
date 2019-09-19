#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import ipaddress
from .query_string_match import QueryStringMatch


def SubnetMatch(key, value):
    ips = [str(ip) for ip in ipaddress.IPv4Network(value)]
    subnet_str = "{0}: [{1} TO {2}]".format(key, ips[0], ips[-1])
    return QueryStringMatch(subnet_str)
