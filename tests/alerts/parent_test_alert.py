import sys
sys.path.append("../../alerts/")

from lib.config import LOGGING, ES

from alert_helper import TestHelper

class ParentTestAlert(object):

    def event_type(self):
        # todo normalize all bro events and alerts so the _type is still 'event'
        return 'event'

    def setup(self):
        self.helper = TestHelper(ES['servers'][0])

        self.helper.delete_index_if_exists("events", False)
        self.helper.delete_index_if_exists("events-previous", False)
        self.helper.delete_index_if_exists("alerts", False)

        self.helper.create_index("events")
        self.helper.create_index("events-previous")
        self.helper.create_index("alerts")

        for event in self.events():
            self.helper.event_to_es(event, "events", self.event_type())

    def teardown(self):
        self.helper.delete_index_if_exists("events", False)
        self.helper.delete_index_if_exists("events-previous", False)
        self.helper.delete_index_if_exists("alerts", False)

    def generate_default_event(self):
        current_timestamp = self.helper.current_timestamp()

        source_ip = self.helper.random_ip()

        event = {
          "category": "bronotice",
          "receivedtimestamp": current_timestamp,
          "utctimestamp": current_timestamp,
          "timestamp": current_timestamp,
          "hostname": "nsm",
          "processid": "1337",
          "processname": "syslog",
          "severity": "NOTICE",
          "source": "nsm_src",
          "summary": "Example summary",
          "tags": ['tag1', 'tag2'],
          "details": {
            "sourceipaddress": source_ip,
            "hostname": "testhostname"
          }
        }

        return event

    def test_alert(self):
        # THIS IS A HAX, todo: modify this to call celery with syncronous execution
        import time
        time.sleep(2)

        alert_instance = self.alert_class()()
        alert_instance.run()
        self.alert_task = alert_instance

        if self.expected_to_throw == True:
          expected_alert = self.alert()
          self.verify_alert(expected_alert)
        else:
          self.verify_alert_not_fired()

    def verify_alert(self, expected_alert):
        assert len(self.alert_task.alert_ids) != 0

        for alert_id in self.alert_task.alert_ids:
          alert = self.helper.get_alert_by_id(alert_id)

          assert alert['found'] == True
          assert alert['_type'] == 'alert'
          assert alert['_version'] == 1
          assert alert['_index'] == 'alerts'

          assert alert['_source']['category'] == expected_alert['_source']['category']
          assert alert['_source']['severity'] == expected_alert['_source']['severity']
          assert alert['_source']['summary'] == expected_alert['_source']['summary']
          assert alert['_source']['tags'] == expected_alert['_source']['tags']

          assert len(alert['_source']['events']) == len(expected_alert['_source']['events'])

    def verify_alert_not_fired(self):
        assert len(self.alert_task.alert_ids) == 0
