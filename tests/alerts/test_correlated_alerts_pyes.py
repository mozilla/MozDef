import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../alerts"))

from alert_test_suite import AlertTestSuite
from correlated_alerts_pyes import AlertCorrelatedIntelNotice

class ParentCorrelatedIntelNoticeTest(AlertTestSuite):
    def alert_class(self):
        return AlertCorrelatedIntelNotice

    def event_type(self):
        return 'bro'

    def generate_default_event(self):
        event = super(ParentCorrelatedIntelNoticeTest, self).generate_default_event()
        source_ip = "1.2.3.4"
        event['summary'] = "CrowdStrike::Correlated_Alerts Host " + source_ip + " caused an alert to throw"
        event['details']['sourceipaddress'] = source_ip
        event['eventsource'] = "nsm"
        event['details']['note'] = "CrowdStrike::Correlated_Alerts example alert"
        return event


class TestCorrelatedIntelNoticePositive(ParentCorrelatedIntelNoticeTest):
    expected_to_throw = True

    def events(self):
        event = self.generate_default_event()
        return [event]

    def alert(self):
        return {u'_id': u'0AI3emwOS9-77Eh97iMVMg',
 u'_index': u'alerts',
 u'_source': {u'category': u'correlatedalerts',
              u'events': [{u'documentid': u'VWQWL4moR3idcP7m5KnL3Q',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'note': u'CrowdStrike::Correlated_Alerts example alert',
                                                            u'sourceipaddress': u'1.2.3.4'},
                                               u'eventsource': u'nsm',
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:22:17.061925+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:17.061925+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:17.061925+00:00'},
                           u'documenttype': u'bro'}],
              u'severity': u'NOTICE',
              u'summary': u'nsm CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw',
              u'tags': [u'nsm,bro,correlated'],
              u'url': u'https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures',
              u'utctimestamp': u'2016-07-20T14:22:19.120795+00:00'},
 u'_type': u'alert',
 u'_version': 1,
 u'found': True}


class TestCorrelatedIntelNoticeAsEventType(ParentCorrelatedIntelNoticeTest):
    expected_to_throw = False

    def event_type(self):
        return "event"

    def events(self):
        event = self.generate_default_event()
        return [event]


class TestCorrelatedIntelNoticeWithChangedEventSource(ParentCorrelatedIntelNoticeTest):
    expected_to_throw = False

    def events(self):
        event = self.generate_default_event()
        event['eventsource'] = "syslog"
        return [event]


class TestCorrelatedIntelNoticeWithChangedCategory(ParentCorrelatedIntelNoticeTest):
    expected_to_throw = False

    def events(self):
        event = self.generate_default_event()
        event['category'] = "brointel"
        return [event]


class TestCorrelatedIntelNoticeWithRemovedSourceIP(ParentCorrelatedIntelNoticeTest):
    expected_to_throw = False

    def events(self):
        event = self.generate_default_event()
        event['details'].pop("sourceipaddress")
        return [event]


class TestCorrelatedIntelNoticeWithUnmatchedNote(ParentCorrelatedIntelNoticeTest):
    expected_to_throw = False

    def events(self):
        event = self.generate_default_event()
        event['details']['note'] = 'ConnAnomaly::ConnLong'
        return [event]


class TestCorrelatedIntelNoticeOldTimestampDoesntExist(ParentCorrelatedIntelNoticeTest):
    expected_to_throw = False

    def events(self):
        default_event = self.generate_default_event()
        custom_timestamp = self.subtract_from_timestamp(self.current_timestamp(), dict(minutes=16))
        default_event['receivedtimestamp'] = custom_timestamp
        default_event['utctimestamp'] = custom_timestamp
        default_event['timestamp'] = custom_timestamp
        return [default_event]
