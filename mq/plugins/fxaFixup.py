# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import netaddr


def isIP(ip):
    try:
        netaddr.IPNetwork(ip)
        return True
    except:
        return False


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''
        # get specific categories
        # for firefox accounts data sent by heka
        self.registration = ['fxaauthwebserver',
                             'fxaauth',
                             'fxacontentwebserver',
                             'fxacustoms',
                             'fxaoauthwebserver',
                             'fxabrowseridwebserver',
                             'fxaprofilewebserver',
                             'fxa-auth-server',
                             'fxa-customsmozsvc'
                             ]
        self.priority = 10

    def onMessage(self, message, metadata):

        if 'eventsource' not in message:
            return (message, metadata)
        # drop non-relevant messages
        if message['eventsource'] in ('Fxa-customsMozSvc', 'FxaContentWebserver', 'FxaAuthWebserver', 'FxaOauthWebserver', 'FxaAuth', 'fxa-auth-server'):
            if 'details' in message:
                if 'status' in message['details']:
                    if message['details']['status'] == 200:
                        # normal 200 returns for web content
                        return(None, metadata)
                # FxaAuth sends http status as 'code'
                if 'code' in message['details']:
                    if message['details']['code'] == 200:
                        # normal 200 returns for web content
                        return(None, metadata)
                if 'op' in message['details']:
                    if message['details']['op'] == 'mailer.send.1':
                        # Due to status flag not being a string
                        return(None, metadata)

        # tag the message
        if 'tags' in message and isinstance(message['tags'], list):
            message['tags'].append('firefoxaccounts')
        else:
            message['tags'] = ['firefoxaccounts']

        # fix various fields
        if 'details' in message and isinstance(message['details'], dict):
            # elastic search needs valid IPs for ip fields.
            if 'http_x_forwarded_for' in message['details']:
                if message['details']['http_x_forwarded_for'] == '-':
                    message['details']['http_x_forwarded_for'] = '0.0.0.0'

            if 'upstream_response_time' in message['details']:
                if message['details']['upstream_response_time'] == '-':
                    message['details']['upstream_response_time'] = 0

            # category fixes
            if 'name' in message['details']:
                if message['details']['name'] == 'fxa-auth-server':
                    message['category'] = 'fxa-auth-server'

            if message['eventsource'] in ('FxaContentWebserver', 'FxaAuthWebserver'):
                if message['category'] == 'logfile':
                    message['category'] = 'weblog'

            if 'remoteaddresschain' in message['details']:
                if isinstance(message['details']['remoteaddresschain'], list):
                    sourceIP = message['details']['remoteaddresschain'][0]
                    if isIP(sourceIP):
                        message['details']['sourceipaddress'] = sourceIP

                # handle the case of an escaped list:
                # "remoteaddresschain": "[\"1.2.3.4\",\"5.6.7.8\",\"127.0.0.1\"]"
                if (isinstance(message['details']['remoteaddresschain'], str) and
                        message['details']['remoteaddresschain'][0] == '[' and
                        message['details']['remoteaddresschain'][-1] == ']'):
                    # remove the brackets and double quotes
                    for i in ['[', ']', '"']:
                        message['details']['remoteaddresschain'] = message['details']['remoteaddresschain'].replace(i, '')
                    # make sure it's still a list
                    if ',' in message['details']['remoteaddresschain']:
                        sourceIP = message['details']['remoteaddresschain'].split(',')[0]
                        if isIP(sourceIP):
                            message['details']['sourceipaddress'] = sourceIP

            # fxacustoms sends source ip as just 'ip'
            if 'ip' in message['details']:
                if isIP(message['details']['ip']):
                    message['details']['sourceipaddress'] = message['details']['ip']

        return (message, metadata)
