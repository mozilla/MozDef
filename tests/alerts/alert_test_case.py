import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../alerts"))

from alert_test_suite import AlertTestSuite


class AlertTestCase(object):
    def __init__(self, description, events=[], expected_alert=None):
        self.description = description
        # As a result of defining our test cases as class level variables
        # we need to copy each event so that other tests dont
        # mess with the same instance in memory
        self.events = AlertTestSuite.copy(events)
        assert any(isinstance(i, list) for i in self.events) is False, 'Test case events contains a sublist when it should not.'
        self.expected_alert = expected_alert
        self.full_events = []

    def run(self, alert_filename, alert_classname):
        alert_file_module = __import__(alert_filename)
        alert_class_attr = getattr(alert_file_module, alert_classname)

        alert_task = alert_class_attr()
        alert_task.run()
        return alert_task
