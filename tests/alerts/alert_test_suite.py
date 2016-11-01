import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from unit_test_suite import UnitTestSuite

import copy
import re


class AlertTestSuite(UnitTestSuite):
    def setup(self):
        super(AlertTestSuite, self).setup()

        alerts_dir = os.path.join(os.path.dirname(__file__), "../../alerts/")
        os.chdir(alerts_dir)

        self.alert_classname = (self.__class__.__name__[4:] if
                                self.__class__.__name__.startswith('Test') else
                                False)

        if not self.alert_filename:
            # Convert "AlertFooBar" to "foo_bar" and "BazQux" to "baz_qux"
            self.alert_filename = re.sub(
                '([a-z0-9])([A-Z])',
                r'\1_\2',
                re.sub(
                    '(.)([A-Z][a-z]+)',
                    r'\1_\2',
                    self.alert_classname[5:] if
                    self.alert_classname.startswith('Alert') else
                    self.alert_classname)).lower()

    # Some housekeeping stuff here to make sure the data we get is 'good'
    def verify_starting_values(self, test_case):
        # Verify the description for the test case is populated
        assert test_case.description is not None or ""
        assert test_case.description is not ""

        # Verify alert_filename is a legit file
        # full_alert_file_path = "../../../alerts/" + self.alert_filename + ".py"
        full_alert_file_path = "./" + self.alert_filename + ".py"
        assert os.path.isfile(full_alert_file_path) is True

        # Verify we're able to load in the alert_classname
        # This can probably be improved, but for the mean time, we're just
        # gonna grep for class name
        alert_source_str = open(full_alert_file_path, 'r').read()
        class_search_str = "class " + self.alert_classname + "("
        assert class_search_str in alert_source_str

        # Verify events is not empty
        assert len(test_case.events) is not 0

        # Verify that if we're a positive test case, we actually passed in an
        # expected_alert
        if test_case.expected_test_result is True:
            assert test_case.expected_alert is not None
        else:
            # How can we expect an alert, when we're expecting the alert to
            # never throw?
            assert test_case.expected_alert is None

    # todo: remote this out to utilities
    def dict_merge(self, target, *args):
        # Merge multiple dicts
        if len(args) > 1:
            for obj in args:
                self.dict_merge(target, obj)
            return target

        # Recursively merge dicts and set non-dict values
        obj = args[0]
        if not isinstance(obj, dict):
            return obj
        for k, v in obj.iteritems():
            if k in target and isinstance(target[k], dict):
                self.dict_merge(target[k], v)
            else:
                target[k] = v
        return target

    def test_alert_test_case(self, test_case):
        self.verify_starting_values(test_case)
        temp_events = test_case.events
        for event in temp_events:
            temp_event = self.dict_merge(self.generate_default_event(), self.default_event)

            merged_event = self.dict_merge(temp_event, event)
            merged_event['_source']['utctimestamp'] = merged_event['_source']['utctimestamp']()
            test_case.full_events.append(merged_event)
            self.populate_test_event(
                merged_event['_source'], merged_event['_type'])

        self.es_client.flush('events')

        alert_task = test_case.run(alert_filename=self.alert_filename, alert_classname=self.alert_classname)
        self.verify_alert_task(alert_task, test_case)

    def verify_expected_alert(self, found_alert, test_case):
        # Verify index is set correctly
        assert found_alert['_index'] == 'alerts'
        # Verify alert type is correct
        assert found_alert['_type'] == 'alert'

        # Verify that the alert has the right "look to it"
        assert found_alert.keys() == [
            '_score', '_type', '_id', '_source', '_index']

        # Verify the alert has an id field that is unicode
        assert type(found_alert['_id']) == unicode

        # Verify there is a utctimestamp field
        assert 'utctimestamp' in found_alert['_source']

        # Verify the events are added onto the alert
        assert type(found_alert['_source']['events']) == list
        assert len(found_alert['_source']['events']) is not 0
        alert_events = found_alert['_source']['events']
        sorted_alert_events = sorted(alert_events, key=lambda k: k[
                                     'documentsource']['utctimestamp'])

        created_events = test_case.full_events
        sorted_created_events = sorted(created_events, key=lambda k: k[
                                       '_source']['utctimestamp'])

        event_index = 0
        for event in sorted_alert_events:
            assert event['documentsource'] == sorted_created_events[
                event_index]['_source']
            event_index += 1

        # Verify that the alert properties are set correctly
        for key, value in test_case.expected_alert.iteritems():
            assert found_alert['_source'][key] == value

    def verify_alert_task(self, alert_task, test_case):
        if test_case.expected_test_result is True:
            assert len(alert_task.alert_ids) is not 0
            self.es_client.flush('alerts')
            for alert_id in alert_task.alert_ids:
                found_alert = self.es_client.get_alert_by_id(alert_id)
                self.verify_expected_alert(found_alert, test_case)
        else:
            assert len(alert_task.alert_ids) is 0

    @staticmethod
    def copy(obj):
        return copy.deepcopy(obj)
