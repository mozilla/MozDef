import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../alerts"))

from alert_test_suite import AlertTestSuite
from bruteforce_ssh_pyes import AlertBruteforceSshES

# Taken from the specific alert task
# todo make this dynamic
THRESHOLD_NUMBER = 10

class ParentBruteforceSshESTest(AlertTestSuite):
    def alert_class(self):
        return AlertBruteforceSshES

    def generate_default_event(self):
        event = super(ParentBruteforceSshESTest, self).generate_default_event()
        source_ip = "1.2.3.4"
        event['program'] = "sshd"
        event['summary'] = "login invalid ldap_count_entries failed by " + source_ip
        event['details']['sourceipaddress'] = source_ip
        return event

class TestBruteforceSshESPositive(ParentBruteforceSshESTest):
    expected_to_throw = True

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            events.append(event)

        return events

    def alert(self):
        return {u'_id': u'xcMui9Y0TUyTJB-sRdaIcA',
 u'_index': u'alerts',
 u'_source': {u'category': u'bruteforce',
              u'events': [{u'documentid': u'FXL2a5VXTcmZiKhA1bK-1g',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.642969+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.642969+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.642969+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'rixAqj4dTBy03WQutnpRAQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.643002+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.643002+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.643002+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'PSCJic6JTYGpZhhIonnVaw',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.642917+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.642917+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.642917+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'aYa8fJASQ6CJbAmrepCXbQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.643038+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.643038+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.643038+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'i7zd5mbuTSyHOx_5RnKHOw',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.642901+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.642901+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.642901+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'JxJW9v8xS2Sfu7j6x8DmWQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.642931+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.642931+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.642931+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'br8fhQXoRz6U8UsNe-zptA',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.642989+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.642989+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.642989+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'5FTjE5A8SO-0Sa4OKiyxTQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.642855+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.642855+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.642855+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'9b9KUZ4mTcmffeAA2ooNxQ',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.642944+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.642944+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.642944+00:00'},
                           u'documenttype': u'event'},
                          {u'documentid': u'M4AmhNQaQJWmbHubqpnFHw',
                           u'documentindex': u'events',
                           u'documentsource': {u'category': u'bronotice',
                                               u'details': {u'sourceipaddress': u'1.2.3.4'},
                                               u'hostname': u'nsm',
                                               u'processid': u'1337',
                                               u'processname': u'syslog',
                                               u'program': u'sshd',
                                               u'receivedtimestamp': u'2016-07-20T14:22:43.642957+00:00',
                                               u'severity': u'NOTICE',
                                               u'source': u'nsm_src',
                                               u'summary': u'login invalid ldap_count_entries failed by 1.2.3.4',
                                               u'tags': [u'tag1', u'tag2'],
                                               u'timestamp': u'2016-07-20T14:22:43.642957+00:00',
                                               u'utctimestamp': u'2016-07-20T14:22:43.642957+00:00'},
                           u'documenttype': u'event'}],
              u'severity': u'NOTICE',
              u'summary': u'10 ssh bruteforce attempts by 1.2.3.4 testhostname (10 hits)',
              u'tags': [u'ssh'],
              u'utctimestamp': u'2016-07-20T14:22:45.676057+00:00'},
 u'_type': u'alert',
 u'_version': 1,
 u'found': True}


class TestBruteforceSshESNotEnoughEvents(ParentBruteforceSshESTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER-1):
            event = self.generate_default_event()
            events.append(event)

        return events

class TestBruteforceSshESWithMustNotEvent(ParentBruteforceSshESTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            source_ip = "10.22.75.203"
            event['summary'] = "login invalid ldap_count_entries failed by " + source_ip
            event['details']['sourceipaddress'] = source_ip
            events.append(event)

        return events

class TestBruteforceSshESWithMustNotEvent144(ParentBruteforceSshESTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            source_ip = "10.8.75.144"
            event['summary'] = "login invalid ldap_count_entries failed by " + source_ip
            event['details']['sourceipaddress'] = source_ip
            events.append(event)

        return events

class TestBruteforceSshESOldTimestampDoesntExist(ParentBruteforceSshESTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            custom_timestamp = self.subtract_from_timestamp(self.current_timestamp(), dict(minutes=3))
            event['receivedtimestamp'] = custom_timestamp
            event['utctimestamp'] = custom_timestamp
            event['timestamp'] = custom_timestamp
            events.append(event)

        return events


class TestBruteforceSshESWithWrongType(ParentBruteforceSshESTest):
    expected_to_throw = False

    def event_type(self):
      return "bro"

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            events.append(event)

        return events


class TestBruteforceSshESWithWrongProgram(ParentBruteforceSshESTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            event['program'] = "syslog"
            events.append(event)

        return events


class TestBruteforceSshESWithWrongSummary(ParentBruteforceSshESTest):
    expected_to_throw = False

    def events(self):
        events = []
        for a in range(THRESHOLD_NUMBER):
            event = self.generate_default_event()
            event['summary'] = "Test summary"
            events.append(event)

        return events
