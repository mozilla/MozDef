import mock

from mozdef_util.utilities.toUTC import toUTC
from mq.plugins.stackdriver_audit import message


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
        cats = ["activity", "data_access"]

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
        assert (
            toUTC(result["receivedtimestamp"]).isoformat()
            == result["receivedtimestamp"]
        )

    def test_defaults(self):
        event = {
            "tags": ["pubsub"],
            "receivedtimestamp": "2019-09-26T21:36:46.512859+00:00",
            "mozdefhostname": "alamakota",
            "source": "stackdriver",
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
            "category": "data_access",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T21:36:46.512859+00:00",
            "timestamp": "2019-09-26T21:36:33.878395+00:00",
            "utctimestamp": "2019-09-26T21:36:33.878395+00:00",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "customendpoint": "",
            "details": {
                "insertId": "1trq6mpdd8sb",
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
                            "time": "2019-09-26T21:36:33.881423358Z",
                        },
                    },
                    "resourceName": "projects/mcd-001-252615",
                    "serviceName": "monitoring.googleapis.com",
                },
                "receiveTimestamp": "2019-09-26T21:36:34.774874835Z",
                "resource": {
                    "labels": {
                        "method": "google.monitoring.v3.AgentTranslationService.CreateCollectdTimeSeries",
                        "project_id": "mcd-001-252615",
                        "service": "monitoring.googleapis.com",
                    },
                    "type": "audited_resource",
                },
                "severity": "INFO",
                "timestamp": "2019-09-26T21:36:33.878395883Z",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        print(result)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result["category"] == "data_access"
        assert (
            result["details"]["username"]
            == event["details"]["gaudit"]["authenticationInfo"]["principalEmail"]
        )
        assert result["details"]["action"] == event["details"]["gaudit"]["methodName"]
        assert result["details"]["service"] == event["details"]["gaudit"]["serviceName"]
        assert (
            result["details"]["resourcename"]
            == event["details"]["gaudit"]["resourceName"]
        )
        assert result["details"]["resourcetype"] == event["details"]["resource"]["type"]
        assert (
            result["details"]["projectid"]
            == event["details"]["resource"]["labels"]["project_id"]
        )
        assert result["details"]["logname"] == event["details"]["logName"]
        assert (
            result["details"]["sdreceivetimestamp"]
            == event["details"]["receiveTimestamp"]
        )
        assert (
            result["details"]["sourceipaddress"]
            == event["details"]["gaudit"]["requestMetadata"]["callerIp"]
        )

    def test_audit_activity(self):
        event = {
            "category": "activity",
            "source": "stackdriver",
            "tags": [
                "projects/mcd-001-252615/subscriptions/mozdefsubscription",
                "pubsub",
                "stackdriver",
            ],
            "receivedtimestamp": "2019-09-26T22:45:58.094538+00:00",
            "timestamp": "2019-09-26T22:40:06.961000+00:00",
            "utctimestamp": "2019-09-26T22:40:06.961000+00:00",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "customendpoint": "",
            "details": {
                "insertId": "-zi2h8cd20yk",
                "logName": "projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Factivity",
                "operation": {
                    "id": "operation-1569537402872-5937c675c21bb-e3c92921-82cf6ecc",
                    "last": True,
                    "producer": "compute.googleapis.com",
                },
                "protoPayload": {
                    "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
                    "authenticationInfo": {
                        "principalEmail": "mpurzynski@gcp.infra.mozilla.com"
                    },
                    "methodName": "v1.compute.instances.delete",
                    "request": {
                        "@type": "type.googleapis.com/compute.instances.delete"
                    },
                    "requestMetadata": {
                        "callerIp": "63.245.222.198",
                        "callerSuppliedUserAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:71.0) Gecko/20100101 Firefox/71.0,gzip(gfe)",
                    },
                    "resourceName": "projects/mcd-001-252615/zones/us-central1-a/instances/instance-1",
                    "serviceName": "compute.googleapis.com",
                },
                "receiveTimestamp": "2019-09-26T22:40:07.584281344Z",
                "resource": {
                    "labels": {
                        "instance_id": "6732871386305430043",
                        "project_id": "mcd-001-252615",
                        "zone": "us-central1-a",
                    },
                    "type": "gce_instance",
                },
                "severity": "NOTICE",
                "timestamp": "2019-09-26T22:40:06.961Z",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        print(result)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result["category"] == "activity"
        assert (
            result["details"]["username"]
            == event["details"]["gaudit"]["authenticationInfo"]["principalEmail"]
        )
        assert result["details"]["action"] == event["details"]["gaudit"]["methodName"]
        assert result["details"]["service"] == event["details"]["gaudit"]["serviceName"]
        assert (
            result["details"]["resourcename"]
            == event["details"]["gaudit"]["resourceName"]
        )
        assert result["details"]["resourcetype"] == event["details"]["resource"]["type"]
        assert (
            result["details"]["projectid"]
            == event["details"]["resource"]["labels"]["project_id"]
        )
        assert result["details"]["logname"] == event["details"]["logName"]
        assert (
            result["details"]["sdreceivetimestamp"]
            == event["details"]["receiveTimestamp"]
        )
        assert (
            result["details"]["sourceipaddress"]
            == event["details"]["gaudit"]["requestMetadata"]["callerIp"]
        )

