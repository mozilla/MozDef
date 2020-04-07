#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


from elasticsearch_dsl import Q


def BooleanMatch(must=[], must_not=[], should=[]):
    return Q('bool', must=must, must_not=must_not, should=should)
