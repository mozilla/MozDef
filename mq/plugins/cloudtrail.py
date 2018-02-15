# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
            Plugin used to fix object type discretions with cloudtrail messages
        '''
        self.registration = ['cloudtrail']
        self.priority = 10

    def onMessage(self, message, metadata):
        if 'source' not in message:
            return (message, metadata)

        if not message['source'] == 'cloudtrail':
            return (message, metadata)

        if 'details' not in message:
            return (message, metadata)

        if type(message['details']) is not dict:
            return (message, metadata)

        if 'requestparameters' in message['details'] and type(message['details']['requestparameters']) is dict:
            # Handle details.requestparameters.iamInstanceProfile strings
            if 'iamInstanceProfile' in message['details']['requestparameters']:
                iam_instance_profile = message['details']['requestparameters']['iamInstanceProfile']
                if type(iam_instance_profile) is not dict:
                    message['details']['requestparameters']['iamInstanceProfile'] = {
                        'raw_value': iam_instance_profile
                    }

            # Handle details.requestparameters.attribute strings
            if 'attribute' in message['details']['requestparameters']:
                attribute = message['details']['requestparameters']['attribute']
                if type(attribute) is not dict:
                    message['details']['requestparameters']['attribute'] = {
                        'raw_value': attribute
                    }

            # Handle details.requestparameters.description strings
            if 'description' in message['details']['requestparameters']:
                description = message['details']['requestparameters']['description']
                if type(description) is not dict:
                    message['details']['requestparameters']['description'] = {
                        'raw_value': description
                    }

            # Handle details.requestparameters.filter strings
            if 'filter' in message['details']['requestparameters']:
                filter_str = message['details']['requestparameters']['filter']
                if type(filter_str) is not dict:
                    message['details']['requestparameters']['filter'] = {
                        'raw_value': filter_str
                    }

            # Handle details.requestparameters.rule strings
            if 'rule' in message['details']['requestparameters']:
                rule_str = message['details']['requestparameters']['rule']
                if type(rule_str) is not dict:
                    message['details']['requestparameters']['rule'] = {
                        'raw_value': rule_str
                    }

        if 'responseelements' in message['details'] and type(message['details']['responseelements']) is dict:
            # Handle details.responseelements.role strings
            if 'role' in message['details']['responseelements']:
                role_str = message['details']['responseelements']['role']
                if type(role_str) is not dict:
                    message['details']['responseelements']['role'] = {
                        'raw_value': role_str
                    }

            # Handle details.responseelements.subnets strings
            if 'subnets' in message['details']['responseelements']:
                subnets_str = message['details']['responseelements']['subnets']
                if type(subnets_str) is not dict:
                    message['details']['responseelements']['subnets'] = {
                        'raw_value': subnets_str
                    }

            # Handle details.responseelements.endpoint strings
            if 'endpoint' in message['details']['responseelements']:
                endpoint_str = message['details']['responseelements']['endpoint']
                if type(endpoint_str) is not dict:
                    message['details']['responseelements']['endpoint'] = {
                        'raw_value': endpoint_str
                    }

        # Handle details.additionaleventdata strings
        if 'additionaleventdata' in message['details']:
            additionaleventdata_str = message['details']['additionaleventdata']
            if type(additionaleventdata_str) is not dict:
                message['details']['additionaleventdata'] = {
                    'raw_value': additionaleventdata_str
                }

        # Handle details.serviceeventdetails strings
        if 'serviceeventdetails' in message['details']:
            serviceeventdetails_str = message['details']['serviceeventdetails']
            if type(serviceeventdetails_str) is not dict:
                message['details']['serviceeventdetails'] = {
                    'raw_value': serviceeventdetails_str
                }

        return (message, metadata)
