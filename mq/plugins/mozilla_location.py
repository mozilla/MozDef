# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
from configlib import getConfig


class message(object):
    def __init__(self):
        '''
        this plugin takes a source hostname of form
        host.private.site.mozilla.com
        extracts the site, adds it and compares the site
        to a list of known datacenters or offices and adds that metadata
        '''
        self.registration = ['network', 'netflow']
        self.priority = 5

        config_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mozilla_location.conf")
        self.dc_code_list = getConfig('dc_code_list', '', config_location).split(',')
        self.offices_code_list = getConfig('offices_code_list', '', config_location).split(',')

    def onMessage(self, message, metadata):
        if 'details' in message and 'hostname' in message['details']:
            hostnamesplit = str.lower(message['details']['hostname']).split('.')
            if len(hostnamesplit) == 5:
                if 'mozilla' == hostnamesplit[-2]:
                    message['details']['site'] = hostnamesplit[-3]
                    if message['details']['site'] in self.dc_code_list:
                        message['details']['sitetype'] = 'datacenter'
                    elif message['details']['site'] in self.offices_code_list:
                        message['details']['sitetype'] = 'office'
                    else:
                        message['details']['sitetype'] = 'unknown'
        elif 'hostname' in message:
            hostnamesplit = str.lower(message['hostname']).split('.')
            if len(hostnamesplit) == 5:
                if 'mozilla' == hostnamesplit[-2]:
                    message['details']['site'] = hostnamesplit[-3]
                    if message['details']['site'] in self.dc_code_list:
                        message['details']['sitetype'] = 'datacenter'
                    elif message['details']['site'] in self.offices_code_list:
                        message['details']['sitetype'] = 'office'
                    else:
                        message['details']['sitetype'] = 'unknown'
        return (message, metadata)
