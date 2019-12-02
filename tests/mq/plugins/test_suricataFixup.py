import json
import random
import string

from mozdef_util.utilities.toUTC import toUTC

from mq.plugins.suricataFixup import message


class TestSuricataFixup(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {
            'index': 'events'
        }

    # Should never match and be modified by the plugin
    def test_notsuri_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'key1': 'suricata'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_notsuri_log2(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'suricata': 'value1'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_suricata_nocustomendpoint_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alert'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def test_suricata_nocategory_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'customendpoint': '',
            'source': 'eve-log',
            'event_type': 'alert'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def test_suricata_wrongcategory_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'customendpoint': '',
            'category': 'alamakota',
            'source': 'eve-log',
            'event_type': 'alert'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_suricata_notype_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'category': 'suricata',
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        assert result['category'] == 'suricata'
        assert result['source'] == 'eve-log'
        assert result['event_type'] == 'unknown'
        assert result['type'] is 'nsm'

    def test_suricata_wrongtype_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alamakota'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        assert result['category'] == 'suricata'
        assert result['source'] == 'eve-log'
        assert result['event_type'] == 'alamakota'
        assert result['type'] is 'nsm'

    def test_suricata_nosource_log(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
        }
        MESSAGE = {
            'ts': 1505701210.163043
        }
        event['message'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result['category'] == 'suricata'
        assert result['source'] == 'unknown'

    def test_suricata_wrongsource_log(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'alamakota',
            'event_type': 'alert'
        }
        MESSAGE = {
            'ts': 1505701210.163043
        }
        event['message'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result['category'] == 'suricata'
        assert result['source'] == 'alamakota'

    def verify_metadata(self, metadata):
        assert metadata['index'] == 'events'

    def test_defaults(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alert'
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        print(result, len(result))
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['category'] == 'suricata'

    def test_nomatch_syslog(self):
        event = {
            "category": "syslog",
            "processid": "0",
            "receivedtimestamp": "2017-09-26T00:22:24.210945+00:00",
            "severity": "7",
            "utctimestamp": "2017-09-26T00:22:23+00:00",
            "timestamp": "2017-09-26T00:22:23+00:00",
            "hostname": "syslog1.private.scl3.mozilla.com",
            "mozdefhostname": "mozdef1.private.scl3.mozilla.com",
            "summary": "Connection from 10.22.74.208 port 9071 on 10.22.74.45 nsm suricata port 22\n",
            "eventsource": "systemslogs",
            "details": {
                "processid": "21233",
                "sourceipv4address": "10.22.74.208",
                "hostname": "hostname1.subdomain.domain.com",
                "program": "sshd",
                "sourceipaddress": "10.22.74.208"
            }
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result['category'] == 'syslog'
        assert result['eventsource'] == 'systemslogs'
        assert result == event

    def test_nomatch_auditd(self):
        event = {
            "category": "execve",
            "processid": "0",
            "receivedtimestamp": "2017-09-26T00:36:27.463745+00:00",
            "severity": "INFO",
            "utctimestamp": "2017-09-26T00:36:27+00:00",
            "tags": [
                "audisp-json",
                "2.1.1",
                "audit"
            ],
            "summary": "Execve: sh -c sudo suricata nsm /usr/lib64/nagios/plugins/custom/check_auditd.sh",
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
                "originaluser": "root",
                "ppid": "10552",
                "cwd": "/",
                "parentprocess": "nrpe",
                "euid": "398",
                "path": "/bin/sh",
                "rdev": "00:00",
                "dev": "08:03",
                "egid": "398",
                "command": "sh -c sudo /usr/lib64/nagios/plugins/custom/check_auditd.sh",
                "mode": "0100755",
                "user": "nagios"
            }
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result['category'] == 'execve'
        assert 'eventsource' not in result
        assert result == event

    def verify_defaults(self, result):
        assert result['category'] == 'suricata'
        assert result['eventsource'] == 'nsm'
        assert toUTC(result['receivedtimestamp']).isoformat() == result['receivedtimestamp']
        assert result['severity'] == 'INFO'
        assert 'event_type' in result
        assert 'source' in result
        assert toUTC(result['timestamp']).isoformat() == result['timestamp']
        assert toUTC(result['utctimestamp']).isoformat() == result['utctimestamp']

    def test_eve_log_alert_flow(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alert'
        }
        MESSAGE = {
            "timestamp":"2018-09-12T22:24:09.546736+0000",
            "flow_id":1484802709084080,
            "in_iface":"enp216s0f0",
            "event_type":"alert",
            "vlan":75,
            "src_ip":"10.48.240.19",
            "src_port":44741,
            "dest_ip":"10.48.75.120",
            "dest_port":53,
            "proto":"017",
            "alert":{
                "action":"allowed",
                "gid":1,
                "signature_id":2500003,
                "rev":1,
                "signature":"SURICATA DNS Query to a Suspicious *.ws Domain",
                "category":"",
                "severity":3
            },
            "app_proto":"dns",
            "flow":{
                "pkts_toserver":2,
                "pkts_toclient":0,
                "bytes_toserver":150,
                "bytes_toclient":0,
                "start":"2018-09-12T22:24:09.546736+0000"
            },
            "payload":"qFEBAAABAAAAAAAAA3d3dwhpbnNlY3VyZQJ3cwAAHAAB",
            "payload_printable":".Q...........www.insecure.ws.....",
            "stream":0,
            "packet":"AABeAAEKtAwl4EAQCABFAAA9M+5AAD4RuNYKMPATCjBLeK7FADUAKZFMqFEBAAABAAAAAAAAA3d3dwhpbnNlY3VyZQJ3cwAAHAAB",
            "packet_info":{
                "linktype":1
            }
        }
        event['message'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['flow']['start']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['flow']['start']).isoformat() == result['timestamp']
        assert result['details']['originipbytes'] == MESSAGE['flow']['bytes_toserver']
        assert result['details']['responseipbytes'] == MESSAGE['flow']['bytes_toclient']
        assert result['details']['orig_pkts'] == MESSAGE['flow']['pkts_toserver']
        assert result['details']['resp_pkts'] == MESSAGE['flow']['pkts_toclient']
        assert result['details']['service'] == MESSAGE['app_proto']
        assert 'pkts_toserver' not in result['details']['flow']
        assert 'pkts_toclient' not in result['details']['flow']
        assert 'bytes_toserver' not in result['details']['flow']
        assert 'bytes_toclient' not in result['details']['flow']
        assert 'app_proto' not in result['details']
        assert result['summary'] == '10.48.240.19:44741 -> 10.48.75.120:53'

    def test_eve_log_alert_http(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alert'
        }
        MESSAGE = {
            "timestamp":"2018-09-12T22:24:09.546736+0000",
            "flow_id":1484802709084080,
            "in_iface":"enp216s0f0",
            "event_type":"alert",
            "vlan":75,
            "src_ip":"10.48.240.19",
            "src_port":44741,
            "dest_ip":"10.48.74.17",
            "dest_port":3128,
            "proto":"017",
            "alert":{
                "action":"allowed",
                "gid":1,
                "signature_id":2024897,
                "rev":1,
                "signature":"ET USER_AGENTS Go HTTP Client User-Agent",
                "category":"",
                "severity":3
            },
            "app_proto":"http",
            "flow":{
                "pkts_toserver":555,
                "pkts_toclient":20,
                "bytes_toserver":350,
                "bytes_toclient":4444,
                "start":"2018-10-12T22:24:09.546736+0000"
            },
            "payload":"Q09OTkVDVCBzZWN1cml0eS10cmFja2VyLmRlYmlhbi5vcmc6NDQzIEhUVFAvMS4xDQpIb3N0OiBzZWN1cml0eS10cmFja2VyLmRlYmlhbi5vcmc6NDQzDQpVc2VyLUFnZW50OiBHby1odHRwLWNsaWVudC8xLjENCg0K",
            "payload_printable":"CONNECT security-tracker.debian.org:443 HTTP/1.1\r\nHost: security-tracker.debian.org:443\r\nUser-Agent: Go-http-client/1.1\r\n\r\n",
            "stream":0,
            "packet":"RQAAKAAAAABABgAACjBLMAowShHR6Aw4ClEmlrx/mcdQEgoAAAAAAA==",
            "packet_info":{
                "linktype":12
            },
            "http": {
                "hostname":"security-tracker.debian.org",
                "url":"security-tracker.debian.org:443",
                "http_user_agent":"Go-http-client/1.1",
                "http_method":"CONNECT",
                "protocol":"HTTP/1.1",
                "status":200,
                "length":0,
                "redirect":"afakedestination"
            },
        }
        event['message'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['flow']['start']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['flow']['start']).isoformat() == result['timestamp']
        assert result['details']['host'] == MESSAGE['http']['hostname']
        assert result['details']['method'] == MESSAGE['http']['http_method']
        assert result['details']['user_agent'] == MESSAGE['http']['http_user_agent']
        assert result['details']['status_code'] == MESSAGE['http']['status']
        assert result['details']['uri'] == MESSAGE['http']['url']
        assert result['details']['redirect_dst'] == MESSAGE['http']['redirect']
        assert result['details']['request_body_len'] == MESSAGE['http']['length']

    def test_eve_log_alert_truncate(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alert'
        }
        MESSAGE = {
            "timestamp":"2018-09-12T22:24:09.546736+0000",
            "flow_id":1484802709084080,
            "in_iface":"enp216s0f0",
            "event_type":"alert",
            "vlan":75,
            "src_ip":"10.48.240.19",
            "src_port":44741,
            "dest_ip":"10.48.74.17",
            "dest_port":3128,
            "proto":"017",
            "alert":{
                "action":"allowed",
                "gid":1,
                "signature_id":2024897,
                "rev":1,
                "signature":"ET USER_AGENTS Go HTTP Client User-Agent",
                "category":"",
                "severity":3
            },
            "app_proto":"http",
            "flow":{
                "pkts_toserver":555,
                "pkts_toclient":20,
                "bytes_toserver":350,
                "bytes_toclient":4444,
                "start":"2018-10-12T22:24:09.546736+0000"
            },
            "stream":0,
            "packet_info":{
                "linktype":12
            },
            "http": {
                "hostname":"such.a.host.com",
                "url":"/allyourfiles",
                "http_user_agent":"FirefoxRulez",
                "http_method":"GET",
                "protocol":"HTTP/1.2",
                "status":200,
                "length":5000,
                "redirect":"afakedestination"
            },
        }
        # Note - do not copy to other apps. This is INSECURE.
        large_pseudorandom_string = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5000))
        MESSAGE['packet'] = large_pseudorandom_string
        MESSAGE['payload'] = large_pseudorandom_string
        MESSAGE['payload_printable'] = large_pseudorandom_string
        MESSAGE['http']['http_response_body'] = large_pseudorandom_string
        MESSAGE['http']['http_response_body_printable'] = large_pseudorandom_string
        event['message'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['host'] == MESSAGE['http']['hostname']
        assert result['details']['method'] == MESSAGE['http']['http_method']
        assert result['details']['user_agent'] == MESSAGE['http']['http_user_agent']
        assert result['details']['status_code'] == MESSAGE['http']['status']
        assert result['details']['uri'] == MESSAGE['http']['url']
        assert result['details']['redirect_dst'] == MESSAGE['http']['redirect']
        assert result['details']['request_body_len'] == MESSAGE['http']['length']
        assert len(result['details']['packet']) == 4095
        assert len(result['details']['payload']) == 4095
        assert len(result['details']['payload_printable']) == 4095
        assert len(result['details']['http_response_body']) == 4095
        assert len(result['details']['http_response_body_printable']) == 4095

    def test_eve_log_alert_flowbits(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alert'
        }
        MESSAGE = {
            "timestamp":"2018-09-12T22:24:09.546736+0000",
            "flow_id":1484802709084080,
            "in_iface":"enp216s0f0",
            "event_type":"alert",
            "vlan":75,
            "src_ip":"10.48.240.19",
            "src_port":44741,
            "dest_ip":"10.48.75.120",
            "dest_port":53,
            "proto":"017",
            "alert":{
                "action":"allowed",
                "gid":1,
                "signature_id":2500003,
                "rev":1,
                "signature":"SURICATA DNS Query to a Suspicious *.ws Domain",
                "category":"",
                "severity":3
            },
            "app_proto":"dns",
            "flow":{
                "pkts_toserver":2,
                "pkts_toclient":0,
                "bytes_toserver":150,
                "bytes_toclient":0,
                "start":"2018-09-12T22:24:09.546736+0000"
            },
            "payload":"qFEBAAABAAAAAAAAA3d3dwhpbnNlY3VyZQJ3cwAAHAAB",
            "payload_printable":".Q...........www.insecure.ws.....",
            "stream":0,
            "packet":"AABeAAEKtAwl4EAQCABFAAA9M+5AAD4RuNYKMPATCjBLeK7FADUAKZFMqFEBAAABAAAAAAAAA3d3dwhpbnNlY3VyZQJ3cwAAHAAB",
            "packet_info":{
                "linktype":1
            },
            "vars":{
                "flowbits":{
                    "et.http.javaclient.vulnerable":"true",
                    "et.javanotjar":"true",
                    "et.http.javaclient":"true"
                }
            }
        }
        event['message'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert 'vars' in result['details']
        assert 'flowbits' in result['details']['vars']
        assert result['details']['vars']['flowbits']['et.http.javaclient.vulnerable'] == "true"
        assert result['details']['vars']['flowbits']['et.javanotjar'] == "true"

    def test_eve_log_alert_rename(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alert'
        }
        MESSAGE = {
            "timestamp":"2018-09-12T22:24:09.546736+0000",
            "flow_id":1484802709084080,
            "in_iface":"enp216s0f0",
            "event_type":"alert",
            "vlan":75,
            "src_ip":"10.48.240.19",
            "src_port":44741,
            "dest_ip":"10.48.75.120",
            "dest_port":53,
            "proto":"017",
            "alert":{
                "action":"allowed",
                "gid":1,
                "signature_id":2500003,
                "rev":1,
                "signature":"SURICATA DNS Query to a Suspicious *.ws Domain",
                "category":"",
                "severity":3
            },
            "app_proto":"dns",
            "flow":{
                "pkts_toserver":2,
                "pkts_toclient":0,
                "bytes_toserver":150,
                "bytes_toclient":0,
                "start":"2018-09-12T22:24:09.546736+0000"
            },
            "payload":"qFEBAAABAAAAAAAAA3d3dwhpbnNlY3VyZQJ3cwAAHAAB",
            "payload_printable":".Q...........www.insecure.ws.....",
            "stream":0,
            "packet":"AABeAAEKtAwl4EAQCABFAAA9M+5AAD4RuNYKMPATCjBLeK7FADUAKZFMqFEBAAABAAAAAAAAA3d3dwhpbnNlY3VyZQJ3cwAAHAAB",
            "packet_info":{
                "linktype":1
            }
        }
        event['message'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert 'suricata_alert' in result['details']
        assert 'alert' not in result['details']
        assert result['details']['suricata_alert']['action'] == MESSAGE['alert']['action']
        assert result['details']['suricata_alert']['gid'] == MESSAGE['alert']['gid']
        assert result['details']['suricata_alert']['rev'] == MESSAGE['alert']['rev']
        assert result['details']['suricata_alert']['signature_id'] == MESSAGE['alert']['signature_id']
        assert result['details']['suricata_alert']['signature'] == MESSAGE['alert']['signature']
        assert result['details']['suricata_alert']['category'] == MESSAGE['alert']['category']
        assert result['details']['suricata_alert']['severity'] == MESSAGE['alert']['severity']

    def test_smtp_alert(self):
        event = {
            'customendpoint': '',
            'category': 'suricata',
            'source': 'eve-log',
            'event_type': 'alert'
        }
        MESSAGE = {
            "event_type": "alert",
            'smtp': {
                'helo': 'example.com',
                'mail_from': '<ttesterson@example.com',
                'rcpt_to': ['<abc.example.com>']
            },
            'email': {
                'status': 'BODY_STARTED',
                'from': '"Test Email List"<ttesterson@example.com>'
            }
        }
        event['message'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['smtp'] == MESSAGE['smtp']
        assert 'email' not in result['details']
