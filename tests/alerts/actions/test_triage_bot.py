import json

import alerts.actions.triage_bot as bot

import requests_mock


def _ssh_sensitive_host_alert():
    return {
        "_index": "alerts-201911",
        "_type": "_doc",
        "_id": "jY29OGBBCfj908U9z3kd",
        "_version": 1,
        "_score": None,
        "_source": {
            "utctimestamp": "2019-11-04T23:04:36.351726+00:00",
            "severity": "WARNING",
            "summary": "Session opened on sensitive host by (1): tester [test@website.com]",
            "classname": "AlertGenericLoader:ssh_open_crit",
            "category": "session",
            "tags": ["session", "successful"],
            "events": [
                {
                    "documentindex": "events-20191104",
                    "documentsource": {
                        "receivedtimestamp": "2019-11-04T23:03:17.740981+00:00",
                        "mozdefhostname": "website.com",
                        "details": {
                            "program": "sshd",
                            "eventsourceipaddress": "1.2.3.4",
                            "username": "tester",
                        },
                        "tags": [".source.moz_net"],
                        "source": "authpriv",
                        "processname": "sshd",
                        "severity": "INFO",
                        "processid": "27767",
                        "summary": "pam_unix(sshd:session): session opened for user tester by (uid=0)",
                        "hostname": "a.host.website.com",
                        "facility": "authpriv",
                        "utctimestamp": "2019-11-04T23:03:17+00:00",
                        "timestamp": "2019-11-04T23:03:17+00:00",
                        "category": "syslog",
                        "type": "event",
                        "mozdef": {
                            "plugins": [
                                "parse_sshd", "parse_su", "sshdFindIP"
                            ]
                        },
                    },
                    "documentid": "X8-tOG4B-YuPuGRRXQta",
                }
            ],
            "channel": None,
            "url": "website.com",
            "notify_mozdefbot": True,
            "details": {"sites": []},
        },
        "fields": {
            "utctimestamp": ["2019-11-04T23:04:36.351Z"],
            "events.documentsource.utctimestamp": ["2019-11-04T23:03:17.000Z"],
            "events.documentsource.receivedtimestamp": ["2019-11-04T23:03:17.740Z"],
            "events.documentsource.timestamp": ["2019-11-04T23:03:17.000Z"],
        },
        "highlight": {
            "category": [
                "@kibana-highlighted-field@session@/kibana-highlighted-field@"
            ],
            "tags": ["@kibana-highlighted-field@session@/kibana-highlighted-field@"],
        },
        "sort": [1572908676351],
    }


def _duo_bypass_code_gen_alert():
    return {
        "_index": "alerts-201911",
        "_type": "_doc",
        "_id": "Rd8h4ukN9Ob7umH452xl",
        "_version": 1,
        "_score": None,
        "_source": {
            "utctimestamp": "2019-11-04T23:36:36.966791+00:00",
            "severity": "NOTICE",
            "summary": "DuoSecurity MFA Bypass codes generated (1): tester@website.com [a.website.com]",
            "classname": "AlertGenericLoader:duosecurity_bypass_generated",
            "category": "duo",
            "tags": ["duosecurity"],
            "events": [
                {
                    "documentindex": "events-20191104",
                    "documentsource": {
                        "receivedtimestamp": "2019-11-04T23:35:02.313328+00:00",
                        "mozdefhostname": "mozdef.website.com",
                        "details": {
                            "auto_generated": [],
                            "bypass": "",
                            "bypass_code_ids": 2,
                            "count": 10,
                            "eventtype": "administrator",
                            "object": "tester@website.com",
                            "remaining_uses": 1,
                            "user_id": "",
                            "username": "API",
                            "valid_secs": 0,
                        },
                        "category": "administration",
                        "hostname": "mozdef.website.com",
                        "processid": "23285",
                        "processname": "/opt/mozdef/envs/mozdef/cron/duo_logpull.py",
                        "severity": "INFO",
                        "summary": "bypass_create",
                        "tags": ["duosecurity"],
                        "utctimestamp": "2019-11-04T23:31:32+00:00",
                        "timestamp": "2019-11-04T23:31:32+00:00",
                        "type": "event",
                        "mozdef": {
                            "plugins": []
                        },
                        "source": "UNKNOWN",
                    },
                    "documentid": "wPPKOG4B-YuPuGRRc2s7",
                }
            ],
            "channel": None,
            "url": "website.com",
            "notify_mozdefbot": False,
            "details": {"sites": []},
        },
        "fields": {
            "utctimestamp": ["2019-11-04T23:36:36.966Z"],
            "events.documentsource.utctimestamp": ["2019-11-04T23:31:32.000Z"],
            "events.documentsource.receivedtimestamp": ["2019-11-04T23:35:02.313Z"],
            "events.documentsource.timestamp": ["2019-11-04T23:31:32.000Z"],
        },
        "highlight": {
            "category": ["@kibana-highlighted-field@duo@/kibana-highlighted-field@"],
            "tags": [
                "@kibana-highlighted-field@duosecurity@/kibana-highlighted-field@"
            ],
        },
        "sort": [1572910596966],
    }


