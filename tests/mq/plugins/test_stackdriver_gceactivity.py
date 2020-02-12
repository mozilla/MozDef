from mozdef_util.utilities.toUTC import toUTC
from mq.plugins.stackdriver_gceactivity import message


class TestStackDriverGCEActivity(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {"index": "events"}

    def test_notags_log(self):
        metadata = {"index": "events"}
        event = {"category": "gceactivity"}

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def test_nocategory_log(self):
        metadata = {"index": "events"}
        event = {"tags": "audit"}

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_wrongtags_log(self):
        metadata = {"index": "events"}
        event = {"tags": "audit", "category": "gceactivity"}

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def verify_metadata(self, metadata):
        assert metadata["index"] == "events"

    def verify_defaults(self, result):
        assert result["category"] == "gceactivity"
        assert toUTC(result["receivedtimestamp"]).isoformat() == result["receivedtimestamp"]

    def test_defaults(self):
        event = {
            'category': 'gceactivity',
            'source': 'stackdriver',
            'tags': ['projects/mcd-001-252615/subscriptions/mozdefsubscription', 'pubsub', 'stackdriver'],
            'receivedtimestamp': '2019-11-22T01:23:49.238723+00:00',
            'timestamp': '2019-11-22T01:23:47.936931+00:00',
            'utctimestamp': '2019-11-22T01:23:47.936931+00:00',
            'mozdefhostname': 'mozdefqa2.private.mdc1.mozilla.com',
            'customendpoint': '',
            'details': {
                'insertId': '1y7iw8ag15tmjpz',
                'jsonPayload': {
                    'actor': {'user': 'luke@or.not'},
                    'event_subtype': 'compute.instances.reset',
                    'event_timestamp_us': '1574385827936931',
                    'event_type': 'GCE_API_CALL',
                    'ip_address': '',
                    'operation': {
                        'id': '2169930274576172620',
                        'name': 'operation-1574385827284-597e543f984be-d1640557-51c07a30',
                        'type': 'operation',
                        'zone': 'us-west2-a',
                    },
                    'request': {
                        'body': 'null',
                        'url': 'https://compute.googleapis.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1/reset?key=AIzaSyDWUi9T78xEO-m10evQANR7TMSiB_bjyNc',
                    },
                    'resource': {
                        'id': '3401561556013842918',
                        'name': 'mozdefdevvm1',
                        'type': 'instance',
                        'zone': 'us-west2-a',
                    },
                    'trace_id': 'operation-1574385827284-597e543f984be-d1640557-51c07a30',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0,gzip(gfe),gzip(gfe)',
                    'version': '1.2',
                },
                'labels': {
                    'compute.googleapis.com/resource_id': '3401561556013842918',
                    'compute.googleapis.com/resource_name': 'mozdefdevvm1',
                    'compute.googleapis.com/resource_type': 'instance',
                    'compute.googleapis.com/resource_zone': 'us-west2-a',
                },
                'logName': 'projects/mcd-001-252615/logs/compute.googleapis.com%2Factivity_log',
                'receiveTimestamp': '2019-11-22T01:23:47.988998161Z',
                'resource': {
                    'labels': {
                        'instance_id': '3401561556013842918',
                        'project_id': 'mcd-001-252615',
                        'zone': 'us-west2-a',
                    },
                    'type': 'gce_instance',
                },
                'severity': 'INFO',
                'timestamp': '2019-11-22T01:23:47.936931Z',
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

    def test_stackdriver(self):
        event = {
            'category': 'gceactivity',
            'source': 'stackdriver',
            'tags': ['projects/mcd-001-252615/subscriptions/mozdefsubscription', 'pubsub', 'stackdriver'],
            'receivedtimestamp': '2019-11-22T01:23:49.238723+00:00',
            'timestamp': '2019-11-22T01:23:47.936931+00:00',
            'utctimestamp': '2019-11-22T01:23:47.936931+00:00',
            'mozdefhostname': 'mozdefqa2.private.mdc1.mozilla.com',
            'customendpoint': '',
            'details': {
                'insertId': '1y7iw8ag15tmjpz',
                'jsonPayload': {
                    'actor': {'user': 'luke@or.not'},
                    'event_subtype': 'compute.instances.reset',
                    'event_timestamp_us': '1574385827936931',
                    'event_type': 'GCE_API_CALL',
                    'ip_address': '',
                    'operation': {
                        'id': '2169930274576172620',
                        'name': 'operation-1574385827284-597e543f984be-d1640557-51c07a30',
                        'type': 'operation',
                        'zone': 'us-west2-a',
                    },
                    'request': {
                        'body': 'null',
                        'url': 'https://compute.googleapis.com/compute/v1/projects/mcd-001-252615/zones/us-west2-a/instances/mozdefdevvm1/reset?key=AIzaSyDWUi9T78xEO-m10evQANR7TMSiB_bjyNc',
                    },
                    'resource': {
                        'id': '3401561556013842918',
                        'name': 'mozdefdevvm1',
                        'type': 'instance',
                        'zone': 'us-west2-a',
                    },
                    'trace_id': 'operation-1574385827284-597e543f984be-d1640557-51c07a30',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0,gzip(gfe),gzip(gfe)',
                    'version': '1.2',
                },
                'labels': {
                    'compute.googleapis.com/resource_id': '3401561556013842918',
                    'compute.googleapis.com/resource_name': 'mozdefdevvm1',
                    'compute.googleapis.com/resource_type': 'instance',
                    'compute.googleapis.com/resource_zone': 'us-west2-a',
                },
                'logName': 'projects/mcd-001-252615/logs/compute.googleapis.com%2Factivity_log',
                'receiveTimestamp': '2019-11-22T01:23:47.988998161Z',
                'resource': {
                    'labels': {
                        'instance_id': '3401561556013842918',
                        'project_id': 'mcd-001-252615',
                        'zone': 'us-west2-a',
                    },
                    'type': 'gce_instance',
                },
                'severity': 'INFO',
                'timestamp': '2019-11-22T01:23:47.936931Z',
            },
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)

        assert result["details"]["action"] == "compute.instances.reset"
        assert result["details"]["gceactivity"]["resource"]["id"] == "3401561556013842918"
        assert result["utctimestamp"] == "2019-11-22T01:23:47.936931+00:00"
        assert result["details"]["username"] == "luke@or.not"
        assert result["details"]["service"] == "compute.googleapis.com"
        assert result["summary"] == "luke@or.not executed compute.instances.reset on mozdefdevvm1"
        assert "jsonPayload" not in result["details"]
