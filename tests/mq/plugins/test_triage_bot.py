# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import json

import requests_mock

import mq.plugins.triage_bot as bot


class TestTriageBot:
    def test_update_alert_status_request_success(self):
        with requests_mock.mock() as mock:
            url = "http://mock.site"
            cfg = bot.RESTConfig(url, "token")
            msg = bot.UserResponseMessage(
                "id",
                bot.UserInfo("test@site.com", "tester"),
                bot.Confidence.HIGH,
                bot.UserResponse.YES,
            )

            mock.post(url + "/alertstatus", json={"error": None})
            succeeded = bot.update_alert_status(msg, cfg)

            assert succeeded

    def test_update_alert_status_request_failure(self):
        with requests_mock.mock() as mock:
            url = "http://mock.site"
            cfg = bot.RESTConfig(url, "token")
            msg = bot.UserResponseMessage(
                "id",
                bot.UserInfo("test@site.com", "tester"),
                bot.Confidence.HIGH,
                bot.UserResponse.YES,
            )

            mock.post(url + "/alertstatus", json={"error": None}, status_code=400)
            succeeded = bot.update_alert_status(msg, cfg)

            assert not succeeded

    def test_process_rejects_bad_messages(self):
        msg = {"details": {"identifier": "test"}}
        cfg = bot.RESTConfig("", "")

        (new_msg, new_meta) = bot.process(msg, {}, cfg)

        assert new_msg is None
        assert new_meta is None

    def test_process_invokes_update_for_good_messages(self):
        msg = {
            "details": {
                "identifier": "id",
                "user": {"email": "tester@site.com", "slack": "tester"},
                "identityConfidence": "high",
                "response": "yes",
            }
        }
        cfg = bot.RESTConfig("http://mock.site", "token")

        with requests_mock.mock() as mock:
            mock.post(cfg.url + "/alertstatus", json={"error": None})
            (new_msg, new_meta) = bot.process(msg, {}, cfg)

            assert len(mock.request_history) == 1

            req_json = mock.request_history[0].json()

            assert req_json == {
                "alert": "id",
                "status": "acknowledged",
                "user": {
                    "email": "tester@site.com",
                    "slack": "tester",
                },
                "identityConfidence": "high",
                "response": "yes",
            }

    def test_process_reformats_messages_for_elasticsearch(self):
        msg = {
            "details": {
                "identifier": "id",
                "user": {
                    "email": "tester@site.com",
                    "slack": "tester",
                },
                "identityConfidence": "high",
                "response": "yes",
            },
        }

        cfg = bot.RESTConfig("http://mock.site", "token")

        with requests_mock.mock() as mock:
            mock.post(cfg.url + "/alertstatus", json={"error": None})
            (new_msg, new_meta) = bot.process(msg, {}, cfg)

            assert "user" not in msg["details"]
            assert msg["category"] == "triagebot"
            assert msg["summary"] == "TriageBot Response: yes from: tester@site.com"
            assert msg["details"] == {
                "identifier": "id",
                "email": "tester@site.com",
                "slack": "tester",
                "identityConfidence": "high",
                "userresponse": "yes",
            }


class TestLambda:
    class MockStream:
        def __init__(self, payload):
            self.payload = payload

        def read(self, _bytes=None):
            return self.payload

    class MockLambda:
        def __init__(self, sess):
            self.session = sess

        def list_functions(self, **kwargs):
            self.session.calls["list_functions"].append(kwargs)

            dummy1 = {
                "FunctionName": "test1",
                "FunctionArn": "abc123",
                "Description": "First test function",
            }
            dummy2 = {
                "FunctionName": "MozDefSlackTraigeBotAPI-SlackTriageBotApiFunction-TEST",
                "FunctionArn": "def321",
                "Description": "Second test function",
            }

            if len(self.session.calls["list_functions"]) < 2:
                return {"NextMarker": "test", "Functions": [dummy1]}

            return {"Functions": [dummy2]}

        def invoke(self, **kwargs):
            self.session.calls["invoke"].append(kwargs)

            return {"Payload": TestLambda.MockStream(json.dumps({"result": "testurl"}))}

    class MockSession:
        def __init__(self):
            self.calls = {"list_functions": [], "invoke": []}

        def client(self, _service_name):
            return TestLambda.MockLambda(self)

    def test_discovery(self):
        session = TestLambda.MockSession()
        discover = bot._discovery(session)
        queue_url = discover()

        assert queue_url == "testurl"
        assert len(session.calls["list_functions"]) == 2
        assert len(session.calls["invoke"]) == 1
