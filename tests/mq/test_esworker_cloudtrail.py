#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com

import pytz
import tzlocal


def utc_timezone():
    return pytz.timezone('UTC')


tzlocal.get_localzone = utc_timezone


import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../mq"))
from mq import esworker_cloudtrail


class MockOptions():
    @property
    def mozdefhostname(self):
        return 'sample'


class TestKeyMapping():
    def setup(self):
        mock_options = MockOptions()
        esworker_cloudtrail.options = mock_options
        self.key_mapping = esworker_cloudtrail.keyMapping

    def test_cloudtrail_dict(self):
        cloudtrail_dict = {
            u'apiVersion': u'20140328',
            u'awsRegion': u'us-west-2',
            u'eventID': u'd29avef1-1a81-4125-4cb1-3ddca313b6c3',
            u'eventName': u'CreateLogStream',
            u'eventSource': u'logs.amazonaws.com',
            u'eventTime': u'2017-10-14T19:54:01Z',
            u'eventType': u'AwsApiCall',
            u'eventVersion': u'1.04',
            u'recipientAccountId': u'125234098624',
            u'requestID': u'6146b9c2-153e-31e2-6782-1fb937ca1c57',
            u'requestParameters': {
                u'logGroupName': u'/aws/lambda/abcd-webhooks-pulse',
                u'logStreamName': u'2017/10/14/[$LATEST]a7918c9450164d3db2cef43f95bba7a7'
            },
            u'responseElements': None,
            u'sourceIPAddress': u'1.2.3.4',
            u'userAgent': u'awslambda-worker',
            u'userIdentity': {
                u'accessKeyId': u'ASBSDGLKHSDGBD2YXSGSLDHTJA',
                u'accountId': u'125234098624',
                u'arn': u'arn:aws:sts::125234098624:assumed-role/lambda-abcd-webhooks-pulse/abcd-webhooks-pulse',
                u'principalId': u'AROABRMQYSEGL3VWEDW3K:abcd-webhooks-pulse',
                u'sessionContext': {
                    u'attributes': {
                        u'creationDate': u'2017-10-14T19:47:02Z',
                        u'mfaAuthenticated': u'false'
                    },
                    u'sessionIssuer': {
                        u'accountId': u'125234098624',
                        u'arn': u'arn:aws:iam::125234098624:role/lambda-abcd-webhooks-pulse',
                        u'principalId': u'AROABRMQYSEGL3VWEDW3K',
                        u'type': u'Role',
                        u'userName': u'lambda-abcd-webhooks-pulse'
                    }
                },
                u'type': u'AssumedRole'
            }
        }

        result = self.key_mapping(cloudtrail_dict)

        assert result['category'] == 'AwsApiCall'
        assert result['hostname'] == 'logs.amazonaws.com'
        assert result['mozdefhostname'] == 'sample'
        assert type(result['processid']) is str
        # verify processid is an integer inside of that string
        assert int(result['processid'])
        assert type(result['processname']) is str
        assert result['severity'] == 'INFO'
        assert result['summary'] == '1.2.3.4 performed CreateLogStream in logs.amazonaws.com'
        assert result['timestamp'] == '2017-10-14T19:54:01+00:00'
        assert result['utctimestamp'] == '2017-10-14T19:54:01+00:00'
        assert result['receivedtimestamp'] != result['utctimestamp']
        expected_details = {
            u'apiversion': u'20140328',
            u'awsregion': u'us-west-2',
            'eventReadOnly': False,
            'eventVerb': u'Create',
            u'eventid': u'd29avef1-1a81-4125-4cb1-3ddca313b6c3',
            u'eventname': u'CreateLogStream',
            u'eventversion': u'1.04',
            u'recipientaccountid': u'125234098624',
            u'requestid': u'6146b9c2-153e-31e2-6782-1fb937ca1c57',
            u'requestparameters': {
                u'logGroupName': u'/aws/lambda/abcd-webhooks-pulse',
                u'logStreamName': u'2017/10/14/[$LATEST]a7918c9450164d3db2cef43f95bba7a7'
            },
            u'responseelements': None,
            'sourceipaddress': u'1.2.3.4',
            u'useragent': u'awslambda-worker',
            u'useridentity': {
                u'accessKeyId': u'ASBSDGLKHSDGBD2YXSGSLDHTJA',
                u'accountId': u'125234098624',
                u'arn': u'arn:aws:sts::125234098624:assumed-role/lambda-abcd-webhooks-pulse/abcd-webhooks-pulse',
                u'principalId': u'AROABRMQYSEGL3VWEDW3K:abcd-webhooks-pulse',
                u'sessionContext': {
                    u'attributes': {
                        u'creationDate': u'2017-10-14T19:47:02Z',
                        u'mfaAuthenticated': u'false'
                    },
                    u'sessionIssuer': {
                        u'accountId': u'125234098624',
                        u'arn': u'arn:aws:iam::125234098624:role/lambda-abcd-webhooks-pulse',
                        u'principalId': u'AROABRMQYSEGL3VWEDW3K',
                        u'type': u'Role',
                        u'userName': u'lambda-abcd-webhooks-pulse'
                    }
                },
                u'type': u'AssumedRole'
            }
        }

        assert result['details'] == expected_details
