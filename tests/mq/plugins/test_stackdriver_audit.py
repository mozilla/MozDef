from mozdef_util.utilities.toUTC import toUTC
from mq.plugins.stackdriver_audit import message


class TestStackDriverAudit(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {"index": "events"}

    # Should never match and be modified by the plugin
    def test_notags_log(self):
        metadata = {"index": "events"}
        event = {
            "source": "stackdriver",
            "details": {"logName": "projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access"},
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def test_wrongtags_log(self):
        metadata = {"index": "events"}
        event = {
            "tags": "audit",
            "source": "stackdriver",
            "details": {"logName": "projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access"},
        }

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
            'category': 'data_access',
            'source': 'stackdriver',
            'tags': ['projects/mcd-001-252615/subscriptions/mozdefsubscription', 'pubsub', 'stackdriver'],
            'receivedtimestamp': '2019-11-21T23:53:36.695909+00:00',
            'timestamp': '2019-11-21T23:45:34.930000+00:00',
            'utctimestamp': '2019-11-21T23:45:34.930000+00:00',
            'mozdefhostname': 'mozdefqa2.private.mdc1.mozilla.com',
            'customendpoint': '',
            'details': {
                'insertId': 'utar0xd1qjq',
                'logName': 'projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access',
                'protoPayload': {
                    '@type': 'type.googleapis.com/google.cloud.audit.AuditLog',
                    'authenticationInfo': {},
                    'authorizationInfo': [
                        {
                            'permission': 'storage.buckets.get',
                            'resource': 'projects/_/buckets/mcd-001-252615.appspot.com',
                            'resourceAttributes': {},
                        },
                        {
                            'permission': 'storage.buckets.getIamPolicy',
                            'resource': 'projects/_/buckets/mcd-001-252615.appspot.com',
                            'resourceAttributes': {},
                        },
                    ],
                    'methodName': 'storage.buckets.get',
                    'requestMetadata': {
                        'destinationAttributes': {},
                        'requestAttributes': {'auth': {}, 'time': '2019-11-21T23:45:34.949Z'},
                    },
                    'resourceLocation': {'currentLocations': ['asia-northeast2']},
                    'resourceName': 'projects/_/buckets/mcd-001-252615.appspot.com',
                    'serviceName': 'storage.googleapis.com',
                    'status': {'code': 7, 'message': 'PERMISSION_DENIED'},
                },
                'receiveTimestamp': '2019-11-21T23:45:35.521115967Z',
                'resource': {
                    'labels': {
                        'bucket_name': 'mcd-001-252615.appspot.com',
                        'location': 'asia-northeast2',
                        'project_id': 'mcd-001-252615',
                    },
                    'type': 'gcs_bucket',
                },
                'severity': 'ERROR',
                'timestamp': '2019-11-21T23:45:34.93Z',
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

    def test_stackdriver_audit_data_access(self):
        event = {
            'category': 'data_access',
            'source': 'stackdriver',
            'tags': ['projects/mcd-001-252615/subscriptions/mozdefsubscription', 'pubsub', 'stackdriver'],
            'receivedtimestamp': '2019-11-21T22:43:10.041549+00:00',
            'timestamp': '2019-11-21T22:42:25.759000+00:00',
            'utctimestamp': '2019-11-21T22:42:25.759000+00:00',
            'mozdefhostname': 'mozdefqa2.private.mdc1.mozilla.com',
            'customendpoint': '',
            'details': {
                'insertId': '-81ga0vdqblo',
                'logName': 'projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Fdata_access',
                'protoPayload': {
                    '@type': 'type.googleapis.com/google.cloud.audit.AuditLog',
                    'authenticationInfo': {'principalEmail': '732492844671-compute@developer.gserviceaccount.com'},
                    'authorizationInfo': [
                        {
                            'granted': True,
                            'permission': 'compute.instances.list',
                            'resourceAttributes': {
                                'name': 'projects/mcd-001-252615',
                                'service': 'resourcemanager',
                                'type': 'resourcemanager.projects',
                            },
                        }
                    ],
                    'methodName': 'beta.compute.instances.aggregatedList',
                    'numResponseItems': '61',
                    'request': {'@type': 'type.googleapis.com/compute.instances.aggregatedList'},
                    'requestMetadata': {
                        'callerIp': '2620:101:80fb:224:2864:cebc:a1e:640c',
                        'callerSuppliedUserAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0,gzip(gfe),gzip(gfe)',
                        'destinationAttributes': {},
                        'requestAttributes': {'auth': {}, 'time': '2019-11-21T22:42:26.336Z'},
                    },
                    'resourceLocation': {'currentLocations': ['global']},
                    'resourceName': 'projects/mcd-001-252615/global/instances',
                    'serviceName': 'compute.googleapis.com',
                },
                'receiveTimestamp': '2019-11-21T22:42:26.904624537Z',
                'resource': {
                    'labels': {
                        'location': 'global',
                        'method': 'compute.instances.aggregatedList',
                        'project_id': 'mcd-001-252615',
                        'service': 'compute.googleapis.com',
                        'version': 'beta',
                    },
                    'type': 'api',
                },
                'severity': 'INFO',
                'timestamp': '2019-11-21T22:42:25.759Z',
            },
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "data_access"
        assert result["details"]["action"] == "beta.compute.instances.aggregatedList"
        assert result["details"]["gaudit"]["authenticationInfo"]["principalEmail"] == "732492844671-compute@developer.gserviceaccount.com"
        assert result["details"]["gaudit"]["methodName"] == "beta.compute.instances.aggregatedList"
        assert result["details"]["projectid"] == "mcd-001-252615"
        assert result["details"]["service"] == "compute.googleapis.com"
        assert result["details"]["sourceipaddress"] == "2620:101:80fb:224:2864:cebc:a1e:640c"
        assert result["details"]["username"] == "732492844671-compute@developer.gserviceaccount.com"
        assert result["source"] == "stackdriver"
        assert result["utctimestamp"] == "2019-11-21T22:42:25.759000+00:00"
        assert "protoPayload" not in result["details"]

    def test_stackdriver_audit_activity(self):
        event = {
            'category': 'activity',
            'source': 'stackdriver',
            'tags': ['projects/mcd-001-252615/subscriptions/mozdefsubscription', 'pubsub', 'stackdriver'],
            'receivedtimestamp': '2019-11-22T00:03:20.621831+00:00',
            'timestamp': '2019-11-22T00:03:18.137000+00:00',
            'utctimestamp': '2019-11-22T00:03:18.137000+00:00',
            'mozdefhostname': 'mozdefqa2.private.mdc1.mozilla.com',
            'customendpoint': '',
            'details': {
                'insertId': '8w7e9jdcf16',
                'logName': 'projects/mcd-001-252615/logs/cloudaudit.googleapis.com%2Factivity',
                'operation': {
                    'first': True,
                    'id': 'operation-1574380998061-597e424216be9-afa9fe5d-5f5c5c27',
                    'producer': 'type.googleapis.com',
                },
                'protoPayload': {
                    '@type': 'type.googleapis.com/google.cloud.audit.AuditLog',
                    'authenticationInfo': {'principalEmail': 'onceuponatime@inagalaxynottoofaraway.com'},
                    'authorizationInfo': [
                        {
                            'granted': True,
                            'permission': 'compute.instances.reset',
                            'resourceAttributes': {
                                'name': 'projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1',
                                'service': 'compute',
                                'type': 'compute.instances',
                            },
                        }
                    ],
                    'methodName': 'v1.compute.instances.reset',
                    'request': {'@type': 'type.googleapis.com/compute.instances.reset'},
                    'requestMetadata': {
                        'callerIp': '2620:101:80fb:224:a889:abf2:7b0b:f928',
                        'callerSuppliedUserAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0,gzip(gfe),gzip(gfe)',
                        'destinationAttributes': {},
                        'requestAttributes': {'auth': {}, 'time': '2019-11-22T00:03:18.826Z'},
                    },
                    'resourceLocation': {'currentLocations': ['us-west2-a']},
                    'resourceName': 'projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1',
                    'response': {
                        '@type': 'type.googleapis.com/operation',
                        'id': '868140788263590697',
                        'insertTime': '2019-11-21T16:03:18.588-08:00',
                        'name': 'operation-1574380998061-597e424216be9-afa9fe5d-5f5c5c27',
                        'operationType': 'reset',
                        'progress': '0',
                        'selfLink': 'https://www.googleapis.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a/operations/operation-1574380998061-597e424216be9-afa9fe5d-5f5c5c27',
                        'selfLinkWithId': 'https://www.googleapis.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a/operations/868140788263590697',
                        'startTime': '2019-11-21T16:03:18.597-08:00',
                        'status': 'RUNNING',
                        'targetId': '3401561556013842918',
                        'targetLink': 'https://www.googleapis.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1',
                        'user': 'onceuponatime@inagalaxynottoofaraway.com',
                        'zone': 'https://www.googleapis.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a',
                    },
                    'serviceName': 'compute.googleapis.com',
                },
                'receiveTimestamp': '2019-11-22T00:03:19.525805615Z',
                'resource': {
                    'labels': {
                        'instance_id': '3401561556013842918',
                        'project_id': 'mcd-001-252615',
                        'zone': 'us-west2-a',
                    },
                    'type': 'gce_instance',
                },
                'severity': 'NOTICE',
                'timestamp': '2019-11-22T00:03:18.137Z',
            },
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "activity"
        assert result["details"]["action"] == "v1.compute.instances.reset"
        assert result["details"]["gaudit"]["authenticationInfo"]["principalEmail"] == "onceuponatime@inagalaxynottoofaraway.com"
        assert result["details"]["gaudit"]["methodName"] == "v1.compute.instances.reset"
        assert result["details"]["operation"]["producer"] == "type.googleapis.com"
        assert result["details"]["projectid"] == "mcd-001-252615"
        assert result["details"]["resourcename"] == "projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1"
        assert result["details"]["resourcetype"] == "gce_instance"
        assert result["details"]["service"] == "compute.googleapis.com"
        assert result["details"]["username"] == "onceuponatime@inagalaxynottoofaraway.com"
        assert result["summary"] == "onceuponatime@inagalaxynottoofaraway.com executed v1.compute.instances.reset on projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1"

        assert "protoPayload" not in result["details"]
