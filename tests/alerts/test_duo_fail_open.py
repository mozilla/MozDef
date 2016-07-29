import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../alerts"))

from parent_test_alert import ParentTestAlert

from duo_fail_open import AlertDuoFailOpen

# Taken from the specific alert task
# todo make this dynamic
THRESHOLD_NUMBER = 1
SAMPLESLIMIT_NUMBER = 10

class ParentDuoFailOpenTest(ParentTestAlert):
    def alert_class(self):
        return AlertDuoFailOpen

    def generate_default_event(self):
        event = super(ParentDuoFailOpenTest, self).generate_default_event()
        event['summary'] = "Failsafe Duo login summary"
        return event


class TestDuoFailOpenWithSamplesLimit(ParentDuoFailOpenTest):
    expected_to_throw = True

    def events(self):
        events = []
        for a in range(SAMPLESLIMIT_NUMBER):
            event = self.generate_default_event()
            events.append(event)

        return events

    def alert(self):
      return {u'_id': u'uSV1qU-WSnegXkEymgBYqg',
 u'_index': u'alerts',
 u'_source': {u'category': u'bypass',
              u'events': [{u'documentid': u'MbZ1ZUqRQvSjg_9atwQNBA',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'212.34.24.34'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179260+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179260+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179260+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'mvMoppSBTKCGeAyL6HKLpg',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'153.107.187.112'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179297+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179297+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179297+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'HmZl9dKuQgK-XsRu2UKjXQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'166.148.232.93'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179332+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179332+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179332+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'zn4av0UeSzy22U5XaXfx4w',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'206.97.177.242'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179376+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179376+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179376+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'1r3xLKbHR9CT4h7PTi0_Tg',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'97.220.247.47'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179274+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179274+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179274+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'9Ts55xB2RcmIStLYC-ZLuQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'92.45.88.152'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179365+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179365+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179365+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'KmRDQgRYSZun-5-BQh2mog',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'145.110.64.5'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179398+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179398+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179398+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'_rT8ZSwbSDi6CndBeLSH8g',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'78.89.219.153'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179343+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179343+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179343+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'-r5doVKoQGy2iNS3Jsa4Tg',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'255.105.26.34'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179354+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179354+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179354+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'nCi46qkBQi2MZZbbc3PKcQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'122.154.69.24'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179387+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179387+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179387+00:00'},
                           u'documenttype': u'event'}],
              u'severity': u'WARNING',
              u'summary': u'DuoSecurity contact failed, fail open triggered on testhostname',
              u'tags': [u'openvpn', u'duosecurity'],
              u'utctimestamp': u'2016-07-20T14:23:20.240874+00:00'},
 u'_type': u'alert',
 u'_version': 1,
 u'found': True}


class TestDuoFailOpenPositiveWithThreshold(ParentDuoFailOpenTest):
    expected_to_throw = True

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            events.append(event)

        return events

    def alert(self):
      return {u'_id': u'uSV1qU-WSnegXkEymgBYqg',
 u'_index': u'alerts',
 u'_source': {u'category': u'bypass',
              u'events': [{u'documentid': u'nCi46qkBQi2MZZbbc3PKcQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'122.154.69.24'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'receivedtimestamp': u'2016-07-20T14:23:18.179387+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'Failsafe Duo login summary',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:23:18.179387+00:00',
                                               u'utctimestamp': u'2016-07-20T14:23:18.179387+00:00'},
                           u'documenttype': u'event'}],
              u'severity': u'WARNING',
              u'summary': u'DuoSecurity contact failed, fail open triggered on testhostname',
              u'tags': [u'openvpn', u'duosecurity'],
              u'utctimestamp': u'2016-07-20T14:23:20.240874+00:00'},
 u'_type': u'alert',
 u'_version': 1,
 u'found': True}


class TestDuoFailOpenMissingHostname(ParentDuoFailOpenTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            event['details'].pop('hostname')
            events.append(event)

        return events


class TestDuoFailOpenIncorrectSummary(ParentDuoFailOpenTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            event['summary'] = "Example test summary"
            events.append(event)

        return events


class TestDuoFailOpenOldTimestampDoesntExist(ParentDuoFailOpenTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            custom_timestamp = self.helper.subtract_from_timestamp(self.helper.current_timestamp(), dict(minutes=16))
            event['receivedtimestamp'] = custom_timestamp
            event['utctimestamp'] = custom_timestamp
            event['timestamp'] = custom_timestamp

            events.append(event)

        return events


class TestDuoFailOpenNotEnoughEvents(ParentDuoFailOpenTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER-1):
            event = self.generate_default_event()
            events.append(event)

        return events