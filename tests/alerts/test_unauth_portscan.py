from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertUnauthPortScan(AlertTestSuite):
    alert_filename = "unauth_portscan"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "bro",
        "_source": {
            "category": "bronotice",
            "summary": "Scan::Port_Scan 1.2.3.4 scanned at least 12 unique ports of host 5.6.7.8 in 0m3s local",
            "eventsource": "nsm",
            "hostname": "nsmhost",
            "details": {
              "uid": "",
              "actions": "Notice::ACTION_LOG",
              "note": "Scan::Port_Scan",
              "sourceipv4address": "0.0.0.0",
              "indicators": [
                "1.2.3.4"
              ],
              "msg": "1.2.3.4 scanned at least 12 unique ports of host 5.6.7.8 in 0m3s",
              "destinationipaddress": "5.6.7.8",
            },
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        'category': 'scan',
        'severity': 'NOTICE',
        'summary': "nsmhost: Unauthorized Port Scan Event from [u'1.2.3.4'] scanning ports on host 5.6.7.8",
        'tags': [],
        'url': 'https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures',
    }

    test_cases = [
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[default_event],
            expected_alert=default_alert
        ),

        PositiveAlertTestCase(
            description="Positive test case with an event with somewhat old timestamp",
            events=[
                {
                    "_source": {
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 29})
                    }
                }
            ],
            expected_alert=default_alert
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad event type",
            events=[
                {
                    "_type": "event",
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad category",
            events=[
                {
                    "_source": {
                        "category": "Badcategory",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad eventsource",
            events=[
                {
                    "_source": {
                        "eventsource": "Badeventsource",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with non existent details.indicators",
            events=[
                {
                    "_source": {
                        "details": {
                            "indicators": None,
                        }
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad details.note",
            events=[
                {
                    "_source": {
                        "details": {
                            "note": "Badnote",
                        }
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[
                {
                    "_source": {
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
                    }
                }
            ],
        ),
    ]
