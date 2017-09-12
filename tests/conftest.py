#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com


def pytest_addoption(parser):
    parser.addoption(
        "--delete_indexes",
        action='store_true',
        default=False,
        help="A flag to indicate if we should delete all indexes in ES before each test. This could result in inconsistent tests if not specified."
    )
    parser.addoption(
        "--delete_queues",
        action='store_true',
        default=False,
        help="A flag to indicate if we should delete the contents of rabbitmq queues. This could result in inconsistent tests if not specified."
    )
