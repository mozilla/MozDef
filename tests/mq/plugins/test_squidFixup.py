import mock

from mozdef_util.utilities.toUTC import toUTC

from mq.plugins.squidFixup import message


class TestSquidFixup(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {
            'index': 'events'
        }

    # Should never match and be modified by the plugin
    def test_notsquid_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'key1': 'squid'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_notsquid_log2(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'squid': 'value1'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_squid_notype_log(self):
        metadata = {
            'index': 'events'
        }
        event = {
            'category': 'proxy'
        }

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def test_squid_wrongtype_log(self):
        event = {
            'category': 'proxy',
            'SOURCE': 'nosuchtype',
            'customendpoint': ' '
        }
        event['MESSAGE'] = "1547953357.127 1690 192.168.97.135 58306 185.53.177.31 443 TCP_TUNNEL - 86 4700 CONNECT test.com:443 - test.com -"

        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)

    @mock.patch('mq.plugins.squidFixup.node')
    def test_mozdefhostname_mock_string(self, mock_path):
        mock_path.return_value = 'samplehostname'
        event = {
            'category': 'proxy',
            'SOURCE': 'something',
            'customendpoint': ' '
        }
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result['mozdefhostname'] == 'samplehostname'

    @mock.patch('mq.plugins.squidFixup.node')
    def test_mozdefhostname_mock_exception(self, mock_path):
        mock_path.side_effect = ValueError
        event = {
            'category': 'proxy',
            'SOURCE': 'something',
            'customendpoint': ' '
        }
        plugin = message()
        result, metadata = plugin.onMessage(event, self.metadata)
        assert result['mozdefhostname'] == 'failed to fetch mozdefhostname'

    def verify_metadata(self, metadata):
        assert metadata['index'] == 'events'

    def test_defaults(self):
        event = {
            'category': 'proxy',
            'source': 'something',
            'customendpoint': ' '
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['category'] == 'proxy'
        assert result['source'] == 'something'

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
            "summary": "Connection from 10.22.74.208 port 9071 on 10.22.74.45 squid proxy port 22\n",
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
                "originaluser": "squid",
                "ppid": "10552",
                "cwd": "/",
                "parentprocess": "proxy",
                "euid": "398",
                "path": "/bin/sh",
                "rdev": "00:00",
                "dev": "08:03",
                "egid": "398",
                "command": "sh -c sudo /usr/lib64/nagios/plugins/custom/check_auditd.sh",
                "mode": "0100755",
                "user": "squid"
            }
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result['category'] == 'execve'
        assert 'eventsource' not in result
        assert result == event

    def verify_defaults(self, result):
        assert result['category'] == 'proxy'
        assert result['customendpoint'] == ' '
        assert result['eventsource'] == 'squid'
        assert toUTC(result['receivedtimestamp']).isoformat() == result['receivedtimestamp']
        assert result['severity'] == 'INFO'

    def test_access_http_allow_custom_port_log(self):
        event = {
            "tags":"squid",
            "source":"access",
            "customendpoint":" ",
            "category":"proxy",
            "TAGS":".source.access_src",
            "SOURCEIP":"127.0.0.1",
            "SOURCE":"access_src",
            "PRIORITY":"notice",
            "MESSAGE":"1548043032.187 524 192.168.97.135 58322 185.53.177.31 444 TCP_MISS 200 152 339 GET http://test.com:444/ http test.com text/html",
            "HOST_FROM":"localhost",
            "HOST":"localhost",
            "FILE_NAME":"/etc/syslog-ng/access.log.local",
            "FACILITY":"user",
            "DATE":"Jan 21 03:57:42"
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['sourceipaddress'] == '192.168.97.135'
        assert result['details']['destinationipaddress'] == '185.53.177.31'
        assert result['details']['sourceport'] == 58322
        assert result['details']['destinationport'] == 444
        assert result['details']['duration'] == 0.524
        assert result['details']['requestsize'] == 152
        assert result['details']['responsesize'] == 339
        assert result['details']['proxyaction'] == 'TCP_MISS'
        assert result['details']['status'] == '200'
        assert result['details']['method'] == 'GET'
        assert result['details']['destination'] == 'http://test.com:444/'
        assert result['details']['proto'] == 'http'
        assert result['details']['host'] == 'test.com'
        assert result['details']['mimetype'] == 'text/html'
        assert result['summary'] == '1548043032.187 524 192.168.97.135 58322 185.53.177.31 444 TCP_MISS 200 152 339 GET http://test.com:444/ http test.com text/html'
        assert 'SOURCEIP' not in result
        assert 'PRIORITY' not in result
        assert 'MESSAGE' not in result
        assert 'HOST_FROM' not in result
        assert 'HOST' not in result
        assert 'FILE_NAME' not in result
        assert 'FACILITY' not in result
        assert 'DATE' not in result
        assert 'TAGS' not in result

    def test_access_http_allow_without_uri_log(self):
        event = {
            "tags":"squid",
            "source":"access",
            "customendpoint":" ",
            "category":"proxy",
            "TAGS":".source.access_src",
            "SOURCEIP":"127.0.0.1",
            "SOURCE":"access_src",
            "PRIORITY":"notice",
            "MESSAGE":"1548043032.187 412 192.168.97.135 58322 185.53.177.31 80 TCP_MISS 403 158 453 GET http://test.com/ http test.com text/html",
            "HOST_FROM":"localhost",
            "HOST":"localhost",
            "FILE_NAME":"/etc/syslog-ng/access.log.local",
            "FACILITY":"user",
            "DATE":"Jan 21 03:57:42"
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['sourceipaddress'] == '192.168.97.135'
        assert result['details']['destinationipaddress'] == '185.53.177.31'
        assert result['details']['sourceport'] == 58322
        assert result['details']['destinationport'] == 80
        assert result['details']['duration'] == 0.412
        assert result['details']['requestsize'] == 158
        assert result['details']['responsesize'] == 453
        assert result['details']['proxyaction'] == 'TCP_MISS'
        assert result['details']['status'] == '403'
        assert result['details']['method'] == 'GET'
        assert result['details']['destination'] == 'http://test.com/'
        assert result['details']['proto'] == 'http'
        assert result['details']['host'] == 'test.com'
        assert result['details']['mimetype'] == 'text/html'
        assert result['tags'] == 'squid'
        assert result['summary'] == '1548043032.187 412 192.168.97.135 58322 185.53.177.31 80 TCP_MISS 403 158 453 GET http://test.com/ http test.com text/html'
        assert 'SOURCEIP' not in result
        assert 'PRIORITY' not in result
        assert 'MESSAGE' not in result
        assert 'HOST_FROM' not in result
        assert 'HOST' not in result
        assert 'FILE_NAME' not in result
        assert 'FACILITY' not in result
        assert 'DATE' not in result
        assert 'TAGS' not in result

    def test_access_http_allow_with_uri_log(self):
        event = {
            "tags":"squid",
            "source":"access",
            "customendpoint":" ",
            "category":"proxy",
            "TAGS":".source.access_src",
            "SOURCEIP":"127.0.0.1",
            "SOURCE":"access_src",
            "PRIORITY":"notice",
            "MESSAGE":"1548043032.187 412 192.168.97.135 58322 185.53.177.31 80 TCP_MISS 403 158 453 GET http://test.com/3something.bin http test.com text/html",
            "HOST_FROM":"localhost",
            "HOST":"localhost",
            "FILE_NAME":"/etc/syslog-ng/access.log.local",
            "FACILITY":"user",
            "DATE":"Jan 21 03:57:42"
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['sourceipaddress'] == '192.168.97.135'
        assert result['details']['destinationipaddress'] == '185.53.177.31'
        assert result['details']['sourceport'] == 58322
        assert result['details']['destinationport'] == 80
        assert result['details']['duration'] == 0.412
        assert result['details']['requestsize'] == 158
        assert result['details']['responsesize'] == 453
        assert result['details']['proxyaction'] == 'TCP_MISS'
        assert result['details']['status'] == '403'
        assert result['details']['method'] == 'GET'
        assert result['details']['destination'] == 'http://test.com/3something.bin'
        assert result['details']['proto'] == 'http'
        assert result['details']['host'] == 'test.com'
        assert result['details']['mimetype'] == 'text/html'
        assert result['tags'] == 'squid'
        assert result['summary'] == '1548043032.187 412 192.168.97.135 58322 185.53.177.31 80 TCP_MISS 403 158 453 GET http://test.com/3something.bin http test.com text/html'
        assert 'SOURCEIP' not in result
        assert 'PRIORITY' not in result
        assert 'MESSAGE' not in result
        assert 'HOST_FROM' not in result
        assert 'HOST' not in result
        assert 'FILE_NAME' not in result
        assert 'FACILITY' not in result
        assert 'DATE' not in result
        assert 'TAGS' not in result

    def test_access_http_allow_with_uri_custom_port_log(self):
        event = {
            "tags":"squid",
            "source":"access",
            "customendpoint":" ",
            "category":"proxy",
            "TAGS":".source.access_src",
            "SOURCEIP":"127.0.0.1",
            "SOURCE":"access_src",
            "PRIORITY":"notice",
            "MESSAGE":"1548043032.187 412 192.168.97.135 58322 185.53.177.31 444 TCP_MISS 403 158 453 GET http://test.com:444/3something.bin http test.com text/html",
            "HOST_FROM":"localhost",
            "HOST":"localhost",
            "FILE_NAME":"/etc/syslog-ng/access.log.local",
            "FACILITY":"user",
            "DATE":"Jan 21 03:57:42"
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['sourceipaddress'] == '192.168.97.135'
        assert result['details']['destinationipaddress'] == '185.53.177.31'
        assert result['details']['sourceport'] == 58322
        assert result['details']['destinationport'] == 444
        assert result['details']['duration'] == 0.412
        assert result['details']['requestsize'] == 158
        assert result['details']['responsesize'] == 453
        assert result['details']['proxyaction'] == 'TCP_MISS'
        assert result['details']['status'] == '403'
        assert result['details']['method'] == 'GET'
        assert result['details']['destination'] == 'http://test.com:444/3something.bin'
        assert result['details']['proto'] == 'http'
        assert result['details']['host'] == 'test.com'
        assert result['details']['mimetype'] == 'text/html'
        assert result['tags'] == 'squid'
        assert result['summary'] == '1548043032.187 412 192.168.97.135 58322 185.53.177.31 444 TCP_MISS 403 158 453 GET http://test.com:444/3something.bin http test.com text/html'
        assert 'SOURCEIP' not in result
        assert 'PRIORITY' not in result
        assert 'MESSAGE' not in result
        assert 'HOST_FROM' not in result
        assert 'HOST' not in result
        assert 'FILE_NAME' not in result
        assert 'FACILITY' not in result
        assert 'DATE' not in result
        assert 'TAGS' not in result

    def test_access_ssl_allow(self):
        event = {
            "tags":"squid",
            "source":"access",
            "customendpoint":" ",
            "category":"proxy",
            "TAGS":".source.access_src",
            "SOURCEIP":"127.0.0.1",
            "SOURCE":"access_src",
            "PRIORITY":"notice",
            "MESSAGE":"1548043024.368 1082 192.168.97.135 58318 185.53.177.31 443 TCP_TUNNEL - 86 4700 CONNECT test.com:443 - test.com -",
            "HOST_FROM":"localhost",
            "HOST":"localhost",
            "FILE_NAME":"/etc/syslog-ng/access.log.local",
            "FACILITY":"user",
            "DATE":"Jan 21 03:57:42"
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['sourceipaddress'] == '192.168.97.135'
        assert result['details']['destinationipaddress'] == '185.53.177.31'
        assert result['details']['sourceport'] == 58318
        assert result['details']['destinationport'] == 443
        assert result['details']['duration'] == 1.082
        assert result['details']['requestsize'] == 86
        assert result['details']['responsesize'] == 4700
        assert result['details']['proxyaction'] == 'TCP_TUNNEL'
        assert result['details']['status'] == '-'
        assert result['details']['method'] == 'CONNECT'
        assert result['details']['destination'] == 'test.com:443'
        assert result['details']['proto'] == 'ssl'
        assert result['details']['host'] == 'test.com'
        assert result['details']['mimetype'] == '-'
        assert result['tags'] == 'squid'
        assert result['summary'] == '1548043024.368 1082 192.168.97.135 58318 185.53.177.31 443 TCP_TUNNEL - 86 4700 CONNECT test.com:443 - test.com -'
        assert 'SOURCEIP' not in result
        assert 'PRIORITY' not in result
        assert 'MESSAGE' not in result
        assert 'HOST_FROM' not in result
        assert 'HOST' not in result
        assert 'FILE_NAME' not in result
        assert 'FACILITY' not in result
        assert 'DATE' not in result
        assert 'TAGS' not in result

    def test_access_ssl_deny(self):
        event = {
            "tags":"squid",
            "source":"access",
            "customendpoint":" ",
            "category":"proxy",
            "TAGS":".source.access_src",
            "SOURCEIP":"127.0.0.1",
            "SOURCE":"access_src",
            "PRIORITY":"notice",
            "MESSAGE":"1548043048.377 0 192.168.97.135 58332 - - TCP_DENIED - 86 3892 CONNECT test.com:444 - - text/html",
            "HOST_FROM":"localhost",
            "HOST":"localhost",
            "FILE_NAME":"/etc/syslog-ng/access.log.local",
            "FACILITY":"user",
            "DATE":"Jan 21 03:57:42"
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['sourceipaddress'] == '192.168.97.135'
        assert result['details']['destinationipaddress'] == '0.0.0.0'
        assert result['details']['sourceport'] == 58332
        assert result['details']['destinationport'] == 444
        assert result['details']['duration'] == 0.0
        assert result['details']['requestsize'] == 86
        assert result['details']['responsesize'] == 3892
        assert result['details']['proxyaction'] == 'TCP_DENIED'
        assert result['details']['status'] == '-'
        assert result['details']['method'] == 'CONNECT'
        assert result['details']['destination'] == 'test.com:444'
        assert result['details']['proto'] == 'ssl'
        assert result['details']['host'] == 'test.com'
        assert result['details']['mimetype'] == 'text/html'
        assert result['tags'] == 'squid'
        assert result['summary'] == '1548043048.377 0 192.168.97.135 58332 - - TCP_DENIED - 86 3892 CONNECT test.com:444 - - text/html'
        assert 'SOURCEIP' not in result
        assert 'PRIORITY' not in result
        assert 'MESSAGE' not in result
        assert 'HOST_FROM' not in result
        assert 'HOST' not in result
        assert 'FILE_NAME' not in result
        assert 'FACILITY' not in result
        assert 'DATE' not in result
        assert 'TAGS' not in result

    def test_access_http_deny_log(self):
        event = {
            "tags":"squid",
            "source":"access",
            "customendpoint":" ",
            "category":"proxy",
            "TAGS":".source.access_src",
            "SOURCEIP":"127.0.0.1",
            "SOURCE":"access_src",
            "PRIORITY":"notice",
            "MESSAGE":"1548043040.983 0 192.168.97.135 58328 - - TCP_DENIED - 152 3992 GET http://test.com:444/ http - text/html",
            "HOST_FROM":"localhost",
            "HOST":"localhost",
            "FILE_NAME":"/etc/syslog-ng/access.log.local",
            "FACILITY":"user",
            "DATE":"Jan 21 03:57:42"
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['sourceipaddress'] == '192.168.97.135'
        assert result['details']['destinationipaddress'] == '0.0.0.0'
        assert result['details']['sourceport'] == 58328
        assert result['details']['destinationport'] == 444
        assert result['details']['duration'] == 0.0
        assert result['details']['requestsize'] == 152
        assert result['details']['responsesize'] == 3992
        assert result['details']['proxyaction'] == 'TCP_DENIED'
        assert result['details']['status'] == '-'
        assert result['details']['method'] == 'GET'
        assert result['details']['destination'] == 'http://test.com:444/'
        assert result['details']['proto'] == 'http'
        assert result['details']['host'] == 'test.com'
        assert result['details']['mimetype'] == 'text/html'
        assert result['tags'] == 'squid'
        assert result['summary'] == '1548043040.983 0 192.168.97.135 58328 - - TCP_DENIED - 152 3992 GET http://test.com:444/ http - text/html'
        assert 'TAGS' not in result
        assert 'SOURCEIP' not in result
        assert 'PRIORITY' not in result
        assert 'MESSAGE' not in result
        assert 'HOST_FROM' not in result
        assert 'HOST' not in result
        assert 'FILE_NAME' not in result
        assert 'FACILITY' not in result
        assert 'DATE' not in result

    def test_access_http_deny_with_uri_log(self):
        event = {
            "tags":"squid",
            "source":"access",
            "customendpoint":" ",
            "category":"proxy",
            "TAGS":".source.access_src",
            "SOURCEIP":"127.0.0.1",
            "SOURCE":"access_src",
            "PRIORITY":"notice",
            "MESSAGE":"1548043040.983 0 192.168.97.135 58328 - - TCP_DENIED - 152 3992 GET http://test.com:444/ http - text/html",
            "HOST_FROM":"localhost",
            "HOST":"localhost",
            "FILE_NAME":"/etc/syslog-ng/access.log.local",
            "FACILITY":"user",
            "DATE":"Jan 21 03:57:42"
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        assert result['details']['sourceipaddress'] == '192.168.97.135'
        assert result['details']['destinationipaddress'] == '0.0.0.0'
        assert result['details']['sourceport'] == 58328
        assert result['details']['destinationport'] == 444
        assert result['details']['duration'] == 0.0
        assert result['details']['requestsize'] == 152
        assert result['details']['responsesize'] == 3992
        assert result['details']['proxyaction'] == 'TCP_DENIED'
        assert result['details']['status'] == '-'
        assert result['details']['method'] == 'GET'
        assert result['details']['destination'] == 'http://test.com:444/'
        assert result['details']['proto'] == 'http'
        assert result['details']['host'] == 'test.com'
        assert result['details']['mimetype'] == 'text/html'
        assert result['tags'] == 'squid'
        assert result['summary'] == '1548043040.983 0 192.168.97.135 58328 - - TCP_DENIED - 152 3992 GET http://test.com:444/ http - text/html'
        assert 'TAGS' not in result
        assert 'SOURCEIP' not in result
        assert 'PRIORITY' not in result
        assert 'MESSAGE' not in result
        assert 'HOST_FROM' not in result
        assert 'HOST' not in result
        assert 'FILE_NAME' not in result
        assert 'FACILITY' not in result
        assert 'DATE' not in result
