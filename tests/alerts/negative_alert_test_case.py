from alert_test_case import AlertTestCase


class NegativeAlertTestCase(AlertTestCase):
    assert self.expected_alert is None, "NegativeAlertTestCase is used to test cases where an alert does not occur. Therefore expected_alert should be None."
    expected_test_result = False
