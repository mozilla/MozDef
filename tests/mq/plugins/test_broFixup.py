from mozdef_util.utilities.toUTC import toUTC

import mock
import json

from mq.plugins.broFixup import message


class TestBroFixup(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {
            'index': 'events'
        }

    # Should never match and be modified by the plugin
    def test_notbro_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'key1': 'bro'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_notbro_log2(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'bro': 'value1'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_bro_notype_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'category': 'bro'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def test_bro_wrongtype_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'nosuchtype',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            'ts': 1505701210.163043
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(MESSAGE.keys())

    @mock.patch('mq.plugins.broFixup.node')
    def test_mozdefhostname_mock_string(self, mock_path):
        mock_path.return_value = 'samplehostname'
        event = {
            'category': 'bro',
            'SOURCE': 'something',
            'customendpoint': 'bro'
        }
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result['mozdefhostname'] == 'samplehostname'

    @mock.patch('mq.plugins.broFixup.node')
    def test_mozdefhostname_mock_exception(self, mock_path):
        mock_path.side_effect = ValueError
        event = {
            'category': 'bro',
            'SOURCE': 'something',
            'customendpoint': 'bro'
        }
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result['mozdefhostname'] == 'failed to fetch mozdefhostname'

    def verify_metadata(self, metadata):
        assert metadata['index'] == 'events'

    def test_defaults(self):
        event = {
            'category': 'bro',
            'SOURCE': 'something',
            'customendpoint': 'bro'
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['category'] == 'bro'
        assert result['source'] == 'thing'

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
            "summary": "Connection from 10.22.74.208 port 9071 on 10.22.74.45 nsm bro port 22\n",
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
            "summary": "Execve: sh -c sudo bro nsm /usr/lib64/nagios/plugins/custom/check_auditd.sh",
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
        assert result['category'] == 'bro'
        assert result['customendpoint'] == 'bro'
        assert result['eventsource'] == 'nsm'
        assert toUTC(result['receivedtimestamp']).isoformat() == result['receivedtimestamp']
        assert result['severity'] == 'INFO'
        assert toUTC(result['timestamp']).isoformat() == result['timestamp']
        assert toUTC(result['utctimestamp']).isoformat() == result['utctimestamp']

    def test_conn_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_conn',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            'conn_state': 'SF',
            'duration': 0.047874,
            'history': 'ShADadfF',
            'id.orig_h': '1.2.3.4',
            'id.orig_p': 39246,
            'id.resp_h': '5.6.7.8',
            'id.resp_p': 80,
            'local_orig': True,
            'local_resp': True,
            'missed_bytes': 0,
            'orig_bytes': 2080,
            'orig_ip_bytes': 2452,
            'orig_pkts': 7,
            'peer': 'nsm-stage1-eth1-2',
            'proto': 'tcp',
            'resp_bytes': 1812,
            'resp_ip_bytes': 2132,
            'resp_pkts': 6,
            'service': 'http',
            'ts': 1505701210.163043,
            'tunnel_parents': [],
            'uid': 'CYxwva4RBFtKpxWLba'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert result['details']['originipbytes'] == 2452
        assert result['details']['responseipbytes'] == 2132
        assert 'orig_ip_bytes' not in result['details']
        assert 'resp_ip_bytes' not in result['details']
        assert 'history' in result['details']
        assert result['summary'] == '1.2.3.4:39246 -> 5.6.7.8:80 ShADadfF 2452 bytes / 2132 bytes'

    def test_files_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_files',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701210.155542,
            "fuid":"FxAKGz3eoA79wYCAwc",
            "tx_hosts":["23.61.194.147"],
            "rx_hosts":["63.245.214.159"],
            "conn_uids":["CucQNa2qHds42xa5na"],
            "filesource":"HTTP",
            "depth":0,
            "analyzers":["MD5","SHA1"],
            "mime_type":"application/ocsp-response",
            "duration":0.0,
            "local_orig":'false',
            "is_orig":'false',
            "seen_bytes":527,
            "total_bytes":527,
            "missing_bytes":0,
            "overflow_bytes":0,
            "timedout":'false',
            "md5":"f30cb6b67044c9871b51dc0263717c92",
            "sha1":"a0a1def8b8f264f6431b973007fca15b90a39aa9",
            "filename":"arandomfile",
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert result['details']['sourceipaddress'] == '63.245.214.159'
        assert result['details']['destinationipaddress'] == '23.61.194.147'
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == '63.245.214.159 downloaded (MD5) f30cb6b67044c9871b51dc0263717c92 MIME application/ocsp-response (527 bytes) from 23.61.194.147 via HTTP'

    def test_files_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_files',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701210.155542,
            "fuid":"FxAKGz3eoA79wYCAwc",
            "tx_hosts":["23.61.194.147"],
            "rx_hosts":["63.245.214.159"],
            "conn_uids":["CucQNa2qHds42xa5na"],
            "depth":0,
            "analyzers":["MD5","SHA1"],
            "duration":0.0,
            "local_orig":'false',
            "is_orig":'false',
            "seen_bytes":527,
            "total_bytes":527,
            "missing_bytes":0,
            "overflow_bytes":0,
            "timedout":'false'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert result['details']['sourceipaddress'] == '63.245.214.159'
        assert result['details']['destinationipaddress'] == '23.61.194.147'
        assert 'md5' in result['details']
        assert 'filename' in result['details']
        assert 'mime_type' in result['details']
        assert 'filesource' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == '63.245.214.159 downloaded (MD5) None MIME unknown (527 bytes) from 23.61.194.147 via None'

    def test_dns_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_dns',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701210.060553,
            "uid":"C6gQDU2AZJBxU1n3qd",
            "id.orig_h":"10.22.81.65",
            "id.orig_p":14092,
            "id.resp_h":"10.22.75.41",
            "id.resp_p":53,
            "proto":"udp",
            "trans_id":37909,
            "rtt":0.001138,
            "query":"50.75.8.10.in-addr.arpa",
            "qclass":1,
            "qclass_name":"C_INTERNET",
            "qtype":12,
            "qtype_name":"PTR",
            "rcode":0,
            "rcode_name":"NOERROR",
            "AA":'true',
            "TC":'false',
            "RD":'true',
            "RA":'true',
            "Z":0,
            "answers":["bedrockadm.private.phx1.mozilla.com"],
            "TTLs":'[3600.0]',
            "rejected":'false'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'DNS PTR type query 10.22.81.65 -> 10.22.75.41:53'

    def test_dns_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_dns',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701210.060553,
            "uid":"C6gQDU2AZJBxU1n3qd",
            "id.orig_h":"10.22.81.65",
            "id.orig_p":14092,
            "id.resp_h":"10.22.75.41",
            "id.resp_p":53,
            "proto":"udp",
            "trans_id":37909,
            "rtt":0.001138,
            "qclass":1,
            "qclass_name":"C_INTERNET",
            "rcode":0,
            "AA":'true',
            "TC":'false',
            "RD":'true',
            "RA":'true',
            "Z":0,
            "answers":["bedrockadm.private.phx1.mozilla.com"],
            "TTLs":'[3600.0]',
            "rejected":'false'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'rcode_name' in result['details']
        assert 'query' in result['details']
        assert 'qtype_name' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'DNS unknown type query 10.22.81.65 -> 10.22.75.41:53'

    def test_http_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_http',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701210.163246,
            "uid":"CMxwva4RHFtKpxWLba",
            "id.orig_h":"10.22.74.212",
            "id.orig_p":39246,
            "id.resp_h":"10.22.74.175",
            "id.resp_p":80,
            "trans_depth":1,
            "method":"GET",
            "host":"hg.mozilla.org",
            "uri":"/projects/build-system?cmd=batch",
            "version":"1.1",
            "user_agent":"mercurial/proto-1.0",
            "request_body_len":0,
            "response_body_len":1639,
            "status_code":200,
            "status_msg":"Script output follows",
            "tags":[],
            "proxied":["X-FORWARDED-FOR -> 34.212.32.13"],
            "resp_fuids":["FFy3254KdpcjRJbjY4"],
            "resp_mime_types":["text/plain"],
            "cluster_client_ip":"34.212.32.13",
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'status_code' in result['details']
        assert 'uri' in result['details']
        assert 'host' in result['details']
        assert 'method' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'HTTP GET 10.22.74.212 -> 10.22.74.175:80'

    def test_ssl_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ssl',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1502751597.597052,
            "uid":"CWmwax23B9dBtn3s16",
            "id.orig_h":"36.70.241.31",
            "id.orig_p":49322,
            "id.resp_h":"63.245.215.82",
            "id.resp_p":443,
            "version":"TLSv12",
            "cipher":"TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256",
            "curve":"secp256r1",
            "server_name":"geo.mozilla.org",
            "resumed":'false',
            "established":'true',
            "cert_chain_fuids":["Fo4Xkx1WrJPQJVG6Zk","FZcDnY15qCFTlPt0E7"],
            "client_cert_chain_fuids":[],
            "subject":"CN=geo.mozilla.org,OU=WebOps,O=Mozilla Foundation,L=Mountain View,ST=California,C=US",
            "issuer":"CN=DigiCert SHA2 Secure Server CA,O=DigiCert Inc,C=US",
            "validation_status":"ok",
            "pfs":'true'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SSL: 36.70.241.31 -> 63.245.215.82:443'

    def test_ssl_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ssl',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1502751597.597052,
            "uid":"CWmwax23B9dBtn3s16",
            "id.orig_h":"36.70.241.31",
            "id.orig_p":49322,
            "id.resp_h":"63.245.215.82",
            "id.resp_p":443,
            "version":"TLSv12",
            "cipher":"TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256",
            "curve":"secp256r1",
            "resumed":'false',
            "established":'true',
            "cert_chain_fuids":["Fo4Xkx1WrJPQJVG6Zk","FZcDnY15qCFTlPt0E7"],
            "client_cert_chain_fuids":[],
            "subject":"CN=geo.mozilla.org,OU=WebOps,O=Mozilla Foundation,L=Mountain View,ST=California,C=US",
            "issuer":"CN=DigiCert SHA2 Secure Server CA,O=DigiCert Inc,C=US",
            "validation_status":"ok",
            "pfs":'true'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'server_name' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SSL: 36.70.241.31 -> 63.245.215.82:443'

    def test_dhcp_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_dhcp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts": 1561756317.104897,
            "uids": ["C6uJBE1z3CKfrA9FE4", "CdCBtl1fKEIMNvebrb", "CNJJ9g1HgefKR09ied", "CuXKNM1R5MEJ9GsMIi", "CMIYsm2weaHvzBRJIi", "C0vslbmXr3Psyy5Ff", "Ct0BRQ2Y84MWhag1Ik", "C5BNK71HlfhlXf8Pq", "C5ZrPG3DfQNzsiUMi2", "CMJHze3BH9o7yg9yM6", "CMSyg03ZZcdic8pTMc"],
            "client_addr": "10.251.255.10",
            "server_addr": "10.251.24.1",
            "mac": "f01898550e0e",
            "host_name": "aliczekkroliczek",
            "domain": "ala.ma.kota",
            "assigned_addr": "10.251.30.202",
            "lease_time": 43200.0,
            "msg_types": ["DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER", "DISCOVER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "DISCOVER", "OFFER", "OFFER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER", "DISCOVER", "DISCOVER", "OFFER", "OFFER", "OFFER"],
            "duration": 34.037004
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == '10.251.30.202 assigned to f01898550e0e'

    def test_dhcp_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_dhcp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts": 1561607456.803827,
            "uids": ["CsXuIb2HTmDaPrPvT7"],
            "host_name": "nsm2",
            "msg_types": ["DISCOVER", "DISCOVER"],
            "duration": 17.778322
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == '0.0.0.0 assigned to 000000000000'

    def test_ftp_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ftp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1363628702.035108,
            "uid":"CdS183kIs8TBugKDf",
            "id.orig_h":"141.142.228.5",
            "id.orig_p":50736,
            "id.resp_h":"141.142.192.162",
            "id.resp_p":21,
            "user":"anonymous",
            "password":"chrome@example.com",
            "command":"EPSV",
            "reply_code":229,
            "reply_msg":"Entering Extended Passive Mode (|||38141|)",
            "data_channel.passive":'true',
            "data_channel.orig_h":"141.142.228.5",
            "data_channel.resp_h":"141.142.192.162",
            "data_channel.resp_p":38141
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'FTP: 141.142.228.5 -> 141.142.192.162:21'

    def test_ftp_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ftp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1363628702.035108,
            "uid":"CdS183kIs8TBugKDf",
            "id.orig_h":"141.142.228.5",
            "id.orig_p":50736,
            "id.resp_h":"141.142.192.162",
            "id.resp_p":21,
            "password":"chrome@example.com",
            "reply_code":229,
            "reply_msg":"Entering Extended Passive Mode (|||38141|)",
            "data_channel.passive":'true',
            "data_channel.orig_h":"141.142.228.5",
            "data_channel.resp_h":"141.142.192.162",
            "data_channel.resp_p":38141
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'command' in result['details']
        assert 'user' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'FTP: 141.142.228.5 -> 141.142.192.162:21'

    def test_pe_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_pe',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701209.93718,
            "id":"FlFe5r3GnwleZBqEVd",
            "machine":"I386",
            "compile_ts":1306768249.0,
            "os":"Windows 95 or NT 4.0",
            "subsystem":"WINDOWS_GUI",
            "is_exe":'true',
            "is_64bit":'false',
            "uses_aslr":'false',
            "uses_dep":'false',
            "uses_code_integrity":'false',
            "uses_seh":'true',
            "has_import_table":'true',
            "has_export_table":'true',
            "has_cert_table":'false',
            "has_debug_data":'true',
            "section_names":[".text",".rdata",".data",".rsrc",".reloc"]
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'PE file: Windows 95 or NT 4.0 WINDOWS_GUI'

    def test_pe_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_pe',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701209.93718,
            "id":"FlFe5r3GnwleZBqEVd",
            "machine":"I386",
            "compile_ts":1306768249.0,
            "is_exe":'true',
            "is_64bit":'false',
            "uses_aslr":'false',
            "uses_dep":'false',
            "uses_code_integrity":'false',
            "uses_seh":'true',
            "has_import_table":'true',
            "has_export_table":'true',
            "has_cert_table":'false',
            "has_debug_data":'true',
            "section_names":[".text",".rdata",".data",".rsrc",".reloc"]
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'subsystem' in result['details']
        assert 'os' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'PE file:  '

    def test_smtp_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_smtp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703597.295432,
            "uid":"Ct7e4waRBwsLoRvfg",
            "id.orig_h":"63.245.214.155",
            "id.orig_p":4523,
            "id.resp_h":"128.199.139.6",
            "id.resp_p":25,
            "trans_depth":1,
            "helo":"smtp.mozilla.org",
            "mailfrom":"bugzilla-daemon@mozilla.org",
            "rcptto":["bugmail@firebot.glob.uno"],
            "date":"Mon, 18 Sep 2017 02:59:56 +0000",
            "from":"\u0022Bugzilla@Mozilla\u0022 <bugzilla-daemon@mozilla.org>",
            "to":["bugmail@firebot.glob.uno"],
            "msg_id":"<bug-1400759-507647@https.bugzilla.mozilla.org/>",
            "subject":"[Bug 1400759] New: Debugger script search not working when content type = \u0027image/svg+xml\u0027",
            "first_received":"by jobqueue2.bugs.scl3.mozilla.com (Postfix, from userid 0)\u0009id 87345380596; Mon, 18 Sep 2017 02:59:56 +0000 (UTC)",
            "second_received":"from jobqueue2.bugs.scl3.mozilla.com (jobqueue2.bugs.scl3.mozilla.com [10.22.82.42])\u0009by mx1.mail.scl3.mozilla.com (Postfix) with ESMTPS id 9EBCBC0A97\u0009for <bugmail@firebot.glob.uno>; Mon, 18 Sep 2017 02:59:56 +0000 (UTC)",
            "last_reply":"250 2.0.0 Ok: queued as 3E1EC13F655",
            "path":["128.199.139.6","63.245.214.155","127.0.0.1","10.22.82.42"],
            "tls":'false',
            "fuids":["FnR86s3vp0xKw286Ei","FiYNQo4ygv3xPAeocd"],
            "is_webmail":'false'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'tls' not in result['details']
        assert result['details']['tls_encrypted'] == 'false'
        assert result['summary'] == 'SMTP: 63.245.214.155 -> 128.199.139.6:25'

    def test_smtp_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_smtp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703597.295432,
            "uid":"Ct7e4waRBwsLoRvfg",
            "id.orig_h":"63.245.214.155",
            "id.orig_p":4523,
            "id.resp_h":"128.199.139.6",
            "id.resp_p":25,
            "trans_depth":1,
            "helo":"smtp.mozilla.org",
            "mailfrom":"bugzilla-daemon@mozilla.org",
            "rcptto":["bugmail@firebot.glob.uno"],
            "date":"Mon, 18 Sep 2017 02:59:56 +0000",
            "subject":"[Bug 1400759] New: Debugger script search not working when content type = \u0027image/svg+xml\u0027",
            "first_received":"by jobqueue2.bugs.scl3.mozilla.com (Postfix, from userid 0)\u0009id 87345380596; Mon, 18 Sep 2017 02:59:56 +0000 (UTC)",
            "second_received":"from jobqueue2.bugs.scl3.mozilla.com (jobqueue2.bugs.scl3.mozilla.com [10.22.82.42])\u0009by mx1.mail.scl3.mozilla.com (Postfix) with ESMTPS id 9EBCBC0A97\u0009for <bugmail@firebot.glob.uno>; Mon, 18 Sep 2017 02:59:56 +0000 (UTC)",
            "last_reply":"250 2.0.0 Ok: queued as 3E1EC13F655",
            "path":["128.199.139.6","63.245.214.155","127.0.0.1","10.22.82.42"],
            "tls":'false',
            "fuids":["FnR86s3vp0xKw286Ei","FiYNQo4ygv3xPAeocd"],
            "is_webmail":'false'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'from' not in result['details']
        assert 'to' not in result['details']
        assert 'msg_id' not in result['details']
        assert 'tls' not in result['details']
        assert result['details']['tls_encrypted'] == 'false'
        assert result['summary'] == 'SMTP: 63.245.214.155 -> 128.199.139.6:25'

    def test_smtp_unicode(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_smtp',
            'customendpoint': 'bro'
        }

        message = {
            'from': '"Test from field\xe2\x80\x99s here" <Contact@1234.com>',
            'id.orig_h': '1.2.3.4',
            'id.orig_p': 47311,
            'id.resp_h': '5.6.7.8',
            'id.resp_p': 25,
            'subject': 'Example subject of email\xe2\x80\x99s',
            'ts': 1531818582.216429,
        }

        event['MESSAGE'] = json.dumps(message)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(message['ts']).isoformat() == result['utctimestamp']
        assert toUTC(message['ts']).isoformat() == result['timestamp']
        assert result['details']['from'] == '"Test from field\xe2\x80\x99s here" <Contact@1234.com>'
        assert result['details']['subject'] == 'Example subject of email\xe2\x80\x99s'

    def test_ssh_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ssh',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703601.393284,
            "uid":"CBiwrdGg2CGf0Y6U9",
            "id.orig_h":"63.245.214.162",
            "id.orig_p":22418,
            "id.resp_h":"192.30.255.112",
            "id.resp_p":22,
            "version":2,
            "auth_success":'true',
            "auth_attempts":1,
            "direction":"OUTBOUND",
            "client":"SSH-2.0-OpenSSH_6.6.1p1 Ubuntu-2ubuntu2.8",
            "server":"SSH-2.0-libssh_0.7.0",
            "cipher_alg":"chacha20-poly1305@openssh.com",
            "mac_alg":"hmac-sha2-256",
            "compression_alg":"none",
            "kex_alg":"ecdh-sha2-nistp256",
            "host_key_alg":"ssh-dss",
            "host_key":"16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SSH: 63.245.214.162 -> 192.30.255.112:22 success true'

    def test_ssh_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ssh',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703601.393284,
            "uid":"CBiwrdGg2CGf0Y6U9",
            "id.orig_h":"63.245.214.162",
            "id.orig_p":22418,
            "id.resp_h":"192.30.255.112",
            "id.resp_p":22,
            "version":2,
            "auth_attempts":1,
            "direction":"OUTBOUND",
            "client":"SSH-2.0-OpenSSH_6.6.1p1 Ubuntu-2ubuntu2.8",
            "server":"SSH-2.0-libssh_0.7.0",
            "cipher_alg":"chacha20-poly1305@openssh.com",
            "mac_alg":"hmac-sha2-256",
            "compression_alg":"none",
            "kex_alg":"ecdh-sha2-nistp256",
            "host_key_alg":"ssh-dss",
            "host_key":"16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'auth_success' not in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SSH: 63.245.214.162 -> 192.30.255.112:22'

    def test_ssh_log_auth_true(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ssh',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703601.393284,
            "id.orig_h":"63.245.214.162",
            "id.orig_p":22418,
            "id.resp_h":"192.30.255.112",
            "id.resp_p":22,
            "auth_success": True
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'auth_success' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SSH: 63.245.214.162 -> 192.30.255.112:22 success True'

    def test_ssh_log_auth_false(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ssh',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703601.393284,
            "id.orig_h":"63.245.214.162",
            "id.orig_p":22418,
            "id.resp_h":"192.30.255.112",
            "id.resp_p":22,
            "auth_success": False
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'auth_success' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SSH: 63.245.214.162 -> 192.30.255.112:22 success False'

    def test_tunnel_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_tunnel',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703604.92601,
            "id.orig_h":"10.22.24.167",
            "id.orig_p":0,
            "id.resp_h":"10.22.74.74",
            "id.resp_p":3128,
            "tunnel_type":"Tunnel::HTTP",
            "action":"Tunnel::DISCOVER"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == '10.22.24.167 -> 10.22.74.74:3128 Tunnel::HTTP Tunnel::DISCOVER'

    def test_tunnel_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_tunnel',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703604.92601,
            "id.orig_h":"10.22.24.167",
            "id.orig_p":0,
            "id.resp_h":"10.22.74.74",
            "id.resp_p":3128
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'tunnel_type' in result['details']
        assert 'action' in result['details']
        assert result['summary'] == '10.22.24.167 -> 10.22.74.74:3128  '

    def test_intel_log(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_intel',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701213.244219,
            "uid":"CwO41Y3TzqvScTyRk",
            "id.orig_h":"10.8.81.221",
            "id.orig_p":46606,
            "id.resp_h":"10.8.81.42",
            "id.resp_p":81,
            "seenindicator":"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)",
            "seen.indicator_type":"Intel::SOFTWARE",
            "seenwhere":"HTTP::IN_USER_AGENT_HEADER",
            "seennode":"nsm-stage1-eth4-4",
            "matched":["Intel::SOFTWARE"],
            "sources":["test"]
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert result['summary'] == 'Bro intel match of Intel::SOFTWARE in HTTP::IN_USER_AGENT_HEADER'

    def test_intel_log2(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_intel',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701213.244219,
            "uid":"CwO41Y3TzqvScTyRk",
            "id.orig_h":"10.8.81.221",
            "id.orig_p":46606,
            "id.resp_h":"10.8.81.42",
            "id.resp_p":81,
            "seen.indicator_type":"Intel::SOFTWARE",
            "seen.where":"HTTP::IN_USER_AGENT_HEADER",
            "seen.node":"nsm-stage1-eth4-4",
            "matched":["Intel::SOFTWARE"],
            "sources":["test"]
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'seenindicator' in result['details']
        assert result['summary'] == 'Bro intel match of Intel::SOFTWARE in HTTP::IN_USER_AGENT_HEADER'

    def test_knowncerts_log(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_known_certs',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701209.939031,
            "host":"10.22.75.54",
            "port_num":8443,
            "subject":"CN=syslog1.private.scl3.mozilla.com,OU=WebOps,O=Mozilla Corporation,L=Mountain View,ST=California,C=US",
            "issuer_subject":"CN=DigiCert SHA2 Secure Server CA,O=DigiCert Inc,C=US",
            "serial":"0B2BF706734AA1CCC969F7990FD20424"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            assert key in result['details']
            assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'Certificate X509 seen from: 10.22.75.54:8443'

    def test_knowncerts_log2(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_known_certs',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701209.939031,
            "host":"10.22.75.54",
            "port_num":8443,
            "subject":"CN=syslog1.private.scl3.mozilla.com,OU=WebOps,O=Mozilla Corporation,L=Mountain View,ST=California,C=US",
            "issuer_subject":"CN=DigiCert SHA2 Secure Server CA,O=DigiCert Inc,C=US"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            assert key in result['details']
            assert MESSAGE[key] == result['details'][key]
        assert 'serial' in result['details']
        assert result['summary'] == 'Certificate X509 seen from: 10.22.75.54:8443'

    def test_knowndevices_log(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_known_devices',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1258531221.486539,
            "mac":"00:0b:db:63:58:a6",
            "dhcp_host_name":"m57-jo"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            assert key in result['details']
            assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'New host: 00:0b:db:63:58:a6'

    def test_knowndevices_log2(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_known_devices',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1258531221.486539
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'mac' in result['details']
        assert 'dhcp_host_name' in result['details']
        assert result['summary'] == 'New host: '

    def test_knownhosts_log(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_known_hosts',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1258535653.085939,
            "host":"65.54.95.64"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            assert key in result['details']
            assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'New host: 65.54.95.64'

    def test_knownhosts_log2(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_known_hosts',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1258535653.085939,
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'host' in result['details']
        assert result['summary'] == 'New host: '

    def test_knownservices_log(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_known_services',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701209.937973,
            "host":"10.22.70.91",
            "port_num":3306,
            "port_proto":"tcp",
            "service":["MYSQL"],
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            assert key in result['details']
            assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'New service: MYSQL on host 10.22.70.91:3306 / tcp'

    def test_knownservices_log2(self):
        event = {
            'category':'bro',
            'SOURCE':'bro_known_services',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701209.937973,
            'service':[]
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'host' in result['details']
        assert 'port_num' in result['details']
        assert 'port_proto' in result['details']
        assert 'service' in result['details']
        assert result['summary'] == 'New service: Unknown on host unknown:0 / '

    def test_notice_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_notice',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701210.803008,
            "uid":"ClM3Um3n5pZjcZZ843",
            "id.orig_h":"73.72.209.187",
            "id.orig_p":61558,
            "id.resp_h":"63.245.213.32",
            "id.resp_p":443,
            "fuid":"F75Pce2pj1HH653VA7",
            "proto":"tcp",
            "note":"SSL::Certificate_Expires_Soon",
            "msg":"Certificate CN=support.mozilla.org,O=Mozilla Foundation,L=Mountain View,ST=California,C=US,postalCode=94041,street=650 Castro St Ste 300,serialNumber=C2543436,1.3.6.1.4.1.311.60.2.1.2=#130A43616C69666F726E6961,1.3.6.1.4.1.311.60.2.1.3=#13025553,businessCategory=Private Organization is going to expire at 2017-10-06-12:00:00.000000000",
            "src":"73.72.209.187",
            "dst":"63.245.213.32",
            "p":443,
            "peer_descr":"nsm-stage1-eth4-2",
            "actions":["Notice::ACTION_LOG"],
            "suppress_for":86400.0,
            "dropped":'false'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'uid' in result['details']
        assert MESSAGE['uid'] == result['details']['uid']
        assert 'note' in result['details']
        assert MESSAGE['note'] == result['details']['note']
        assert 'msg' in result['details']
        assert MESSAGE['msg'] == result['details']['msg']
        assert 'src' not in result['details']
        assert 'dst' not in result['details']
        assert 'sourceipv4address' in result['details']
        assert MESSAGE['src'] == result['details']['sourceipv4address']
        assert 'sourceipaddress' in result['details']
        assert MESSAGE['src'] == result['details']['sourceipaddress']
        assert 'destinationipv4address' in result['details']
        assert MESSAGE['dst'] == result['details']['destinationipv4address']
        assert 'destinationipaddress' in result['details']
        assert MESSAGE['dst'] == result['details']['destinationipaddress']
        assert 'p' in result['details']
        assert MESSAGE['p'] == result['details']['p']
        assert result['details']['indicators']
        assert MESSAGE['src'] in result['details']['indicators']
        assert result['summary'] == "SSL::Certificate_Expires_Soon source 73.72.209.187 destination 63.245.213.32 port 443"

    def test_notice_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_notice',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701210.803008,
            "uid":"ClM3Um3n5pZjcZZ843",
            "note":"Scan::Address_Scan",
            "msg": "10.252.55.230 scanned at least 5 unique hosts on port 3283/tcp in 0m11s",
            "src":"10.252.55.230",
            "p":3283,
            "peer_descr":"nsm-stage1-eth4-2",
            "actions":["Notice::ACTION_LOG"],
            "suppress_for":86400.0,
            "dropped":'false',
            'category': 'bro',
            'source': 'notice',
            'customendpoint': 'bro'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'uid' in result['details']
        assert MESSAGE['uid'] == result['details']['uid']
        assert 'note' in result['details']
        assert MESSAGE['note'] == result['details']['note']
        assert 'msg' in result['details']
        assert MESSAGE['msg'] == result['details']['msg']
        assert 'src' not in result['details']
        assert 'sourceipv4address' in result['details']
        assert MESSAGE['src'] == result['details']['sourceipv4address']
        assert 'sourceipaddress' in result['details']
        assert MESSAGE['src'] == result['details']['sourceipaddress']
        assert 'p' in result['details']
        assert MESSAGE['p'] == result['details']['p']
        assert result['details']['indicators']
        assert MESSAGE['src'] in result['details']['indicators']
        assert result['summary'] == "Scan::Address_Scan source 10.252.55.230 destination unknown port 3283"

    def test_notice_log3(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_notice',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701210.803008,
            "uid":"ClM3Um3n5pZjcZZ843",
            "note":"Scan::Address_Scan",
            "msg": "2620:101:80fc:232:b5a9:5071:1dc1:1499 scanned at least 5 unique hosts on port 445/tcp in 0m13s",
            "src":"2620:101:80fc:232:b5a9:5071:1dc1:1499",
            "p":445,
            "peer_descr":"nsm-stage1-eth4-2",
            "actions":["Notice::ACTION_LOG"],
            "suppress_for":86400.0,
            "dropped":'false',
            'category': 'bro',
            'source': 'notice',
            'customendpoint': 'bro'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'uid' in result['details']
        assert MESSAGE['uid'] == result['details']['uid']
        assert 'note' in result['details']
        assert MESSAGE['note'] == result['details']['note']
        assert 'msg' in result['details']
        assert MESSAGE['msg'] == result['details']['msg']
        assert 'src' not in result['details']
        assert 'sourceipv6address' in result['details']
        assert MESSAGE['src'] == result['details']['sourceipv6address']
        assert 'p' in result['details']
        assert MESSAGE['p'] == result['details']['p']
        assert result['details']['indicators']
        assert MESSAGE['src'] in result['details']['indicators']
        assert result['summary'] == "Scan::Address_Scan source 2620:101:80fc:232:b5a9:5071:1dc1:1499 destination unknown port 445"

    def test_snmp_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_snmp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703535.041376,
            "uid":"ClusjHyL4YWvyV0rd",
            "sourceipaddress":"10.22.75.137",
            "sourceport":36318,
            "destinationipaddress":"10.26.8.128",
            "destinationport":161,
            "duration":0.012456,
            "version":"2c",
            "community":"yourcommunity",
            "get_requests":90,
            "get_bulk_requests":0,
            "get_responses":120,
            "set_requests":0
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SNMPv2c: 10.22.75.137 -> 10.26.8.128:161 (90 get / 0 set requests 120 get responses)'

    def test_snmp_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_snmp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703535.041376,
            "uid":"ClusjHyL4YWvyV0rd",
            "sourceipaddress":"10.22.75.137",
            "sourceport":36318,
            "destinationipaddress":"10.26.8.128",
            "destinationport":161,
            "duration":0.012456,
            "community":"yourcommunity"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SNMPvUnknown: 10.22.75.137 -> 10.26.8.128:161 (0 get / 0 set requests 0 get responses)'

    def test_rdp_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_rdp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1297551041.284715,
            "uid":"CbbyKC4V7tEzua9N8h",
            "sourceipaddress":"192.168.1.200",
            "sourceport":49206,
            "destinationipaddress":"192.168.1.150",
            "destinationport":3389,
            "cookie":"AWAKECODI",
            "result":"encrypted",
            "security_protocol":"HYBRID",
            "cert_count":0
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'RDP: 192.168.1.200 -> 192.168.1.150:3389'

    def test_rdp_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_rdp',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1297551041.284715,
            "uid":"CbbyKC4V7tEzua9N8h",
            "sourceipaddress":"192.168.1.200",
            "sourceport":49206,
            "destinationipaddress":"192.168.1.150",
            "destinationport":3389,
            "result":"encrypted",
            "security_protocol":"HYBRID",
            "cert_count":0,
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'cookie' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'RDP: 192.168.1.200 -> 192.168.1.150:3389'

    def test_sip_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_sip',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1120469590.259876,
            "uid":"C4tJSk2uEibu6Ty4hc",
            "id.orig_h":"192.168.1.2",
            "id.orig_p":5060,
            "id.resp_h":"212.242.33.35",
            "id.resp_p":5060,
            "trans_depth":0,
            "method":"REGISTER",
            "uri":"sip:sip.cybercity.dk",
            "request_from":"<sip:voi18063@sip.cybercity.dk>",
            "request_to":"<sip:voi18063@sip.cybercity.dk>",
            "response_from":"<sip:voi18063@sip.cybercity.dk>",
            "response_to":"<sip:voi18063@sip.cybercity.dk>",
            "call_id":"578222729-4665d775@578222732-4665d772",
            "seq":"69 REGISTER",
            "request_path":["SIP/2.0/UDP 192.168.1.2"],
            "response_path":["SIP/2.0/UDP 192.168.1.2;received=80.230.219.70;rport=5060"],
            "user_agent":"Nero SIPPS IP Phone Version 2.0.51.16",
            "status_code":100,
            "status_msg":"Trying",
            "request_body_len":0,
            "response_body_len":0
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SIP: 192.168.1.2 -> 212.242.33.35:5060 method REGISTER status Trying'

    def test_sip_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_sip',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1120469590.259876,
            "uid":"C4tJSk2uEibu6Ty4hc",
            "id.orig_h":"192.168.1.2",
            "id.orig_p":5060,
            "id.resp_h":"212.242.33.35",
            "id.resp_p":5060,
            "trans_depth":0,
            "request_from":"<sip:voi18063@sip.cybercity.dk>",
            "request_to":"<sip:voi18063@sip.cybercity.dk>",
            "response_from":"<sip:voi18063@sip.cybercity.dk>",
            "response_to":"<sip:voi18063@sip.cybercity.dk>",
            "call_id":"578222729-4665d775@578222732-4665d772",
            "seq":"69 REGISTER",
            "request_path":["SIP/2.0/UDP 192.168.1.2"],
            "response_path":["SIP/2.0/UDP 192.168.1.2;received=80.230.219.70;rport=5060"],
            "user_agent":"Nero SIPPS IP Phone Version 2.0.51.16",
            "request_body_len":0,
            "response_body_len":0
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'method' in result['details']
        assert 'uri' in result['details']
        assert 'status_msg' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SIP: 192.168.1.2 -> 212.242.33.35:5060 method unknown status unknown'

    def test_software_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_software',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703596.442367,
            "host":"10.8.81.221",
            "software_type":"HTTP::BROWSER",
            "name":"Thunderbird",
            "version.major":16,
            "version.minor":0,
            "version.minor2":1,
            "unparsed_version":"Mozilla/5.0 (X11; Linux i686; rv:16.0) Gecko/20121010 Thunderbird/16.0.1"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            # We check for version outside of loop
            if key.startswith('version.'):
                continue
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'Found HTTP::BROWSER software on 10.8.81.221'
        assert 'version' not in result['details']
        assert result['details']['parsed_version'] == {'major': 16, 'minor': 0, 'minor2': 1}

    def test_software_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_software',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703596.442367,
            "host":"10.8.81.221",
            "version.major":16,
            "version.minor":0,
            "version.minor2":1,
            "unparsed_version":"Mozilla/5.0 (X11; Linux i686; rv:16.0) Gecko/20121010 Thunderbird/16.0.1",
            'category': 'bro',
            'source': 'software',
            'customendpoint': 'bro'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            # We check for version outside of loop
            if key.startswith('version.'):
                continue
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'Found unknown software on 10.8.81.221'
        assert 'version' not in result['details']
        assert result['details']['parsed_version'] == {'major': 16, 'minor': 0, 'minor2': 1}

    def test_socks_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_socks',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1340213015.276495,
            "uid":"CUy63t6qOCaFvn6nd",
            "id.orig_h":"10.0.0.55",
            "id.orig_p":53994,
            "id.resp_h":"60.190.189.214",
            "id.resp_p":8124,
            "version":5,
            "status":"succeeded",
            "request.name":"www.osnews.com",
            "request_p":80,
            "bound.host":"192.168.0.31",
            "bound_p":2688
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SOCKSv5: 10.0.0.55 -> 60.190.189.214:8124 status succeeded'

    def test_socks_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_socks',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1340213015.276495,
            "uid":"CUy63t6qOCaFvn6nd",
            "id.orig_h":"10.0.0.55",
            "id.orig_p":53994,
            "id.resp_h":"60.190.189.214",
            "id.resp_p":8124,
            "request.name":"www.osnews.com",
            "request_p":80,
            "bound.host":"192.168.0.31",
            "bound_p":2688
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'status' in result['details']
        assert 'version' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'SOCKSv0: 10.0.0.55 -> 60.190.189.214:8124 status unknown'

    def test_dcerpc_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_dce_rpc',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701213.40556,
            "uid":"C2g5CK5JxgQ5x6b",
            "id.orig_h":"10.26.40.121",
            "id.orig_p":49446,
            "id.resp_h":"10.22.69.21",
            "id.resp_p":445,
            "rtt":0.001135,
            "named_pipe":"\u005cpipe\u005clsass",
            "endpoint":"samr",
            "operation":"SamrEnumerateDomainsInSamServer"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'DCERPC: 10.26.40.121 -> 10.22.69.21:445'

    def test_dcerpc_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_dce_rpc',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701213.40556,
            "uid":"C2g5CK5JxgQ5x6b",
            "id.orig_h":"10.26.40.121",
            "id.orig_p":49446,
            "id.resp_h":"10.22.69.21",
            "id.resp_p":445,
            "rtt":0.001135,
            "named_pipe":"\u005cpipe\u005clsass"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'endpoint' in result['details']
        assert 'operation' in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == 'DCERPC: 10.26.40.121 -> 10.22.69.21:445'

    def test_kerberos_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_kerberos',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701219.06897,
            "uid":"CQ9RPTR8ORJEgof37",
            "id.orig_h":"10.26.40.121",
            "id.orig_p":49467,
            "id.resp_h":"10.22.69.21",
            "id.resp_p":88,
            "request_type":"TGS",
            "service":"host/t-w864-ix-091.releng.ad.mozilla.com",
            "till":2136422885.0,
            "forwardable":'true',
            "renewable":'true',
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'success' not in result['details']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
        assert result['summary'] == '10.26.40.121 -> 10.22.69.21:88 request TGS success unknown'

    def test_kerberos_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_kerberos',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1421708043.07936,
            "uid":"CjoUSf1cih7HpLipTf",
            "id.orig_h":"192.168.1.31",
            "id.orig_p":64726,
            "id.resp_h":"192.168.1.32",
            "id.resp_p":88,
            "request_type":"AS",
            "client":"valid_client_principal/VLADG.NET",
            "service":"krbtgt/VLADG.NET",
            "success":'True',
            "till":1421708111.0,
            "cipher":"aes256-cts-hmac-sha1-96",
            "forwardable":'false',
            "renewable":'true',
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert MESSAGE['success'] == result['details']['success']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == '192.168.1.31 -> 192.168.1.32:88 request AS success True'

    def test_kerberos_log3(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_kerberos',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1421708043.196544,
            "uid":"CIOsYa3u0IxeiYPH7d",
            "id.orig_h":"192.168.1.31",
            "id.orig_p":58922,
            "id.resp_h":"192.168.1.32",
            "id.resp_p":88,
            "request_type":"TGS",
            "client":"valid_client_principal/VLADG.NET",
            "service":"krbtgt/VLADG.NET",
            "success":'False',
            "error_msg":"TICKET NOT RENEWABLE",
            "till":1421708111.0,
            "forwardable":'false',
            "renewable":'false'
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert MESSAGE['success'] == result['details']['success']
        for key in MESSAGE.keys():
            if not key.startswith('id.'):
                assert key in result['details']
                assert MESSAGE[key] == result['details'][key]
        assert result['summary'] == '192.168.1.31 -> 192.168.1.32:88 request TGS success False'

    def test_ntlm_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ntlm',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701552.66651,
            "uid":"Cml9hN1SSy5nwYEVLl",
            "id.orig_h":"10.26.40.48",
            "id.orig_p":49176,
            "id.resp_h":"10.22.69.18",
            "id.resp_p":445,
            "username":"T-W864-IX-018$",
            "hostname":"T-W864-IX-018",
            "domainname":"RELENG",
            "success":'True',
            "status":"SUCCESS",
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert MESSAGE['username'] == result['details']['ntlm']['username']
        assert MESSAGE['hostname'] == result['details']['ntlm']['hostname']
        assert MESSAGE['domainname'] == result['details']['ntlm']['domainname']
        assert MESSAGE['success'] == result['details']['success']
        assert MESSAGE['status'] == result['details']['status']
        assert result['summary'] == 'NTLM: 10.26.40.48 -> 10.22.69.18:445 success True status SUCCESS'

    def test_ntlm_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_ntlm',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505701552.66651,
            "uid":"Cml9hN1SSy5nwYEVLl",
            "id.orig_h":"10.26.40.48",
            "id.orig_p":49176,
            "id.resp_h":"10.22.69.18",
            "id.resp_p":445
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'username' in result['details']['ntlm']
        assert 'hostname' in result['details']['ntlm']
        assert 'domainname' in result['details']['ntlm']
        assert 'success' not in result['details']
        assert 'status' in result['details']
        assert result['summary'] == 'NTLM: 10.26.40.48 -> 10.22.69.18:445 success unknown status unknown'

    def test_smbfiles_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_smb_files',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703595.833874,
            "uid":"C8vKSp2oSqoQtJZyM2",
            "id.orig_h":"10.26.42.82",
            "id.orig_p":53939,
            "id.resp_h":"10.22.69.21",
            "id.resp_p":445,
            "action":"SMB::FILE_OPEN",
            "name":"releng.ad.mozilla.com\u005cPolicies\u005c{8614FE9A-333C-47C1-9EFD-856B4DF64883}\u005cMachine\u005cPreferences\u005cScheduledTasks",
            "path":"\u005c\u005cDC8.releng.ad.mozilla.com\u005cSysVol",
            "size":4096,
            "times.modified":1401486067.13068,
            "times.accessed":1401486067.13068,
            "times.created":1393344470.022491,
            "times.changed":1401486067.13068
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert toUTC(float(MESSAGE['times.modified'])).isoformat() == result['details']['smbtimes']['modified']
        assert toUTC(float(MESSAGE['times.accessed'])).isoformat() == result['details']['smbtimes']['accessed']
        assert toUTC(float(MESSAGE['times.created'])).isoformat() == result['details']['smbtimes']['created']
        assert toUTC(float(MESSAGE['times.changed'])).isoformat() == result['details']['smbtimes']['changed']
        assert 'uid' in result['details']
        assert MESSAGE['uid'] == result['details']['uid']
        assert 'action' in result['details']
        assert MESSAGE['action'] == result['details']['action']
        assert 'name' in result['details']
        assert MESSAGE['name'] == result['details']['name']
        assert 'path' in result['details']
        assert MESSAGE['path'] == result['details']['path']
        assert 'size' in result['details']
        assert MESSAGE['size'] == result['details']['size']
        assert result['summary'] == 'SMB file: 10.26.42.82 -> 10.22.69.21:445 SMB::FILE_OPEN'

    def test_smbfiles_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_smb_files',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703595.833874,
            "uid":"C8vKSp2oSqoQtJZyM2",
            "id.orig_h":"10.26.42.82",
            "id.orig_p":53939,
            "id.resp_h":"10.22.69.21",
            "id.resp_p":445,
            "size":4096,
            "times.modified":1401486067.13068,
            "times.accessed":1401486067.13068,
            "times.created":1393344470.022491,
            "times.changed":1401486067.13068
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert toUTC(float(MESSAGE['times.modified'])).isoformat() == result['details']['smbtimes']['modified']
        assert toUTC(float(MESSAGE['times.accessed'])).isoformat() == result['details']['smbtimes']['accessed']
        assert toUTC(float(MESSAGE['times.created'])).isoformat() == result['details']['smbtimes']['created']
        assert toUTC(float(MESSAGE['times.changed'])).isoformat() == result['details']['smbtimes']['changed']
        assert 'uid' in result['details']
        assert 'action' in result['details']
        assert 'name' in result['details']
        assert 'path' in result['details']
        assert 'size' in result['details']
        assert result['summary'] == 'SMB file: 10.26.42.82 -> 10.22.69.21:445 '

    def test_smbmapping_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_smb_mapping',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703606.752588,
            "uid":"CgvFmm2FAseGbXjC6h",
            "id.orig_h":"10.26.41.138",
            "id.orig_p":49720,
            "id.resp_h":"10.22.69.18",
            "id.resp_p":445,
            "path":"\u005c\u005cDC6\u005cSYSVOL",
            "share_type":"DISK"
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'uid' in result['details']
        assert MESSAGE['uid'] == result['details']['uid']
        assert 'path' in result['details']
        assert MESSAGE['path'] == result['details']['path']
        assert 'share_type' in result['details']
        assert MESSAGE['share_type'] == result['details']['share_type']
        assert result['summary'] == 'SMB mapping: 10.26.41.138 -> 10.22.69.18:445 DISK'

    def test_smbmapping_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_smb_mapping',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703606.752588,
            "uid":"CgvFmm2FAseGbXjC6h",
            "id.orig_h":"10.26.41.138",
            "id.orig_p":49720,
            "id.resp_h":"10.22.69.18",
            "id.resp_p":445
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'uid' in result['details']
        assert MESSAGE['uid'] == result['details']['uid']
        assert 'path' in result['details']
        assert 'share_type' in result['details']
        assert result['summary'] == 'SMB mapping: 10.26.41.138 -> 10.22.69.18:445 '

    def test_x509_log(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_x509',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703595.73864,
            "id":"FNe2XU16VWFNvpk9F2",
            "certificate.version":3,
            "certificate.serial":"34B52BD83D80C284892AC63850038833",
            "certificate.subject":"CN=ssl.wsj.com,OU=Dow Jones and Company,O=Dow Jones and Company,L=Princeton,ST=New Jersey,C=US",
            "certificate.issuer":"CN=GeoTrust SSL CA - G3,O=GeoTrust Inc.,C=US",
            "certificate.not_valid_before":1498608000.0,
            "certificate.not_valid_after":1527379199.0,
            "certificate.key_alg":"rsaEncryption",
            "certificate.sig_alg":"sha256WithRSAEncryption",
            "certificate.key_type":"rsa",
            "certificate.key_length":2048,
            "certificate.exponent":"65537",
            "san.dns":["m-secure.wsj.net","kr.wsj.com","newsplus.stg.wsj.com","services.dowjones.com","si2.wsj.net","djlogin.stg.dowjones.com","si3.wsj.net","fonts.wsj.net","global.stg.factiva.com","graphics.wsj.com","www.wsj.com","s1.wsj.net","global.factiva.com","cdn.store.wsj.net","m.wsj.net","api.barrons.com","s1.marketwatch.com","city.wsj.com","portfolio.wsj.com","m.barrons.com","s3.marketwatch.com","sts3.wsj.net","s3.wsj.net","rwidget.wsj.net","ss.wsj.net","djlogin.dowjones.com","admin.stream.marketwatch.com","vir.www.wsj.com","cdn.smpdev.wsj.net","si1.wsj.net","art-secure.wsj.net","sc.wsj.net","indo.wsj.com","m.wsj.com","blogs.barrons.com","graphicsweb.wsj.com","widgets.dowjones.com","sj.wsj.net","blogs.marketwatch.com","s4.marketwatch.com","api-staging.wsj.net","blogs.wsj.com","api.wsj.net","newsplus.wsj.com","s2.wsj.net","salesforce.dowjones.com","v-secure.wsj.net","signin.wsj.com","salesforce.stg.dowjones.com","symphony.dowjones.com","admin.stream.wsj.com","suggest.stg.dowjones.com","www.stg.wsj.com","api.beta.dowjones.com","podcast.mktw.net","si4.wsj.net","help.wsj.com","api-staging.barrons.com","s4.wsj.net","ore.www.wsj.com","s2.marketwatch.com","cbuy.wsj.com","assets.efinancialnews.com","video-api.wsj.net","video-api-secure.wsj.com","portfolio.marketwatch.com","dr.marketwatch.com","onlinedr.wsj.com","api.stg.dowjones.com","sf.wsj.net","portfolio.barrons.com","signin.stg.wsj.com","video-api.wsj.com","symphony.stg.dowjones.com","art.wsj.net","widgets.stg.dowjones.com","api-secure.wsj.net","suggest.dowjones.com","sg.wsj.net","api-staging-secure.wsj.net","guides.wsj.com","m.jp.wsj.com","api.dowjones.com","video-api-secure.stg.wsj.com","s.wsj.net","api-staging.wsj.com","np3.stg.wsj.com","sfonts.wsj.net","www.ssl.wsj.com","api.wsj.com","s.marketwatch.com","realtime.wsj.com","newsletters.barrons.com","si.wsj.net","projects.wsj.com","m.cn.wsj.com","wn.wsj.com","ssl.wsj.com"],
            "basic_constraints.ca":"false",
            "basic_constraints.path_len": 0
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'id' in result['details']
        assert MESSAGE['id'] == result['details']['id']
        assert 'basic_constraints_ca' in result['details']['certificate']
        assert MESSAGE['basic_constraints.ca'] == result['details']['certificate']['basic_constraints_ca']
        assert 'basic_constraints_path_len' in result['details']['certificate']
        assert MESSAGE['basic_constraints.path_len'] == result['details']['certificate']['basic_constraints_path_len']
        assert 'not_valid_before' in result['details']['certificate']
        assert toUTC(float(MESSAGE['certificate.not_valid_before'])).isoformat() == result['details']['certificate']['not_valid_before']
        del MESSAGE['certificate.not_valid_before']
        assert 'not_valid_after' in result['details']['certificate']
        assert toUTC(float(MESSAGE['certificate.not_valid_after'])).isoformat() == result['details']['certificate']['not_valid_after']
        del MESSAGE['certificate.not_valid_after']
        for key in MESSAGE.keys():
            if key.startswith('certificate'):
                assert key[12:] in result['details']['certificate']
                assert MESSAGE[key] == result['details']['certificate'][key[12:]]
        assert result['summary'] == 'X509 certificate seen'

    def test_x509_log2(self):
        event = {
            'category': 'bro',
            'SOURCE': 'bro_x509',
            'customendpoint': 'bro'
        }
        MESSAGE = {
            "ts":1505703595.73864,
            "id":"FNe2XU16VWFNvpk9F2",
            "certificate.version":3,
            "certificate.subject":"CN=ssl.wsj.com,OU=Dow Jones and Company,O=Dow Jones and Company,L=Princeton,ST=New Jersey,C=US",
            "certificate.issuer":"CN=GeoTrust SSL CA - G3,O=GeoTrust Inc.,C=US",
            "certificate.not_valid_before":1498608000.0,
            "certificate.not_valid_after":1527379199.0,
            "certificate.key_alg":"rsaEncryption",
            "certificate.sig_alg":"sha256WithRSAEncryption",
            "certificate.key_type":"rsa",
            "certificate.key_length":2048,
            "certificate.exponent":"65537",
            "san.dns":["m-secure.wsj.net","kr.wsj.com","newsplus.stg.wsj.com","services.dowjones.com","si2.wsj.net","djlogin.stg.dowjones.com","si3.wsj.net","fonts.wsj.net","global.stg.factiva.com","graphics.wsj.com","www.wsj.com","s1.wsj.net","global.factiva.com","cdn.store.wsj.net","m.wsj.net","api.barrons.com","s1.marketwatch.com","city.wsj.com","portfolio.wsj.com","m.barrons.com","s3.marketwatch.com","sts3.wsj.net","s3.wsj.net","rwidget.wsj.net","ss.wsj.net","djlogin.dowjones.com","admin.stream.marketwatch.com","vir.www.wsj.com","cdn.smpdev.wsj.net","si1.wsj.net","art-secure.wsj.net","sc.wsj.net","indo.wsj.com","m.wsj.com","blogs.barrons.com","graphicsweb.wsj.com","widgets.dowjones.com","sj.wsj.net","blogs.marketwatch.com","s4.marketwatch.com","api-staging.wsj.net","blogs.wsj.com","api.wsj.net","newsplus.wsj.com","s2.wsj.net","salesforce.dowjones.com","v-secure.wsj.net","signin.wsj.com","salesforce.stg.dowjones.com","symphony.dowjones.com","admin.stream.wsj.com","suggest.stg.dowjones.com","www.stg.wsj.com","api.beta.dowjones.com","podcast.mktw.net","si4.wsj.net","help.wsj.com","api-staging.barrons.com","s4.wsj.net","ore.www.wsj.com","s2.marketwatch.com","cbuy.wsj.com","assets.efinancialnews.com","video-api.wsj.net","video-api-secure.wsj.com","portfolio.marketwatch.com","dr.marketwatch.com","onlinedr.wsj.com","api.stg.dowjones.com","sf.wsj.net","portfolio.barrons.com","signin.stg.wsj.com","video-api.wsj.com","symphony.stg.dowjones.com","art.wsj.net","widgets.stg.dowjones.com","api-secure.wsj.net","suggest.dowjones.com","sg.wsj.net","api-staging-secure.wsj.net","guides.wsj.com","m.jp.wsj.com","api.dowjones.com","video-api-secure.stg.wsj.com","s.wsj.net","api-staging.wsj.com","np3.stg.wsj.com","sfonts.wsj.net","www.ssl.wsj.com","api.wsj.com","s.marketwatch.com","realtime.wsj.com","newsletters.barrons.com","si.wsj.net","projects.wsj.com","m.cn.wsj.com","wn.wsj.com","ssl.wsj.com"],
            "basic_constraints.ca":'false',
            "basic_constraints.path_len": 0
        }
        event['MESSAGE'] = json.dumps(MESSAGE)

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(MESSAGE['ts']).isoformat() == result['utctimestamp']
        assert toUTC(MESSAGE['ts']).isoformat() == result['timestamp']
        assert 'id' in result['details']
        assert MESSAGE['id'] == result['details']['id']
        assert 'basic_constraints_ca' in result['details']['certificate']
        assert MESSAGE['basic_constraints.ca'] == result['details']['certificate']['basic_constraints_ca']
        assert 'basic_constraints_path_len' in result['details']['certificate']
        assert MESSAGE['basic_constraints.path_len'] == result['details']['certificate']['basic_constraints_path_len']
        assert 'not_valid_before' in result['details']['certificate']
        assert toUTC(float(MESSAGE['certificate.not_valid_before'])).isoformat() == result['details']['certificate']['not_valid_before']
        del MESSAGE['certificate.not_valid_before']
        assert 'not_valid_after' in result['details']['certificate']
        assert toUTC(float(MESSAGE['certificate.not_valid_after'])).isoformat() == result['details']['certificate']['not_valid_after']
        del MESSAGE['certificate.not_valid_after']
        for key in MESSAGE.keys():
            if key.startswith('certificate'):
                assert key[12:] in result['details']['certificate']
                assert MESSAGE[key] == result['details']['certificate'][key[12:]]
        assert result['summary'] == 'X509 certificate seen'
