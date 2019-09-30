import mock

from mozdef_util.utilities.toUTC import toUTC

from mq.plugins.stackdriver import message


class TestStackdriver(object):
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
        event = {"key1": "syslog", "tags": "pubsub"}
        event["details"] = []

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_notpubsub_log(self):
        metadata = {"index": "events"}
        event = {"key1": "syslog", "tags": "audit"}
        event["details"] = []

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    @mock.patch("mq.plugins.stackdriver.node")
    def test_mozdefhostname_mock_string(self, mock_path):
        mock_path.return_value = "samplehostname"
        event = {"tags": ["pubsub"]}
        event = {
            "tags": ["pubsub"],
            "receivedtimestamp": "2019-09-25T23:51:33.962907335Z",
            "mozdefhostname": "samplehostname",
        }
        event["details"] = {
            "logName": "projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access",
            "protoPayload": {
                "@type": "type.googleapis.com/google.cloud.audit.AuditLog"
            },
            "timestamp": "2019-09-25T23:51:33.962907335Z",
            "utctimestamp": "2019-09-25T23:51:33.962907335Z",
        }
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result["mozdefhostname"] == "samplehostname"

    def verify_metadata(self, metadata):
        assert metadata["index"] == "events"

    def verify_defaults(self, result):
        assert result["source"] == "stackdriver"
        assert result["customendpoint"] == ""
        assert (
            toUTC(result["receivedtimestamp"]).isoformat()
            == result["receivedtimestamp"]
        )

    def test_defaults(self):
        event = {
            "tags": ["pubsub"],
            "receivedtimestamp": "2019-09-25T23:51:33.962907335Z",
            "mozdefhostname": "alamakota",
        }
        event["details"] = {
            "logName": "projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access",
            "protoPayload": {
                "@type": "type.googleapis.com/google.cloud.audit.AuditLog"
            },
            "timestamp": "2019-09-25T23:51:33.962907335Z",
            "utctimestamp": "2019-09-25T23:51:33.962907335Z",
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result["category"] == "data_access"

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

    def test_audit_data_access(self):
        event = {
            "receivedtimestamp": "2019-09-26T19:16:08.714066+00:00",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "details": {
                "insertId": "1wjdblydcmhi",
                "logName": "projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access",
                "protoPayload": {
                    "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
                    "authenticationInfo": {
                        "principalEmail": "732492844671-compute@developer.gserviceaccount.com"
                    },
                    "authorizationInfo": [
                        {
                            "granted": True,
                            "permission": "monitoring.timeSeries.create",
                            "resource": "732492844671",
                            "resourceAttributes": {},
                        }
                    ],
                    "methodName": "google.monitoring.v3.AgentTranslationService.CreateCollectdTimeSeries",
                    "request": {
                        "@type": "type.googleapis.com/google.monitoring.v3.CreateCollectdTimeSeriesRequest",
                        "collectdVersion": "stackdriver_agent/5.5.2-1000.el7",
                        "name": "project/mcd-001-252615",
                        "resource": {
                            "labels": {
                                "instance_id": "3401561556013842918",
                                "zone": "us-west2-a",
                            },
                            "type": "gce_instance",
                        },
                    },
                    "requestMetadata": {
                        "callerIp": "34.94.75.196",
                        "callerNetwork": "//compute.googleapis.com/projects/mcd-001-252615/global/networks/__unknown__",
                        "callerSuppliedUserAgent": "stackdriver_agent/5.5.2-1000.el7,gzip(gfe)",
                        "destinationAttributes": {},
                        "requestAttributes": {
                            "auth": {},
                            "time": "2019-09-26T19:15:32.969371395Z",
                        },
                    },
                    "resourceName": "projects/mcd-001-252615",
                    "serviceName": "monitoring.googleapis.com",
                },
                "receiveTimestamp": "2019-09-26T19:15:33.172428475Z",
                "resource": {
                    "labels": {
                        "method": "google.monitoring.v3.AgentTranslationService.CreateCollectdTimeSeries",
                        "project_id": "mcd-001-252615",
                        "service": "monitoring.googleapis.com",
                    },
                    "type": "audited_resource",
                },
                "severity": "INFO",
                "timestamp": "2019-09-26T19:15:32.966429778Z",
            },
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
            ],
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result["category"] == "data_access"