def _duo_bypass_code_used_alert():
    return {
        "_index": "alerts-201910",
        "_type": "_doc",
        "_id": "n8uK26b1hx3f9OcLa72n",
        "_version": 1,
        "_score": None,
        "_source": {
            "utctimestamp": "2019-10-21T15:55:46.033838+00:00",
            "severity": "NOTICE",
            "summary": "DuoSecurity MFA Bypass codes used to log in (1): tester@website.com [website.com]",
            "classname": "AlertGenericLoader:duosecurity_bypass_used",
            "category": "bypassused",
            "tags": ["duosecurity", "used", "duo_bypass_codes_used"],
            "events": [
                {
                    "documentindex": "events-20191021",
                    "documentsource": {
                        "receivedtimestamp": "2019-10-21T15:50:02.339453+00:00",
                        "mozdefhostname": "mozdef.website.com",
                        "details": {
                            "auto_generated": [],
                            "bypass": "",
                            "bypass_code_ids": 2,
                            "count": 10,
                            "eventtype": "administrator",
                            "object": "tester@website.com",
                            "remaining_uses": 1,
                            "user_id": "",
                            "username": "API",
                            "valid_secs": 0,
                        },
                        "category": "administration",
                        "hostname": "mozdef.website.com",
                        "processid": "15428",
                        "processname": "/opt/mozdef/envs/mozdef/cron/duo_logpull.py",
                        "severity": "INFO",
                        "summary": "bypass_create",
                        "tags": ["duosecurity"],
                        "utctimestamp": "2019-10-21T15:48:43+00:00",
                        "timestamp": "2019-10-21T15:48:43+00:00",
                        "type": "event",
                        "mozdef": {
                            "plugins": []
                        },
                        "source": "UNKNOWN",
                        "alerts": [
                            {"index": "alerts-201910", "id": "J8b2dR63-kMa62bd-92E"}
                        ],
                        "alert_names": [
                            "AlertGenericLoader:duosecurity_bypass_generated"
                        ],
                    },
                    "documentid": "8iMaT3vSO0ddbCe7eaNQ",
                }
            ],
            "channel": None,
            "url": "website.com",
            "notify_mozdefbot": False,
            "details": {"sites": []},
        },
        "fields": {
            "events.documentsource.utctimestamp": ["2019-10-21T15:48:43.000Z"],
            "events.documentsource.receivedtimestamp": ["2019-10-21T15:50:02.339Z"],
            "events.documentsource.timestamp": ["2019-10-21T15:48:43.000Z"],
            "utctimestamp": ["2019-10-21T15:55:46.033Z"],
        },
        "highlight": {
            "category": [
                "@kibana-highlighted-field@bypassused@/kibana-highlighted-field@"
            ]
        },
        "sort": [1571673346033],
    }


