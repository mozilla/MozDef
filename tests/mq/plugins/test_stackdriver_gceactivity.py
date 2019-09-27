import mock

from mozdef_util.utilities.toUTC import toUTC
from mq.plugins.stackdriver_gceactivity import message


class TestStackdriverAudit(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {"index": "events"}

    # Should never match and be modified by the plugin
    def test_notags_log(self):
        metadata = {"index": "events"}
        event = {"key1": "syslog", "tags": "audit"}
        event["details"] = []

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_nodetails_log(self):
        metadata = {"index": "events"}
        event = {"key1": "syslog", "tags": "pubsub"}

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_logname_log(self):
        metadata = {"index": "events"}
        event = {"key1": "syslog", "tags": "stackdriver"}
        event["details"] = []

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_notoneofcats(self):
        cats = ["gceactivity"]

        metadata = {"index": "events"}
        event = {"key1": "syslog", "tags": "audit"}
        event["details"] = []

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    @mock.patch("mq.plugins.stackdriver.node")
    def test_mozdefhostname_mock_string(self, mock_path):
        mock_path.return_value = "samplehostname"
        event = {
            "category": "gceactivity",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T23:52:45.100733+00:00",
            "timestamp": "2019-09-26T23:52:43.299564+00:00",
            "utctimestamp": "2019-09-26T23:52:43.299564+00:00",
            "mozdefhostname": "samplehostname",
            "customendpoint": "",
            "details": {
                "insertId": "1e8s2bf39yzk2",
                "jsonPayload": {
                    "actor": {"user": "mpurzynski@gcp.infra.mozilla.com"},
                    "event_subtype": "compute.instances.reset",
                    "event_timestamp_us": "1569541963299564",
                    "event_type": "GCE_API_CALL",
                    "ip_address": "",
                    "operation": {
                        "id": "5765675022175760804",
                        "name": "operation-1569541962803-5937d77272889-bcc3286b-e21d8a9b",
                        "type": "operation",
                        "zone": "us-west2-a",
                    },
                    "request": {
                        "body": "null",
                        "url": "https://clients6.google.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1/reset?key=AIzaSyCI-zsRP85UVOi0DjtiCwWBwQ1djDy741g",
                    },
                    "resource": {
                        "id": "3401561556013842918",
                        "name": "mozdefdevvm1",
                        "type": "instance",
                        "zone": "us-west2-a",
                    },
                    "trace_id": "operation-1569541962803-5937d77272889-bcc3286b-e21d8a9b",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:71.0) Gecko/20100101 Firefox/71.0,gzip(gfe)",
                    "version": "1.2",
                },
                "labels": {
                    "compute.googleapis.com/resource_id": "3401561556013842918",
                    "compute.googleapis.com/resource_name": "mozdefdevvm1",
                    "compute.googleapis.com/resource_type": "instance",
                    "compute.googleapis.com/resource_zone": "us-west2-a",
                },
                "logName": "projects/mcd-001-252615/logs/compute.googleapis.com%2Factivity_log",
                "receiveTimestamp": "2019-09-26T23:52:43.375310707Z",
                "resource": {
                    "labels": {
                        "instance_id": "3401561556013842918",
                        "project_id": "mcd-001-252615",
                        "zone": "us-west2-a",
                    },
                    "type": "gce_instance",
                },
                "severity": "INFO",
                "timestamp": "2019-09-26T23:52:43.299564Z",
            },
        }
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result["mozdefhostname"] == "samplehostname"

    def verify_metadata(self, metadata):
        assert metadata["index"] == "events"

    def verify_defaults(self, result):
        assert result["source"] == "stackdriver"
        assert result["category"] == "gceactivity"
        assert (
            toUTC(result["receivedtimestamp"]).isoformat()
            == result["receivedtimestamp"]
        )

    def test_defaults(self):
        event = {
            "category": "gceactivity",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T23:52:45.100733+00:00",
            "timestamp": "2019-09-26T23:52:43.299564+00:00",
            "utctimestamp": "2019-09-26T23:52:43.299564+00:00",
            "mozdefhostname": "samplehostname",
            "customendpoint": "",
            "details": {
                "insertId": "1e8s2bf39yzk2",
                "jsonPayload": {
                    "actor": {"user": "mpurzynski@gcp.infra.mozilla.com"},
                    "event_subtype": "compute.instances.reset",
                    "event_timestamp_us": "1569541963299564",
                    "event_type": "GCE_API_CALL",
                    "ip_address": "",
                    "operation": {
                        "id": "5765675022175760804",
                        "name": "operation-1569541962803-5937d77272889-bcc3286b-e21d8a9b",
                        "type": "operation",
                        "zone": "us-west2-a",
                    },
                    "request": {
                        "body": "null",
                        "url": "https://clients6.google.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1/reset?key=AIzaSyCI-zsRP85UVOi0DjtiCwWBwQ1djDy741g",
                    },
                    "resource": {
                        "id": "3401561556013842918",
                        "name": "mozdefdevvm1",
                        "type": "instance",
                        "zone": "us-west2-a",
                    },
                    "trace_id": "operation-1569541962803-5937d77272889-bcc3286b-e21d8a9b",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:71.0) Gecko/20100101 Firefox/71.0,gzip(gfe)",
                    "version": "1.2",
                },
                "labels": {
                    "compute.googleapis.com/resource_id": "3401561556013842918",
                    "compute.googleapis.com/resource_name": "mozdefdevvm1",
                    "compute.googleapis.com/resource_type": "instance",
                    "compute.googleapis.com/resource_zone": "us-west2-a",
                },
                "logName": "projects/mcd-001-252615/logs/compute.googleapis.com%2Factivity_log",
                "receiveTimestamp": "2019-09-26T23:52:43.375310707Z",
                "resource": {
                    "labels": {
                        "instance_id": "3401561556013842918",
                        "project_id": "mcd-001-252615",
                        "zone": "us-west2-a",
                    },
                    "type": "gce_instance",
                },
                "severity": "INFO",
                "timestamp": "2019-09-26T23:52:43.299564Z",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)

    def test_nomatch_syslog(self):
        event = {
            "category": "syslog",
            "processid": "0",
            "receivedtimestamp": "2017-09-26T00:22:24.210945+00:00",
            "severity": "7",
            "utctimestamp": "2017-09-26T00:22:23+00:00",
            "timestamp": "2017-09-26T00:22:23+00:00",
            "hostname": "something1.test.com",
            "mozdefhostname": "something1.test.com",
            "summary": "Connection from 10.22.74.208 port 9071 on 10.22.74.45 pubsub stackdriver port 22\n",
            "eventsource": "systemslogs",
            "tags": "something",
            "details": {
                "processid": "21233",
                "sourceipv4address": "10.22.74.208",
                "hostname": "hostname1.subdomain.domain.com",
                "program": "sshd",
                "sourceipaddress": "10.22.74.208",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "syslog"
        assert result["eventsource"] == "systemslogs"
        assert result == event

    def test_nomatch_auditd(self):
        event = {
            "category": "execve",
            "processid": "0",
            "receivedtimestamp": "2017-09-26T00:36:27.463745+00:00",
            "severity": "INFO",
            "utctimestamp": "2017-09-26T00:36:27+00:00",
            "tags": ["audisp-json", "2.1.1", "audit"],
            "summary": "Execve: sh -c sudo squid proxy /usr/lib64/nagios/plugins/custom/check_auditd.sh",
            "processname": "audisp-json",
            "details": {
                "fsuid": "398",
                "tty": "(none)",
                "uid": "398",
                "process": "/bin/bash",
                "auditkey": "exec",
                "pid": "10553",
                "processname": "sh",
                "session": "16467",
                "fsgid": "398",
                "sgid": "398",
                "auditserial": "3834716",
                "inode": "1835094",
                "ouid": "0",
                "ogid": "0",
                "suid": "398",
                "originaluid": "0",
                "gid": "398",
                "originaluser": "pubsub",
                "ppid": "10552",
                "cwd": "/",
                "parentprocess": "stackdriver",
                "euid": "398",
                "path": "/bin/sh",
                "rdev": "00:00",
                "dev": "08:03",
                "egid": "398",
                "command": "sh -c sudo /usr/lib64/nagios/plugins/custom/check_auditd.sh",
                "mode": "0100755",
                "user": "squid",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "execve"
        assert "eventsource" not in result
        assert result == event

    def test_gceactivity(self):
        event = {
            "category": "gceactivity",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T23:52:45.100733+00:00",
            "timestamp": "2019-09-26T23:52:43.299564+00:00",
            "utctimestamp": "2019-09-26T23:52:43.299564+00:00",
            "mozdefhostname": "samplehostname",
            "customendpoint": "",
            "details": {
                "insertId": "1e8s2bf39yzk2",
                "jsonPayload": {
                    "actor": {"user": "mpurzynski@gcp.infra.mozilla.com"},
                    "event_subtype": "compute.instances.reset",
                    "event_timestamp_us": "1569541963299564",
                    "event_type": "GCE_API_CALL",
                    "ip_address": "",
                    "operation": {
                        "id": "5765675022175760804",
                        "name": "operation-1569541962803-5937d77272889-bcc3286b-e21d8a9b",
                        "type": "operation",
                        "zone": "us-west2-a",
                    },
                    "request": {
                        "body": "null",
                        "url": "https://clients6.google.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1/reset?key=AIzaSyCI-zsRP85UVOi0DjtiCwWBwQ1djDy741g",
                    },
                    "resource": {
                        "id": "3401561556013842918",
                        "name": "mozdefdevvm1",
                        "type": "instance",
                        "zone": "us-west2-a",
                    },
                    "trace_id": "operation-1569541962803-5937d77272889-bcc3286b-e21d8a9b",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:71.0) Gecko/20100101 Firefox/71.0,gzip(gfe)",
                    "version": "1.2",
                },
                "labels": {
                    "compute.googleapis.com/resource_id": "3401561556013842918",
                    "compute.googleapis.com/resource_name": "mozdefdevvm1",
                    "compute.googleapis.com/resource_type": "instance",
                    "compute.googleapis.com/resource_zone": "us-west2-a",
                },
                "logName": "projects/mcd-001-252615/logs/compute.googleapis.com%2Factivity_log",
                "receiveTimestamp": "2019-09-26T23:52:43.375310707Z",
                "resource": {
                    "labels": {
                        "instance_id": "3401561556013842918",
                        "project_id": "mcd-001-252615",
                        "zone": "us-west2-a",
                    },
                    "type": "gce_instance",
                },
                "severity": "INFO",
                "timestamp": "2019-09-26T23:52:43.299564Z",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        print(result)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert (
            result["details"]["username"]
            == event["details"]["gceactivity"]["actor"]["user"]
        )
        assert (
            result["details"]["action"]
            == event["details"]["gceactivity"]["event_subtype"]
        )
        assert (
            result["details"]["actiongroup"]
            == event["details"]["gceactivity"]["event_type"]
        )
        assert (
            result["details"]["resourcename"]
            == event["details"]["gceactivity"]["resource"]["name"]
        )
        assert (
            result["details"]["resourcetype"]
            == event["details"]["gceactivity"]["resource"]["type"]
        )
        assert (
            result["details"]["resourceid"]
            == event["details"]["gceactivity"]["resource"]["id"]
        )
        assert (
            result["details"]["projectid"]
            == event["details"]["resource"]["labels"]["project_id"]
        )
        assert result["details"]["logname"] == event["details"]["logName"]
        assert (
            result["details"]["sdreceivetimestamp"]
            == event["details"]["receiveTimestamp"]
        )

