#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


from elasticsearch_dsl import Q


def RangeMatch(field_name, from_value, to_value):
    return Q('range', **{field_name: {'gte': from_value, 'lte': to_value}})
