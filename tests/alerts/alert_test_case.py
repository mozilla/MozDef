from tests.alerts.alert_test_suite import AlertTestSuite


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
        alert_task.close_connections()
        # for alerts that run multiple iterations
        # we want to know if an exception was thrown/caught
        # so we can bubble that up via pytest
        if hasattr(alert_task, 'error_thrown'):
            raise alert_task.error_thrown
        return alert_task