def _ssh_access_releng_alert():
    return {
        "_index": "alerts-201911",
        "_type": "_doc",
        "_id": "8UtbAqm0dFl4qd9GwkA2",
        "_version": 1,
        "_score": None,
        "_source": {
            "utctimestamp": "2019-11-05T01:14:57.912292+00:00",
            "severity": "NOTICE",
            "summary": "SSH login from 10.49.48.100 on releng.website.com as user tester",
            "classname": "AlertAuthSignRelengSSH",
            "category": "access",
            "tags": ["ssh"],
            "events": [
                {
                    "documentindex": "events-20191105",
                    "documentsource": {
                        "receivedtimestamp": "2019-11-05T01:13:25.818826+00:00",
                        "mozdefhostname": "mozdef4.private.mdc1.mozilla.com",
                        "details": {
                            "id": "9637193494562349801",
                            "source_ip": "4.3.2.1",
                            "program": "sshd",
                            "message": "Accepted publickey for tester from 4.3.2.1 port 36998 ssh2",
                            "received_at": "2019-11-05T01:08:17Z",
                            "generated_at": "2019-11-04T17:08:17Z",
                            "display_received_at": "Nov 05 01:08:17",
                            "source_id": 835214730,
                            "source_name": "other.website.com",
                            "hostname": "releng.website.com",
                            "severity": "Info",
                            "facility": "Auth",
                            "sourceipaddress": "4.3.2.1",
                            "sourceipv4address": "4.3.2.1",
                        },
                        "tags": ["papertrail", "releng"],
                        "utctimestamp": "2019-11-04T17:08:17+00:00",
                        "timestamp": "2019-11-04T17:08:17+00:00",
                        "hostname": "releng.website.com",
                        "summary": "Accepted publickey for tester from 4.3.2.1 port 36998 ssh2",
                        "severity": "INFO",
                        "category": "syslog",
                        "type": "event",
                        "mozdef": {
                            "plugins": [
                                "parse_sshd",
                                "parse_su",
                                "sshdFindIP",
                                "ipFixup",
                                "geoip",
                            ]
                        },
                        "processid": "UNKNOWN",
                        "processname": "UNKNOWN",
                        "source": "UNKNOWN",
                    },
                    "documentid": "hsudfg92123ASDf234rm",
                }
            ],
            "channel": "infosec-releng-alerts",
            "notify_mozdefbot": True,
            "details": {
                "sourceipv4address": "4.3.2.1",
                "sourceipaddress": "4.3.2.1",
                "sites": [],
            },
        },
        "fields": {
            "utctimestamp": ["2019-11-05T01:14:57.912Z"],
            "events.documentsource.details.generated_at": ["2019-11-04T17:08:17.000Z"],
            "events.documentsource.details.received_at": ["2019-11-05T01:08:17.000Z"],
            "events.documentsource.utctimestamp": ["2019-11-04T17:08:17.000Z"],
            "events.documentsource.receivedtimestamp": ["2019-11-05T01:13:25.818Z"],
            "events.documentsource.timestamp": ["2019-11-04T17:08:17.000Z"],
        },
        "highlight": {
            "category": ["@kibana-highlighted-field@access@/kibana-highlighted-field@"],
            "tags": ["@kibana-highlighted-field@ssh@/kibana-highlighted-field@"],
        },
        "sort": [1572916497912],
    }


def _person_api_profile():
    return {
        "created": {"value": "2019-02-27T11:23:00.000Z"},
        "identities": {"mozilla_ldap_primary_email": {"value": "test@email.com"}},
        "first_name": {"value": "tester"},
        "last_name": {"value": "mctestperson"},
        "alternative_name": {"value": "testing"},
        "primary_email": {"value": "test@email.com"},
    }


class TestAlertRecognition(object):
    """Unit tests for the triage bot alert plugin.
    """

    mock_config = bot.Config(
        [
            "AlertGenericLoader:ssh_open_crit",
            "AlertAuthSignRelengSSH",
            "AlertGenericLoader:duosecurity_bypass_generated",
            "AlertGenericLoader:duosecurity_bypass_used"
        ],
        "", "", "", "", "", 0, "", "", "", 0, "", "", "", "", "", ""
    )

    def test_declines_unrecognized_alert(self):
        msg = _ssh_sensitive_host_alert()

        # Without the `session` tag, the alert should not fire.
        msg["_source"]["classname"] = "test"

        result = bot.try_make_outbound(msg, self.mock_config, "")

        assert result is None

    def test_recognizes_ssh_sensitive_host(self):
        msg = _ssh_sensitive_host_alert()

        result = bot.try_make_outbound(msg, self.mock_config, "")

        assert result is not None

    def test_recognizes_duo_bypass_codes_generated(self):
        msg = _duo_bypass_code_gen_alert()

        result = bot.try_make_outbound(msg, self.mock_config, "")

        assert result is not None

    def test_recognizes_duo_bypass_codes_used(self):
        msg = _duo_bypass_code_used_alert()

        result = bot.try_make_outbound(msg, self.mock_config, "")

        assert result is not None

    def test_recognizes_ssh_access_releng(self):
        msg = _ssh_access_releng_alert()

        result = bot.try_make_outbound(msg, self.mock_config, "")

        assert result is not None


