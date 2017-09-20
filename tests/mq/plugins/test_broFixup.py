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
