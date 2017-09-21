import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../lib"))
from utilities.toUTC import toUTC

import mock

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../mq/plugins"))
from broFixup import message


class TestBroFixup(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {
            'doc_type': 'event',
            'index': 'events'
        }

    @mock.patch('broFixup.node')
    def test_mozdefhostname_mock_string(self, mock_path):
        mock_path.return_value = 'samplehostname'
        event = {}
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result['mozdefhostname'] == 'samplehostname'

    @mock.patch('broFixup.node')
    def test_mozdefhostname_mock_exception(self, mock_path):
        mock_path.side_effect = ValueError
        event = {}
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result['mozdefhostname'] == 'failed to fetch mozdefhostname'

    def verify_metadata(self, metadata):
        assert metadata['doc_type'] == 'nsm'

    def test_defaults(self):
        event = {}
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details'] == {}

    def verify_defaults(self, result):
        assert result['category'] == 'bro'
        assert result['customendpoint'] == 'bro'
        assert result['eventsource'] == 'nsm'
        assert toUTC(result['receivedtimestamp']).isoformat() == result['receivedtimestamp']
        assert result['severity'] == 'INFO'
        assert toUTC(result['timestamp']).isoformat() == result['timestamp']
        assert toUTC(result['utctimestamp']).isoformat() == result['utctimestamp']

    # Would just need to duplicate this function, with your event json as the event variable
    def test_conn_log(self):
        event = {
            'conn_state': 'SF',
            'duration': 0.047874,
            'history': 'ShADadfF',
            'sourceipaddress': '1.2.3.4',
            'sourceport': 39246,
            'destinationipaddress': '5.6.7.8',
            'destinationport': 80,
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
            'uid': 'CYxwva4RBFtKpxWLba',
            'category': 'bro',
            'type': 'conn',
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        # Then need to add assert statements here for the values that you've changed in the plugin
        # for example:  assert result['summary'] == 'Modified summary from plugin'
        assert result['details']['originipbytes'] == 2452
        assert result['details']['responseipbytes'] == 2132
        assert 'orig_ip_bytes' not in result['details']
        assert 'resp_ip_bytes' not in result['details']
        assert 'history' in result['details']
        assert result['summary'] == '1.2.3.4:39246 -> 5.6.7.8:80 ShADadfF 2452 bytes / 2132 bytes'

    def test_files_log(self):
        event = {
            "ts":1505701210.155542,
            "fuid":"FxAKGz3eoA79wYCAwc",
            "tx_hosts":["23.61.194.147"],
            "rx_hosts":["63.245.214.159"],
            "conn_uids":["CucQNa2qHds42xa5na"],
            "source":"HTTP",
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
            'category': 'bro',
            'type': 'files'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['details']['sourceipaddress'] == '63.245.214.159'
        assert result['details']['destinationipaddress'] == '23.61.194.147'
        assert result['summary'] == '63.245.214.159 downloaded (MD5) f30cb6b67044c9871b51dc0263717c92 filename arandomfile MIME application/ocsp-response (527 bytes) from 23.61.194.147 via HTTP'

    def test_files_log2(self):
        event = {
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
            "timedout":'false',
            'category': 'bro',
            'type': 'files'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['details']['sourceipaddress'] == '63.245.214.159'
        assert result['details']['destinationipaddress'] == '23.61.194.147'
        assert 'md5' in result['details']
        assert 'filename' in result['details']
        assert 'mime_type' in result['details']
        assert 'source' in result['details']
        assert result['summary'] == '63.245.214.159 downloaded (MD5) None filename unknown MIME unknown (527 bytes) from 23.61.194.147 via None'

    def test_dns_log(self):
        event = {
            "ts":1505701210.060553,
            "uid":"C6gQDU2AZJBxU1n3qd",
            "sourceipaddress":"10.22.81.65",
            "sourceport":14092,
            "destinationipaddress":"10.22.75.41",
            "destinationport":53,
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
            "rejected":'false',
            'category': 'bro',
            'type': 'dns'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == '10.22.81.65 -> 10.22.75.41:53 PTR 50.75.8.10.in-addr.arpa NOERROR'
    
    def test_dns_log2(self):
        event = {
            "ts":1505701210.060553,
            "uid":"C6gQDU2AZJBxU1n3qd",
            "sourceipaddress":"10.22.81.65",
            "sourceport":14092,
            "destinationipaddress":"10.22.75.41",
            "destinationport":53,
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
            "rejected":'false',
            'category': 'bro',
            'type': 'dns'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'rcode_name' in result['details']
        assert 'query' in result['details']
        assert 'qtype_name' in result['details']
        assert result['summary'] == '10.22.81.65 -> 10.22.75.41:53   '

    def test_http_log(self):
        event =  {
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
            'category': 'bro',
            'type': 'http'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'status_code' in result['details']
        assert 'uri' in result['details']
        assert 'host' in result['details']
        assert 'method' in result['details']
        assert result['summary'] == 'GET hg.mozilla.org /projects/build-system?cmd=batch 200'

    def test_ssl_log(self):
        event = {
            "ts":1502751597.597052,
            "uid":"CWmwax23B9dBtn3s16",
            "sourceipaddress":"36.70.241.31",
            "sourceport":49322,
            "destinationipaddress":"63.245.215.82",
            "destinationport":443,
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
            "pfs":'true',
            'category': 'bro',
            'type': 'ssl'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == 'SSL: 36.70.241.31 -> 63.245.215.82:443 geo.mozilla.org'
    
    def test_ssl_log2(self):
        event = {
            "ts":1502751597.597052,
            "uid":"CWmwax23B9dBtn3s16",
            "sourceipaddress":"36.70.241.31",
            "sourceport":49322,
            "destinationipaddress":"63.245.215.82",
            "destinationport":443,
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
            "pfs":'true',
            'category': 'bro',
            'type': 'ssl'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'server_name' in result['details']
        assert result['summary'] == 'SSL: 36.70.241.31 -> 63.245.215.82:443 63.245.215.82'

    def test_dhcp_log(self):
        event = {
            "ts":1505701256.181043,
            "uid":"Cbs59u2x6KXu85dsOi",
            "sourceipaddress":"10.26.40.65",
            "sourceport":68,
            "destinationipaddress":"10.26.40.1",
            "destinationport":67,
            "mac":"00:25:90:9b:67:b2",
            "assigned_ip":"10.26.40.65",
            "lease_time":86400.0,
            "trans_id":1504605887,
            'category': 'bro',
            'type': 'dhcp'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == '10.26.40.65 assigned to 00:25:90:9b:67:b2'

    def test_ftp_log(self):
        event = {
            "ts":1363628702.035108,
            "uid":"CdS183kIs8TBugKDf",
            "sourceipaddress":"141.142.228.5",
            "sourceport":50736,
            "destinationipaddress":"141.142.192.162",
            "destinationport":21,
            "user":"anonymous",
            "password":"chrome@example.com",
            "command":"EPSV",
            "reply_code":229,
            "reply_msg":"Entering Extended Passive Mode (|||38141|)",
            "data_channel.passive":'true',
            "data_channel.orig_h":"141.142.228.5",
            "data_channel.resp_h":"141.142.192.162",
            "data_channel.resp_p":38141,
            'category': 'bro',
            'type': 'ftp'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == 'FTP: 141.142.228.5 -> 141.142.192.162:21 EPSV anonymous'

    def test_ftp_log2(self):
        event = {
            "ts":1363628702.035108,
            "uid":"CdS183kIs8TBugKDf",
            "sourceipaddress":"141.142.228.5",
            "sourceport":50736,
            "destinationipaddress":"141.142.192.162",
            "destinationport":21,
            "password":"chrome@example.com",
            "reply_code":229,
            "reply_msg":"Entering Extended Passive Mode (|||38141|)",
            "data_channel.passive":'true',
            "data_channel.orig_h":"141.142.228.5",
            "data_channel.resp_h":"141.142.192.162",
            "data_channel.resp_p":38141,
            'category': 'bro',
            'type': 'ftp'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'command' in result['details']
        assert 'user' in result['details']
        assert result['summary'] == 'FTP: 141.142.228.5 -> 141.142.192.162:21  '

    def test_pe_log(self):
        event = {
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
            "section_names":[".text",".rdata",".data",".rsrc",".reloc"],
            'category': 'bro',
            'type': 'pe'
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == 'PE file: Windows 95 or NT 4.0 WINDOWS_GUI'

    def test_pe_log2(self):
        event = {
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
            "section_names":[".text",".rdata",".data",".rsrc",".reloc"],
            'category': 'bro',
            'type': 'pe'
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'subsystem' in result['details']
        assert 'os' in result['details']
        assert result['summary'] == 'PE file:  '

    def test_smtp_log(self):
        event = {
            "ts":1505703597.295432,
            "uid":"Ct7e4waRBwsLoRvfg",
            "sourceipaddress":"63.245.214.155",
            "sourceport":4523,
            "destinationipaddress":"128.199.139.6",
            "destinationport":25,
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
            "is_webmail":'false',
            'category': 'bro',
            'type': 'smtp'
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        #assert result['summary'] == 'SMTP: 63.245.214.155 -> 128.199.139.6:25 from \u0022Bugzilla@Mozilla\u0022 <bugzilla-daemon@mozilla.org> to bugmail@firebot.glob.uno ID <bug-1400759-507647@https.bugzilla.mozilla.org/>'.decode('unicode-escape')
    
    def test_smtp_log2(self):
        event = {
            "ts":1505703597.295432,
            "uid":"Ct7e4waRBwsLoRvfg",
            "sourceipaddress":"63.245.214.155",
            "sourceport":4523,
            "destinationipaddress":"128.199.139.6",
            "destinationport":25,
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
            "is_webmail":'false',
            'category': 'bro',
            'type': 'smtp'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'from' in result['details']
        assert 'to' in result['details']
        assert 'msg_id' in result['details']
    
    def test_ssh_log(self):
        event = {
            "ts":1505703601.393284,
            "uid":"CBiwrdGg2CGf0Y6U9",
            "sourceipaddress":"63.245.214.162",
            "sourceport":22418,
            "destinationipaddress":"192.30.255.112",
            "destinationport":22,
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
            "host_key":"16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48",
            'category': 'bro',
            'type': 'ssh'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == 'SSH: 63.245.214.162 -> 192.30.255.112:22 success true'

    def test_ssh_log2(self):
        event = {
            "ts":1505703601.393284,
            "uid":"CBiwrdGg2CGf0Y6U9",
            "sourceipaddress":"63.245.214.162",
            "sourceport":22418,
            "destinationipaddress":"192.30.255.112",
            "destinationport":22,
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
            "host_key":"16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48",
            'category': 'bro',
            'type': 'ssh'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'auth_success' in result['details']
        assert result['summary'] == 'SSH: 63.245.214.162 -> 192.30.255.112:22 success unknown'
    
    def test_tunnel_log(self):
        event = {
            "ts":1505703604.92601,
            "sourceipaddress":"10.22.24.167",
            "sourceport":0,
            "destinationipaddress":"10.22.74.74",
            "destinationport":3128,
            "tunnel_type":"Tunnel::HTTP",
            "action":"Tunnel::DISCOVER",
            'category': 'bro',
            'type': 'tunnel'
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == '10.22.24.167 -> 10.22.74.74:3128 Tunnel::HTTP Tunnel::DISCOVER'
    
    def test_tunnel_log2(self):
        event = {
            "ts":1505703604.92601,
            "sourceipaddress":"10.22.24.167",
            "sourceport":0,
            "destinationipaddress":"10.22.74.74",
            "destinationport":3128,
            'category': 'bro',
            'type': 'tunnel'
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'tunnel_type' in result['details']
        assert 'action' in result['details']
        assert result['summary'] == '10.22.24.167 -> 10.22.74.74:3128  '
    
    def test_intel_log(self):
        event = {
            "ts":1505701213.244219,
            "uid":"CwO41Y3TzqvScTyRk",
            "sourceipaddress":"10.8.81.221",
            "sourceport":46606,
            "destinationipaddress":"10.8.81.42",
            "destinationport":81,
            "seenindicator":"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)",
            "seen.indicator_type":"Intel::SOFTWARE",
            "seenwhere":"HTTP::IN_USER_AGENT_HEADER",
            "seennode":"nsm-stage1-eth4-4",
            "matched":["Intel::SOFTWARE"],
            "sources":["test"],
            'category':'bro',
            'type':'intel'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == 'Bro intel match: Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

    def test_intel_log2(self):
        event = {
            "ts":1505701213.244219,
            "uid":"CwO41Y3TzqvScTyRk",
            "sourceipaddress":"10.8.81.221",
            "sourceport":46606,
            "destinationipaddress":"10.8.81.42",
            "destinationport":81,
            "seen.indicator_type":"Intel::SOFTWARE",
            "seen.where":"HTTP::IN_USER_AGENT_HEADER",
            "seen.node":"nsm-stage1-eth4-4",
            "matched":["Intel::SOFTWARE"],
            "sources":["test"],
            'category':'bro',
            'type':'intel'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'seenindicator' in result['details']
        assert result['summary'] == 'Bro intel match: '
    
    def test_knowncerts_log(self):
        event = {
            "ts":1505701209.939031,
            "host":"10.22.75.54",
            "port_num":8443,
            "subject":"CN=syslog1.private.scl3.mozilla.com,OU=WebOps,O=Mozilla Corporation,L=Mountain View,ST=California,C=US",
            "issuer_subject":"CN=DigiCert SHA2 Secure Server CA,O=DigiCert Inc,C=US",
            "serial":"0B2BF706734AA1CCC969F7990FD20424",
            'category': 'bro',
            'type': 'knowncerts'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert result['summary'] == 'Certificate seen from: 10.22.75.54:8443 serial 0B2BF706734AA1CCC969F7990FD20424'
    
    def test_knowncerts_log2(self):
        event = {
            "ts":1505701209.939031,
            "host":"10.22.75.54",
            "port_num":8443,
            "subject":"CN=syslog1.private.scl3.mozilla.com,OU=WebOps,O=Mozilla Corporation,L=Mountain View,ST=California,C=US",
            "issuer_subject":"CN=DigiCert SHA2 Secure Server CA,O=DigiCert Inc,C=US",
            'category': 'bro',
            'type': 'knowncerts'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'serial' in result['details']
        assert result['summary'] == 'Certificate seen from: 10.22.75.54:8443 serial 0'
    
    def test_notice_log(self):
        event = {
            "ts":1505701210.803008,
            "uid":"ClM3Um3n5pZjcZZ843",
            "sourceipaddress":"73.72.209.187",
            "sourceport":61558,
            "destinationipaddress":"63.245.213.32",
            "destinationport":443,
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
            "dropped":'false',
            'category': 'bro',
            'type': 'notice'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'note' in result['details']
        assert 'msg' in result['details']
        assert 'sub' in result['details']
        assert result['summary'] == "SSL::Certificate_Expires_Soon Certificate CN=support.mozilla.org,O=Mozilla Foundation,L=Mountain View,ST=California,C=US,postalCode=94041,street=650 Castro St Ste 300,serialNumber=C2543436,1.3.6.1.4.1.311.60.2.1.2=#130A43616C69666F726E6961,1.3.6.1.4.1.311.60.2.1.3=#13025553,businessCategory=Private Organization is going to expire at 2017-10-06-12:00:00.000000000 "

    def test_x509_log(self):
        event = {
            "ts":1505703595.73864,
            "id":"FNe2XU16VWFNvpk9F2",
            "certificateversion":3,
            "certificateserial":"34B52BD83D80C284892AC63850038833",
            "certificatesubject":"CN=ssl.wsj.com,OU=Dow Jones and Company,O=Dow Jones and Company,L=Princeton,ST=New Jersey,C=US",
            "certificateissuer":"CN=GeoTrust SSL CA - G3,O=GeoTrust Inc.,C=US",
            "certificatenot_valid_before":1498608000.0,
            "certificatenot_valid_after":1527379199.0,
            "certificatekey_alg":"rsaEncryption",
            "certificatesig_alg":"sha256WithRSAEncryption",
            "certificatekey_type":"rsa",
            "certificatekey_length":2048,
            "certificate.exponent":"65537",
            "san.dns":["m-secure.wsj.net","kr.wsj.com","newsplus.stg.wsj.com","services.dowjones.com","si2.wsj.net","djlogin.stg.dowjones.com","si3.wsj.net","fonts.wsj.net","global.stg.factiva.com","graphics.wsj.com","www.wsj.com","s1.wsj.net","global.factiva.com","cdn.store.wsj.net","m.wsj.net","api.barrons.com","s1.marketwatch.com","city.wsj.com","portfolio.wsj.com","m.barrons.com","s3.marketwatch.com","sts3.wsj.net","s3.wsj.net","rwidget.wsj.net","ss.wsj.net","djlogin.dowjones.com","admin.stream.marketwatch.com","vir.www.wsj.com","cdn.smpdev.wsj.net","si1.wsj.net","art-secure.wsj.net","sc.wsj.net","indo.wsj.com","m.wsj.com","blogs.barrons.com","graphicsweb.wsj.com","widgets.dowjones.com","sj.wsj.net","blogs.marketwatch.com","s4.marketwatch.com","api-staging.wsj.net","blogs.wsj.com","api.wsj.net","newsplus.wsj.com","s2.wsj.net","salesforce.dowjones.com","v-secure.wsj.net","signin.wsj.com","salesforce.stg.dowjones.com","symphony.dowjones.com","admin.stream.wsj.com","suggest.stg.dowjones.com","www.stg.wsj.com","api.beta.dowjones.com","podcast.mktw.net","si4.wsj.net","help.wsj.com","api-staging.barrons.com","s4.wsj.net","ore.www.wsj.com","s2.marketwatch.com","cbuy.wsj.com","assets.efinancialnews.com","video-api.wsj.net","video-api-secure.wsj.com","portfolio.marketwatch.com","dr.marketwatch.com","onlinedr.wsj.com","api.stg.dowjones.com","sf.wsj.net","portfolio.barrons.com","signin.stg.wsj.com","video-api.wsj.com","symphony.stg.dowjones.com","art.wsj.net","widgets.stg.dowjones.com","api-secure.wsj.net","suggest.dowjones.com","sg.wsj.net","api-staging-secure.wsj.net","guides.wsj.com","m.jp.wsj.com","api.dowjones.com","video-api-secure.stg.wsj.com","s.wsj.net","api-staging.wsj.com","np3.stg.wsj.com","sfonts.wsj.net","www.ssl.wsj.com","api.wsj.com","s.marketwatch.com","realtime.wsj.com","newsletters.barrons.com","si.wsj.net","projects.wsj.com","m.cn.wsj.com","wn.wsj.com","ssl.wsj.com"],
            "certificate.basic_constraintsca":'false',
            'category': 'bro',
            'type': 'x509'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'certificateserial' in result['details']
        assert result['summary'] == 'Certificate seen serial 34B52BD83D80C284892AC63850038833'

    def test_x509_log2(self):
        event = {
            "ts":1505703595.73864,
            "id":"FNe2XU16VWFNvpk9F2",
            "certificate.version":3,
            "certificatesubject":"CN=ssl.wsj.com,OU=Dow Jones and Company,O=Dow Jones and Company,L=Princeton,ST=New Jersey,C=US",
            "certificateissuer":"CN=GeoTrust SSL CA - G3,O=GeoTrust Inc.,C=US",
            "certificatenot_valid_before":1498608000.0,
            "certificatenot_valid_after":1527379199.0,
            "certificatekey_alg":"rsaEncryption",
            "certificatesig_alg":"sha256WithRSAEncryption",
            "certificatekey_type":"rsa",
            "certificatekey_length":2048,
            "certificate.exponent":"65537",
            "san.dns":["m-secure.wsj.net","kr.wsj.com","newsplus.stg.wsj.com","services.dowjones.com","si2.wsj.net","djlogin.stg.dowjones.com","si3.wsj.net","fonts.wsj.net","global.stg.factiva.com","graphics.wsj.com","www.wsj.com","s1.wsj.net","global.factiva.com","cdn.store.wsj.net","m.wsj.net","api.barrons.com","s1.marketwatch.com","city.wsj.com","portfolio.wsj.com","m.barrons.com","s3.marketwatch.com","sts3.wsj.net","s3.wsj.net","rwidget.wsj.net","ss.wsj.net","djlogin.dowjones.com","admin.stream.marketwatch.com","vir.www.wsj.com","cdn.smpdev.wsj.net","si1.wsj.net","art-secure.wsj.net","sc.wsj.net","indo.wsj.com","m.wsj.com","blogs.barrons.com","graphicsweb.wsj.com","widgets.dowjones.com","sj.wsj.net","blogs.marketwatch.com","s4.marketwatch.com","api-staging.wsj.net","blogs.wsj.com","api.wsj.net","newsplus.wsj.com","s2.wsj.net","salesforce.dowjones.com","v-secure.wsj.net","signin.wsj.com","salesforce.stg.dowjones.com","symphony.dowjones.com","admin.stream.wsj.com","suggest.stg.dowjones.com","www.stg.wsj.com","api.beta.dowjones.com","podcast.mktw.net","si4.wsj.net","help.wsj.com","api-staging.barrons.com","s4.wsj.net","ore.www.wsj.com","s2.marketwatch.com","cbuy.wsj.com","assets.efinancialnews.com","video-api.wsj.net","video-api-secure.wsj.com","portfolio.marketwatch.com","dr.marketwatch.com","onlinedr.wsj.com","api.stg.dowjones.com","sf.wsj.net","portfolio.barrons.com","signin.stg.wsj.com","video-api.wsj.com","symphony.stg.dowjones.com","art.wsj.net","widgets.stg.dowjones.com","api-secure.wsj.net","suggest.dowjones.com","sg.wsj.net","api-staging-secure.wsj.net","guides.wsj.com","m.jp.wsj.com","api.dowjones.com","video-api-secure.stg.wsj.com","s.wsj.net","api-staging.wsj.com","np3.stg.wsj.com","sfonts.wsj.net","www.ssl.wsj.com","api.wsj.com","s.marketwatch.com","realtime.wsj.com","newsletters.barrons.com","si.wsj.net","projects.wsj.com","m.cn.wsj.com","wn.wsj.com","ssl.wsj.com"],
            "certificate.basic_constraintsca":'false',
            'category': 'bro',
            'type': 'x509'
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert toUTC(event['ts']).isoformat() == result['utctimestamp']
        assert toUTC(event['ts']).isoformat() == result['timestamp']
        assert sorted(result['details'].keys()) == sorted(event.keys())
        assert 'certificateserial' in result['details']
        assert result['summary'] == 'Certificate seen serial 0'