class TestPersonAPI:
    """Unit tests for the Person API client code specific to the triage bot.
    """

    def test_authenticate_handles_well_formed_responses(self):
        params = bot.AuthParams(
            client_id="testid",
            client_secret="secret",
            audience="wonderful",
            scope="client:read",
            grants="read_acccess",
        )

        with requests_mock.mock() as mock_http:
            mock_http.post("http://person.api.com", json={"access_token": "testtoken"})

            tkn = bot.authenticate("http://person.api.com", params)

            assert tkn == "testtoken"

    def test_authenticate_handles_unexpected_response(self):
        params = bot.AuthParams(
            client_id="testid",
            client_secret="secret",
            audience="wonderful",
            scope="client:read",
            grants="read_acccess",
        )

        with requests_mock.mock() as mock_http:
            mock_http.post("http://person.api.com", text="Not authenticated")

            tkn = bot.authenticate("http://person.api.com", params)

            assert tkn is None

    def test_primary_username_handles_well_formed_responses(self):
        with requests_mock.mock() as mock_http:
            mock_http.get(
                "http://person.api.com/v2/user/primary_username/testuser",
                json=_person_api_profile(),
            )

            profile = bot.primary_username(
                "http://person.api.com", "testtoken", "testuser"
            )

            assert profile.primary_email == "test@email.com"
            assert profile.first_name == "tester"
            assert profile.alternative_name == "testing"

    def test_primary_username_handles_unexpected_response(self):
        with requests_mock.mock() as mock_http:
            mock_http.get(
                "http://person.api.com/v2/user/primary_username/testuser", json={}
            )

            profile = bot.primary_username(
                "http://person.api.com", "testtoken", "testuser"
            )

            assert profile is None


class TestLambda:
    class MockLambda:
        def __init__(self, sess):
            self.session = sess

        def invoke(self, **kwargs):
            self.session.calls["invoke"].append(kwargs)
            return {"StatusCode": 200}

        def list_functions(self, **kwargs):
            self.session.calls["list_functions"].append(kwargs)
            dummy1 = {
                "FunctionName": "test1",
                "FunctionArn": "abc123",
                "Description": "First test function",
            }
            dummy2 = {
                "FunctionName": "test2",
                "FunctionArn": "def321",
                "Description": "Second test function",
            }

            if len(self.session.calls["list_functions"]) < 2:
                return {"NextMarker": "test", "Functions": [dummy1]}

            return {"Functions": [dummy2]}

    class MockSession:
        def __init__(self):
            self.calls = {"list_functions": [], "invoke": []}

        def client(self, _service_name):
            return TestLambda.MockLambda(self)

    def test_discover(self):
        sess = TestLambda.MockSession()
        discover = bot._discovery(sess)
        functions = discover()

        assert len(functions) == 2
        assert functions[0].name == "test1"
        assert functions[1].name == "test2"
        assert len(sess.calls["list_functions"]) == 2
        assert "Marker" not in sess.calls["list_functions"][0]
        assert sess.calls["list_functions"][1]["Marker"] == "test"

    def test_dispatch(self):
        request = bot.AlertTriageRequest(
            identifier="abcdef0123",
            alert=bot.AlertLabel.SSH_ACCESS_SIGN_RELENG,
            summary="test alert",
            user="test@user.com",
            identityConfidence=bot.Confidence.HIGH,
        )

        sess = TestLambda.MockSession()
        dispatch = bot._dispatcher(sess)
        status = dispatch(request, "test_fn")

        assert status == bot.DispatchResult.SUCCESS
        assert len(sess.calls["invoke"]) == 1
        assert sess.calls["invoke"][0]["FunctionName"] == "test_fn"
        assert json.loads(sess.calls["invoke"][0]["Payload"]) == {
            "identifier": "abcdef0123",
            "alert": "ssh_access_sign_releng",
            "summary": "test alert",
            "user": "test@user.com",
            "identityConfidence": "high",
        }


