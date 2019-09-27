import mock

from mozdef_util.utilities.toUTC import toUTC
from mq.plugins.stackdriver_syslog import message


class TestStackdriverSyslog(object):
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
        metadata = {"index": "events"}
        event = {"category": "auditd", "tags": "syslog"}
        event["details"] = []

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    @mock.patch("mq.plugins.stackdriver.node")
    def test_mozdefhostname_mock_string(self, mock_path):
        mock_path.return_value = "samplehostname"
        event = {
            "category": "syslog",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T23:35:03.623648+00:00",
            "timestamp": "2019-09-26T23:34:57+00:00",
            "utctimestamp": "2019-09-26T23:34:57+00:00",
            "mozdefhostname": "samplehostname",
            "customendpoint": "",
            "details": {
                "insertId": "o1q62cdz5px7z1f9n",
                "labels": {"compute.googleapis.com/resource_name": "mozdefdevvm1"},
                "logName": "projects/mcd-001-252615/logs/syslog",
                "receiveTimestamp": "2019-09-26T23:35:02.439077355Z",
                "resource": {
                    "labels": {
                        "instance_id": "3401561556013842918",
                        "project_id": "mcd-001-252615",
                        "zone": "us-west2-a",
                    },
                    "type": "gce_instance",
                },
                "textPayload": "Sep 26 23:34:57 mozdefdevvm1 systemd: Started Session 315 of user mpurzynski.",
                "timestamp": "2019-09-26T23:34:57Z",
            },
        }
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result["mozdefhostname"] == "samplehostname"

    def verify_metadata(self, metadata):
        assert metadata["index"] == "events"

    def verify_defaults(self, result):
        assert result["source"] == "stackdriver"
        assert (
            toUTC(result["receivedtimestamp"]).isoformat()
            == result["receivedtimestamp"]
        )

    def test_defaults(self):
        event = {
            "category": "syslog",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T23:35:03.623648+00:00",
            "timestamp": "2019-09-26T23:34:57+00:00",
            "utctimestamp": "2019-09-26T23:34:57+00:00",
            "mozdefhostname": "samplehostname",
            "customendpoint": "",
            "details": {
                "insertId": "o1q62cdz5px7z1f9n",
                "labels": {"compute.googleapis.com/resource_name": "mozdefdevvm1"},
                "logName": "projects/mcd-001-252615/logs/syslog",
                "receiveTimestamp": "2019-09-26T23:35:02.439077355Z",
                "resource": {
                    "labels": {
                        "instance_id": "3401561556013842918",
                        "project_id": "mcd-001-252615",
                        "zone": "us-west2-a",
                    },
                    "type": "gce_instance",
                },
                "textPayload": "Sep 26 23:34:57 mozdefdevvm1 systemd: Started Session 315 of user mpurzynski.",
                "timestamp": "2019-09-26T23:34:57Z",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)

    def test_match_syslog(self):
        event = {
            "category": "syslog",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T23:35:03.623648+00:00",
            "timestamp": "2019-09-26T23:34:57+00:00",
            "utctimestamp": "2019-09-26T23:34:57+00:00",
            "mozdefhostname": "samplehostname",
            "customendpoint": "",
            "details": {
                "insertId": "o1q62cdz5px7z1f9n",
                "labels": {"compute.googleapis.com/resource_name": "mozdefdevvm1"},
                "logName": "projects/mcd-001-252615/logs/syslog",
                "receiveTimestamp": "2019-09-26T23:35:02.439077355Z",
                "resource": {
                    "labels": {
                        "instance_id": "3401561556013842918",
                        "project_id": "mcd-001-252615",
                        "zone": "us-west2-a",
                    },
                    "type": "gce_instance",
                },
                "textPayload": "Sep 26 23:34:57 mozdefdevvm1 systemd: Started Session 315 of user mpurzynski.",
                "timestamp": "2019-09-26T23:34:57Z",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "syslog"

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
                "auditkey": "pubsub",
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
                "originaluser": "syslog",
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

    def test_audit_data_access(self):
        event = {
            "category": "syslog",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T23:35:03.623648+00:00",
            "timestamp": "2019-09-26T23:34:57+00:00",
            "utctimestamp": "2019-09-26T23:34:57+00:00",
            "mozdefhostname": "samplehostname",
            "customendpoint": "",
            "details": {
                "insertId": "o1q62cdz5px7z1f9n",
                "labels": {"compute.googleapis.com/resource_name": "mozdefdevvm1"},
                "logName": "projects/mcd-001-252615/logs/syslog",
                "receiveTimestamp": "2019-09-26T23:35:02.439077355Z",
                "resource": {
                    "labels": {
                        "instance_id": "3401561556013842918",
                        "project_id": "mcd-001-252615",
                        "zone": "us-west2-a",
                    },
                    "type": "gce_instance",
                },
                "textPayload": "Sep 26 23:34:57 mozdefdevvm1 systemd: Started Session 315 of user alamakota.",
                "timestamp": "2019-09-26T23:34:57Z",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result["category"] == "syslog"
        assert result["summary"] == "Started Session 315 of user alamakota."
        assert result["processname"] == "systemd"
        assert result["hostname"] == "mozdefdevvm1"
        assert result["utctimestamp"] == "2019-09-26T23:34:57+00:00"
        assert result["timestamp"] == "2019-09-26T23:34:57+00:00"

