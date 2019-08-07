#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import time


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


def pytest_generate_tests(metafunc):
    ''' just to attach the cmd-line args to a test-class that needs them '''
    delete_indexes = metafunc.config.getoption("delete_indexes")
    if delete_indexes and hasattr(metafunc.cls, 'config_delete_indexes'):
        metafunc.cls.config_delete_indexes = delete_indexes

    delete_queues = metafunc.config.getoption("delete_queues")
    if delete_queues and hasattr(metafunc.cls, 'config_delete_queues'):
        metafunc.cls.config_delete_queues = delete_queues


def pytest_configure(config):
    warning_text = ""
    if not config.option.delete_indexes:
        warning_text += "\n** WARNING - Some unit tests will not pass unless the --delete_indexes is specified."
        warning_text += "\nThis is due to the fact that some tests need a 'clean' ES environment **\n"
        warning_text += "** DISCLAIMER - If you enable this flag, all indexes that MozDef uses will be deleted upon test execution **\n"
    else:
        warning_text += "\n** WARNING - The --delete_indexes flag has been set. We will be deleting important indexes from ES before test execution**\n"
        warning_text += "Continuing the unit test execution in 10 seconds...CANCEL ME IF YOU DO NOT WANT PREVIOUS INDEXES DELETED!!! **\n"

    if not config.option.delete_queues:
        warning_text += "\n** WARNING - Some unit tests will not pass unless the --delete_queues is specified."
        warning_text += "\nThis is due to the fact that some tests need a 'clean' RabbitMQ environment **\n"
        warning_text += "** DISCLAIMER - If you enable this flag, the queues in rabbitmq that MozDef uses will be deleted upon test execution **\n"
    else:
        warning_text += "\n** WARNING - The --delete_queues flag has been set. We will be purging RabbitMQ queues before test execution**\n"
        warning_text += "Continuing the unit test execution in 10 seconds...CANCEL ME IF YOU DO NOT WANT PREVIOUS QUEUES PURGED!!! **\n"

    print(warning_text)
    time.sleep(10)