class TestDuplicateChainManagement:
    mock_api_base = "http://mozdef.restapi.com"
    mock_api_token = "testtoken"

    def test_chain_retrieval(self):
        with requests_mock.mock() as mock_http:
            mock_http.get(
                "{}/alerttriagechain".format(self.mock_api_base),
                json={
                    "error": None,
                    "identifiers": ["id123"],
                    "created": "2020/02/19 1:23:45",
                    "modified": "2020/02/19 1:23:45",
                },
            )

            chain = bot._retrieve_duplicate_chain(
                bot.RESTConfig(self.mock_api_base, self.mock_api_token),
                bot.AlertLabel.SENSITIVE_HOST_SESSION,
                bot.Email("tester@mozilla.com"),
            )

            assert len(chain.identifiers) == 1
            assert chain.identifiers[0] == "id123"
            assert chain.created.year == 2020
            assert chain.modified.day == 19

    def test_chain_retrieval_failure(self):
        err_msg = "Chain does not exist"

        with requests_mock.mock() as mock_http:
            mock_http.get(
                "{}/alerttriagechain".format(self.mock_api_base),
                status_code=500,
                json={
                    "error": err_msg,
                    "identifiers": [],
                    "created": "2020/02/19 1:23:45",
                    "modified": "2020/02/19 1:23:45",
                },
            )

            try:
                bot._retrieve_duplicate_chain(
                    bot.RESTConfig(self.mock_api_base, self.mock_api_token),
                    bot.AlertLabel.SSH_ACCESS_SIGN_RELENG,
                    bot.Email("tester@mozilla.com"),
                )
            except bot.APIError as err:
                assert err.message == err_msg
                return

            assert False  # Shouldn't get here

    def test_chain_creation(self):
        with requests_mock.mock() as mock_http:
            mock_http.post(
                "{}/alerttriagechain".format(self.mock_api_base), json={"error": None}
            )

            success = bot._create_duplicate_chain(
                bot.RESTConfig(self.mock_api_base, self.mock_api_token),
                bot.AlertLabel.DUO_BYPASS_CODES_USED,
                bot.Email("tester@mozilla.com"),
                ["testid123"],
            )

            assert success

    def test_chain_creation_failure(self):
        err_msg = "Internal error"

        with requests_mock.mock() as mock_http:
            mock_http.post(
                "{}/alerttriagechain".format(self.mock_api_base),
                json={"error": err_msg},
            )

            try:
                bot._create_duplicate_chain(
                    bot.RESTConfig(self.mock_api_base, self.mock_api_token),
                    bot.AlertLabel.SENSITIVE_HOST_SESSION,
                    bot.Email("tester@mozilla.com"),
                    ["testid123"],
                )
            except bot.APIError as err:
                assert err.message == err_msg
                return

            assert False  # shouldn't get here

    def test_chain_update(self):
        with requests_mock.mock() as mock_http:
            mock_http.put(
                "{}/alerttriagechain".format(self.mock_api_base), json={"error": None}
            )

            success = bot._update_duplicate_chain(
                bot.RESTConfig(self.mock_api_base, self.mock_api_token),
                bot.AlertLabel.DUO_BYPASS_CODES_GENERATED,
                bot.Email("tester@mozilla.com"),
                ["testid123"],
            )

            assert success

    def test_chain_update_failure(self):
        err_msg = "No such chain exists"

        with requests_mock.mock() as mock_http:
            mock_http.put(
                "{}/alerttriagechain".format(self.mock_api_base),
                json={"error": err_msg},
            )

            try:
                bot._update_duplicate_chain(
                    bot.RESTConfig(self.mock_api_base, self.mock_api_token),
                    bot.AlertLabel.SENSITIVE_HOST_SESSION,
                    bot.Email("tester@mozilla.com"),
                    ["testid123"],
                )
            except bot.APIError as err:
                assert err.message == err_msg
                return

            assert False  # Shouldn't get here
