from mozdef_util.utilities.toUTC import toUTC
from mq.plugins.stackdriver_syslog import message


class TestStackDriverSyslog(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {"index": "events"}

    # Should never match and be modified by the plugin
    def test_notags_log(self):
        metadata = {"index": "events"}
        event = {
            "source": "stackdriver",
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def test_wrongtags_log(self):
        metadata = {"index": "events"}
        event = {
            "tags": "audit",
            "source": "stackdriver",
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def test_wrongcategory_log(self):
        metadata = {"index": "events"}
        event = {
            "tags": "audit",
            "source": "stackdriver",
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def verify_metadata(self, metadata):
        assert metadata["index"] == "events"

    def verify_defaults(self, result):
        assert result["category"] == "syslog"
        assert toUTC(result["receivedtimestamp"]).isoformat() == result["receivedtimestamp"]

    def test_defaults(self):
        event = {
            'category': 'syslog',
            'source': 'stackdriver',
            'tags': ['projects/mcd-001-252615/subscriptions/mozdefsubscription', 'pubsub', 'stackdriver'],
            'receivedtimestamp': '2019-11-22T00:32:20.078819+00:00',
            'timestamp': '2019-11-22T00:32  :13+00:00',
            'utctimestamp': '2019-11-22T00:32:13+00:00',
            'mozdefhostname': 'mozdefqa2.private.mdc1.mozilla.com',
            'customendpoint': '',
            'details': {
                'insertId': '5s8y8sgro37aodjds',
                'labels': {'compute.googleapis.com/resource_name': 'mozdefdevvm1'},
                'logName': 'projects/mcd-001-252615/logs/syslog',
                'receiveTimestamp': '2019-11-22T00:32:18.754424975Z',
                'resource': {
                    'labels': {
                        'instance_id': '3401561556013842918',
                        'project_id': 'mcd-001-252615',
                        'zone': 'us-west2-a',
                    },
                    'type': 'gce_instance',
                },
                'textPayload': 'Nov 22 00:32:13 mozdefdevvm1 systemd: Started Session 1 of user mpurzynski.',
                'timestamp': '2019-11-22T00:32:13Z',
            },
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)

    def test_nomatch_generic_syslog(self):
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

    def test_stackdriver_syslog(self):
        event = {
            'category': 'syslog',
            'source': 'stackdriver',
            'tags': ['projects/mcd-001-252615/subscriptions/mozdefsubscription', 'pubsub', 'stackdriver'],
            'receivedtimestamp': '2019-11-22T00:32:20.078819+00:00',
            'timestamp': '2019-11-22T00:32  :13+00:00',
            'utctimestamp': '2019-11-22T00:32:13+00:00',
            'mozdefhostname': 'mozdefqa2.private.mdc1.mozilla.com',
            'customendpoint': '',
            'details': {
                'insertId': '5s8y8sgro37aodjds',
                'labels': {'compute.googleapis.com/resource_name': 'mozdefdevvm1'},
                'logName': 'projects/mcd-001-252615/logs/syslog',
                'receiveTimestamp': '2019-11-22T00:32:18.754424975Z',
                'resource': {
                    'labels': {
                        'instance_id': '3401561556013842918',
                        'project_id': 'mcd-001-252615',
                        'zone': 'us-west2-a',
                    },
                    'type': 'gce_instance',
                },
                'textPayload': 'Nov 22 00:32:13 mozdefdevvm1 systemd: Started Session 1 of user yoda.',
                'timestamp': '2019-11-22T00:32:13Z',
            },
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "syslog"
        assert result["source"] == "stackdriver"
        assert result["utctimestamp"] == "2019-11-22T00:32:13+00:00"
        assert result["hostname"] == "mozdefdevvm1"
        assert result["processname"] == "systemd"
        assert result["summary"] == "Started Session 1 of user yoda."
