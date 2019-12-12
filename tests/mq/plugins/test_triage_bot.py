# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import mq.plugins.triage_bot as bot

import requests_mock


class TestTriageBot:
    def test_update_alert_status_request_success(self):
        with requests_mock.mock() as mock:
            url = 'http://mock.site/updatealert'
            cfg = bot.RESTConfig(url, 'token')
            msg = bot.UserResponseMessage(
                'id',
                bot.UserInfo('test@site.com', 'tester'),
                bot.Confidence.HIGH,
                bot.UserResponse.YES)

            mock.post(url, json={'error': None})
            succeeded = bot.update_alert_status(msg, cfg)

            assert succeeded
    

    def test_update_alert_status_request_failure(self):
        with requests_mock.mock() as mock:
            url = 'http://mock.site/updatealert'
            cfg = bot.RESTConfig(url, 'token')
            msg = bot.UserResponseMessage(
                'id',
                bot.UserInfo('test@site.com', 'tester'),
                bot.Confidence.HIGH,
                bot.UserResponse.YES)

            mock.post(url, json={'error': None}, status_code=400)
            succeeded = bot.update_alert_status(msg, cfg)

            assert not succeeded


    def test_process_rejects_bad_messages(self):
        msg = {
            'identifier': 'test'
        }
        cfg = bot.RESTConfig('', '')

        (new_msg, new_meta) = bot.process(msg, {}, cfg)

        assert new_msg is None
        assert new_meta is None


    def test_process_invokes_update_for_good_messages(self):
        msg = {
            'identifier': 'id',
            'user': {
                'email': 'tester@site.com',
                'slack': 'tester'
            },
            'identityConfidence': 'high',
            'response': 'yes'
        }
        cfg = bot.RESTConfig('http://mock.site/updatealert', 'token')

        with requests_mock.mock() as mock:
            mock.post(cfg.url, json={'error': None})
            (new_msg, new_meta) = bot.process(msg, {}, cfg)

            assert new_msg == msg
