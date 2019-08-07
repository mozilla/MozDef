# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
            Plugin used to parse a filterlog type firewall message
        '''
        self.registration = ['filterlog']
        self.priority = 10

    def onMessage(self, message, metadata):
        if 'summary' not in message:
            return (message, metadata)

        if message['summary'].count(',') < 9:
            return (message, metadata)

        if 'details' not in message:
            message['details'] = {}

        summary_items = message['summary'].split(',')
        message['details']['rulenumber'] = summary_items[0]
        message['details']['subrulenumber'] = summary_items[1]
        message['details']['anchor'] = summary_items[2]
        message['details']['trackor'] = summary_items[3]
        message['details']['interface'] = summary_items[4]
        message['details']['reason'] = summary_items[5]
        message['details']['action'] = summary_items[6]
        message['details']['direction'] = summary_items[7]
        message['details']['ipversion'] = summary_items[8]

        ip_version = int(message['details']['ipversion'])
        if ip_version == 4:
            if 'ip' not in message['details']:
                message['details']['ip'] = {}

            message['details']['ip']['version'] = 4
            message['details']['ip']['tos'] = summary_items[9]
            message['details']['ip']['ecn'] = summary_items[10]
            message['details']['ip']['ttl'] = summary_items[11]
            message['details']['ip']['id'] = summary_items[12]
            message['details']['ip']['offset'] = summary_items[13]
            message['details']['ip']['flags'] = summary_items[14]
            message['details']['ip']['protocolid'] = summary_items[15]
            message['details']['ip']['protocoltext'] = summary_items[16]
            last_index = 16
        elif ip_version == 6:
            if 'ip' not in message['details']:
                message['details']['ip'] = {}

            message['details']['ip']['version'] = 6
            message['details']['ip']['class'] = summary_items[9]
            message['details']['ip']['flow_label'] = summary_items[10]
            message['details']['ip']['hoplimit'] = summary_items[11]
            message['details']['ip']['protocol'] = summary_items[12]
            message['details']['ip']['protocolid'] = summary_items[13]
            last_index = 13

        if ip_version == 4 or ip_version == 6:
            message['details']['ip']['length'] = summary_items[last_index + 1]
            message['details']['sourceipaddress'] = summary_items[last_index + 2]
            message['details']['destinationipaddress'] = summary_items[last_index + 3]

        proto_id = int(message['details']['ip']['protocolid'])

        if proto_id == 6:
            if 'tcp' not in message['details']:
                message['details']['tcp'] = {}

            message['details']['sourceport'] = summary_items[last_index + 4]
            message['details']['destinationport'] = summary_items[last_index + 5]
            message['details']['datalength'] = summary_items[last_index + 6]
            message['details']['tcp']['flags'] = summary_items[last_index + 7]
            message['details']['tcp']['seqnumber'] = summary_items[last_index + 8]
            message['details']['tcp']['acknumber'] = summary_items[last_index + 9]
            message['details']['tcp']['window'] = summary_items[last_index + 10]
            message['details']['tcp']['urg'] = summary_items[last_index + 11]
            message['details']['tcp']['options'] = summary_items[last_index + 12]
        elif proto_id == 17:
            message['details']['sourceport'] = summary_items[last_index + 4]
            message['details']['destinationport'] = summary_items[last_index + 5]
            message['details']['datalength'] = summary_items[last_index + 6]

        return (message, metadata)
