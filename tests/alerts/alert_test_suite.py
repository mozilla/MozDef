import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../alerts/"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from lib.config import LOGGING, ES

from unit_test_suite import UnitTestSuite

import random


class AlertTestSuite(UnitTestSuite):

    def event_type(self):
        # todo normalize all bro events and alerts so the _type is still
        # 'event'
        return 'event'

    def setup(self):
        super(AlertTestSuite, self).setup()

        alerts_dir = os.path.join(os.path.dirname(__file__), "../../alerts/")
        os.chdir(alerts_dir)

    def generate_default_event(self):
        current_timestamp = self.current_timestamp()

        source_ip = self.random_ip()

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
        for event in self.events():
            self.populate_test_event(event, self.event_type())

        # THIS IS A HAX, todo: modify this to call celery with syncronous
        # execution
        import time
        time.sleep(2)

        alert_instance = self.alert_class()()
        alert_instance.run()
        self.alert_task = alert_instance

        if self.expected_to_throw is True:
            expected_alert = self.alert()
            self.verify_alert(expected_alert)
        else:
            self.verify_alert_not_fired()

    def verify_alert(self, expected_alert):
        assert len(self.alert_task.alert_ids) != 0

        self.es_client.flush('alerts')
        for alert_id in self.alert_task.alert_ids:
            alert = self.get_alert_by_id(alert_id)

            assert alert['_index'] == 'alerts'
            assert alert['_type'] == 'alert'

            assert alert['_source']['category'] == expected_alert['_source']['category']
            assert alert['_source']['severity'] == expected_alert['_source']['severity']
            assert alert['_source']['summary'] == expected_alert['_source']['summary']
            assert alert['_source']['tags'] == expected_alert['_source']['tags']

            assert len(alert['_source']['events']) == len( expected_alert['_source']['events'])

    def verify_alert_not_fired(self):
        assert len(self.alert_task.alert_ids) == 0

    def get_alert_by_id(self, alert_id):
        return self.es_client.get_alert_by_id(alert_id)

    def random_ip(self):
        return str(random.randint(1, 255)) + "." + str(random.randint(1, 255)) + "." + str(random.randint(1, 255)) + "." + str(random.randint(1, 255))



