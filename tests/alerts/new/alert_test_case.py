import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../alerts"))


class AlertTestCase(object):
    def __init__(self, description, events=[], events_type='event', expected_alert=None):
        self.description = description
        self.events = events
        self.events_type = events_type
        self.expected_alert = expected_alert
        self.full_events = []

    def run(self, alert_src, alert_name):
        print('\n\tTesting {}'.format(self.description))
        alert_file_module = __import__(alert_src)
        alert_class = getattr(alert_file_module, alert_name)

        # THIS IS A HAX, todo: modify this to call celery with syncronous
        # execution
        import time
        time.sleep(2)

        alert_task = alert_class()
        alert_task.run()
        return alert_task

