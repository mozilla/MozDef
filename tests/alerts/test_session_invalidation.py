#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from tests.alerts.alert_test_suite import AlertTestSuite
from tests.alerts.negative_alert_test_case import NegativeAlertTestCase
from tests.alerts.positive_alert_test_case import PositiveAlertTestCase


class TestAlertSessionInvalidation(AlertTestSuite):
    alert_filename = 'session_invalidation'

    default_event = {
        '_source': {
            'category': 'sessioninvalidation',
            'details': {
                'actor': 'actor@mozilla.com',
                'invalidateduser': 'test@mozilla.com',
                'invalidatedsessions': [
                    'sso',
                    'slack',
                    'gsuite',
                ],
            },
        },
    }

    no_invalidation_event = {
        '_source': {
            'category': 'sessioninvalidation',
            'details': {
                'actor': 'actor@mozilla.com',
                'invalidateduser': None,
                'invalidatedsessions': None,
            },
        },
    }

    default_alert = {
        'category': 'sessioninvalidation',
        'tags': ['sessioninvalidation'],
        'severity': 'WARNING',
        'details': {
            'actor': 'actor@mozilla.com',
            'username': 'actor@mozilla.com',
            'terminations': [
                {
                    'invalidateduser': 'test@mozilla.com',
                    'invalidatedsessions': [
                        'sso',
                        'slack',
                        'gsuite',
                    ],
                },
            ],
        },
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires when an actor terminates sessions',
            events=[default_event],
            expected_alert=default_alert,
        ),
        PositiveAlertTestCase(
            description='Events wherein no termination happened not included',
            events=[default_event, no_invalidation_event],
            expected_alert=default_alert,
        ),
        NegativeAlertTestCase(
            description='Alert does not fire when no terminations happened',
            events=[no_invalidation_event],
        ),
    ]
