from mozdef_util.utilities.toUTC import toUTC
from mq.plugins.stackdriver import message


class TestStackDriver(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {"index": "events"}

    # Should never match and be modified by the plugin
    def test_nodetails_log(self):
        metadata = {"index": "events"}
        event = {"tags": "pubsub"}

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def verify_metadata(self, metadata):
        assert metadata["index"] == "events"

    def verify_defaults(self, result):
        assert result["category"] == "data_access"
        assert toUTC(result["receivedtimestamp"]).isoformat() == result["receivedtimestamp"]

    def test_defaults(self):
        event = {
            "receivedtimestamp": "2019-11-21T22:43:10.041549+00:00",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "details": {
                "insertId": "-81ga0vdqblo",
                "logName": "projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access",
                "protoPayload": {
                    "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
                    "authenticationInfo": {"principalEmail": "mpurzynski@gcp.infra.mozilla.com"},
                    "authorizationInfo": [
                        {
                            "granted": True,
                            "permission": "compute.instances.list",
                            "resourceAttributes": {
                                "name": "projects/mcd-001-252615",
                                "service": "resourcemanager",
                                "type": "resourcemanager.projects",
                            },
                        }
                    ],
                    "methodName": "beta.compute.instances.aggregatedList",
                    "numResponseItems": "61",
                    "request": {"@type": "type.googleapis.com/compute.instances.aggregatedList"},
                    "requestMetadata": {
                        "callerIp": "2620:101:80fb:224:2864:cebc:a1e:640c",
                        "callerSuppliedUserAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0,gzip(gfe),gzip(gfe)",
                        "destinationAttributes": {},
                        "requestAttributes": {"auth": {}, "time": "2019-11-21T22:42:26.336Z",},
                    },
                    "resourceLocation": {"currentLocations": ["global"]},
                    "resourceName": "projects/mcd-001-252615/global/instances",
                    "serviceName": "compute.googleapis.com",
                },
                "receiveTimestamp": "2019-11-21T22:42:26.904624537Z",
                "resource": {
                    "labels": {
                        "location": "global",
                        "method": "compute.instances.aggregatedList",
                        "project_id": "mcd-001-252615",
                        "service": "compute.googleapis.com",
                        "version": "beta",
                    },
                    "type": "api",
                },
                "severity": "INFO",
                "timestamp": "2019-11-21T22:42:25.759Z",
            },
            "tags": ["projects/mcd-001-252615/subscriptions/mozdefsubscription", "pubsub",],
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

    def test_stackdriver(self):
        event = {
            "receivedtimestamp": "2019-11-21T22:43:10.041549+00:00",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "details": {
                "insertId": "-81ga0vdqblo",
                "logName": "projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access",
                "protoPayload": {
                    "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
                    "authenticationInfo": {"principalEmail": "mpurzynski@gcp.infra.mozilla.com"},
                    "authorizationInfo": [
                        {
                            "granted": True,
                            "permission": "compute.instances.list",
                            "resourceAttributes": {
                                "name": "projects/mcd-001-252615",
                                "service": "resourcemanager",
                                "type": "resourcemanager.projects",
                            },
                        }
                    ],
                    "methodName": "beta.compute.instances.aggregatedList",
                    "numResponseItems": "61",
                    "request": {"@type": "type.googleapis.com/compute.instances.aggregatedList"},
                    "requestMetadata": {
                        "callerIp": "2620:101:80fb:224:2864:cebc:a1e:640c",
                        "callerSuppliedUserAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0,gzip(gfe),gzip(gfe)",
                        "destinationAttributes": {},
                        "requestAttributes": {"auth": {}, "time": "2019-11-21T22:42:26.336Z",},
                    },
                    "resourceLocation": {"currentLocations": ["global"]},
                    "resourceName": "projects/mcd-001-252615/global/instances",
                    "serviceName": "compute.googleapis.com",
                },
                "receiveTimestamp": "2019-11-21T22:42:26.904624537Z",
                "resource": {
                    "labels": {
                        "location": "global",
                        "method": "compute.instances.aggregatedList",
                        "project_id": "mcd-001-252615",
                        "service": "compute.googleapis.com",
                        "version": "beta",
                    },
                    "type": "api",
                },
                "severity": "INFO",
                "timestamp": "2019-11-21T22:42:25.759Z",
            },
            "tags": ["projects/mcd-001-252615/subscriptions/mozdefsubscription", "pubsub",],
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "data_access"
        assert result["details"]["protoPayload"]["@type"] == "type.googleapis.com/google.cloud.audit.AuditLog"
