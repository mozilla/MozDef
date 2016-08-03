import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../alerts"))

from parent_test_alert import ParentTestAlert

from bro_notice import AlertBroNotice


class ParentAlertBroNotice(ParentTestAlert):
    def alert_class(self):
        return AlertBroNotice

    def generate_default_event(self):
        event = super(ParentAlertBroNotice, self).generate_default_event()
        event['category'] = 'bronotice'
        event['details']['note'] = "Example note"

        return event


class TestBroNoticeWithGoodEvent(ParentAlertBroNotice):
    expected_to_throw = True

    def events(self):
        event = self.generate_default_event()
        return [event]

    def alert(self):
        return {u'_id': u'DG3ahkCeQ_aH3z8oVGEspQ',
                u'_index': u'alerts',
                u'_source': {u'category': u'bro',
                             u'events': [{u'documentid': u'QcaYwBq9RCK4c-NzXrRJ4w',
                                          u'documentindex': u'events-20160803',
                                          u'documentsource': {u'category': u'bronotice',
                                                              u'details': {u'hostname': u'testhostname',
                                                                           u'note': u'Example note',
                                                                           u'sourceipaddress': u'130.116.245.7'},
                                                              u'hostname': u'nsm',
                                                              u'processid': u'1337',
                                                              u'processname': u'syslog',
                                                              u'receivedtimestamp': u'2016-08-03T15:26:04.021946+00:00',
                                                              u'severity': u'NOTICE',
                                                              u'source': u'nsm_src',
                                                              u'summary': u'Example summary',
                                                              u'tags': [u'tag1', u'tag2'],
                                                              u'timestamp': u'2016-08-03T15:26:04.021946+00:00',
                                                              u'utctimestamp': u'2016-08-03T15:26:04.021946+00:00'},
                                          u'documenttype': u'event'}],
                             u'severity': u'NOTICE',
                             u'summary': u'Example summary',
                             u'tags': [u'bro'],
                             u'utctimestamp': u'2016-08-03T15:26:06.071718+00:00'},
                u'_type': u'alert',
                u'_version': 1,
                u'found': True}


class TestBroNoticeWithBadTimestamp(ParentAlertBroNotice):
    expected_to_throw = False

    def events(self):
        event = self.generate_default_event()
        custom_timestamp = self.helper.subtract_from_timestamp(self.helper.current_timestamp(), dict(minutes=31))
        event['receivedtimestamp'] = custom_timestamp
        event['utctimestamp'] = custom_timestamp
        return [event]


class TestBroNoticeWithBadPacketFilterNote(ParentAlertBroNotice):
    expected_to_throw = False

    def events(self):
        event = self.generate_default_event()
        event['details']['note'] = "PacketFilter::Dropped_Packets"
        return [event]


class TestBroNoticeWithBadCaptureLossNote(ParentAlertBroNotice):
    expected_to_throw = False

    def events(self):
        event = self.generate_default_event()
        event['details']['note'] = "CaptureLoss::Too_Much_Loss"
        return [event]


class TestBroNoticeWithBadWeirdActivityNote(ParentAlertBroNotice):
    expected_to_throw = False

    def events(self):
        event = self.generate_default_event()
        event['details']['note'] = "Weird::Activity"
        return [event]
