import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../alerts/lib"))

from unit_test_suite import UnitTestSuite


class ElasticsearchClientTest(UnitTestSuite):
    def setup(self):
        super(ElasticsearchClientTest, self).setup()


class TestWriteWithRead(ElasticsearchClientTest):
    def setup(self):
        super(TestWriteWithRead, self).setup()

        self.alert = {'category': 'correlatedalerts',
                 'events': [{'documentid': 'l-a3V5mbQl-C91RDzjpNig',
                             'documentindex': 'events-20160819',
                             'documentsource': {'category': 'bronotice',
                                                'details': {'hostname': 'testhostname',
                                                            'note': 'CrowdStrike::Correlated_Alerts example alert',
                                                            'sourceipaddress': '1.2.3.4'},
                                                'eventsource': 'nsm',
                                                'hostname': 'nsm',
                                                'processid': '1337',
                                                'processname': 'syslog',
                                                'receivedtimestamp': '2016-08-19T16:40:55.818595+00:00',
                                                'severity': 'NOTICE',
                                                'source': 'nsm_src',
                                                'summary': 'CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw',
                                                'tags': ['tag1', 'tag2'],
                                                'timestamp': '2016-08-19T16:40:55.818595+00:00',
                                                'utctimestamp': '2016-08-19T16:40:55.818595+00:00'},
                             'documenttype': 'bro'}],
                 'severity': 'NOTICE',
                 'summary': 'nsm CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw',
                 'tags': ['nsm,bro,correlated'],
                 'url': 'https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures',
                 'utctimestamp': '2016-08-19T16:40:57.851092+00:00'}
        self.saved_alert = self.es_client.save_alert(self.alert)
        self.es_client.flush('alerts')

    def test_saved_type(self):
        assert self.saved_alert['_type'] == 'alert'

    def test_saved_index(self):
        assert self.saved_alert['_index'] == 'alerts'

    def test_alert_source(self):
        self.fetched_alert = self.es_client.get_alert_by_id(self.saved_alert['_id'])
        assert self.fetched_alert['_source'] == self.alert

    def test_bad_id(self):
        assert self.es_client.get_alert_by_id("123") is None
