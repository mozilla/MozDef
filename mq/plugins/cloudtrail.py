# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import sys
import os
from mozdef_util.utilities.key_exists import key_exists


class message(object):
    def __init__(self):
        '''
            Plugin used to fix object type discretions with cloudtrail messages
        '''
        self.registration = ['cloudtrail']
        self.priority = 10

        # Just add new entry to this dict to
        # automatically convert key mappings
        # which are mixed string and dict
        # into a dict with a raw_value key as the string value
        self.modify_keys = [
            'details.requestparameters.iamInstanceProfile',
            'details.requestparameters.instanceType',
            'details.requestparameters.attribute',
            'details.requestparameters.description',
            'details.requestparameters.filter',
            'details.requestparameters.rule',
            'details.requestparameters.ebsOptimized',
            'details.requestparameters.source',
            'details.requestparameters.callerReference',
            'details.requestparameters.domainName',
            'details.requestparameters.domainNames',
            'details.responseelements.role',
            'details.responseelements.subnets',
            'details.responseelements.endpoint',
            'details.responseelements.securityGroups',
            'details.responseelements.lastModified',
            'details.additionaleventdata',
            'details.serviceeventdetails',
            'details.requestparameters.disableApiTermination',
            'details.responseelements.findings.service.additionalInfo.unusual',
            'details.responseelements.distribution.distributionConfig.callerReference',
            'details.requestparameters.logStreamName'
        ]

    def convert_key_raw_str(self, needle, haystack):
        num_levels = needle.split(".")
        if len(num_levels) == 0:
            return False
        current_pointer = haystack
        for updated_key in num_levels:
            if updated_key == num_levels[-1]:
                current_pointer[updated_key] = {
                    'raw_value': str(current_pointer[updated_key])
                }
                return haystack
            if updated_key in current_pointer:
                current_pointer = current_pointer[updated_key]
            else:
                return haystack

    def onMessage(self, message, metadata):
        if 'source' not in message:
            return (message, metadata)

        if not message['source'] == 'cloudtrail':
            return (message, metadata)

        for modified_key in self.modify_keys:
            if key_exists(modified_key, message):
                message = self.convert_key_raw_str(modified_key, message)

        return (message, metadata)
