# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Arzhel Younsi arzhel@mozilla.com
# Jeff Bryner jbryner@mozilla.com

dc_code_list = ['phx1', 'scl3', 'pao1', 'sjc2', 'pek1']
offices_code_list = ['par1', 'lon1', 'ber1', 'tpe1', 'pek2', 'tpe1', 'akl1', 'sfo1', 'mtv2', 'yvr1', 'tor1', 'pdx1']        

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


    def onMessage(self, message, metadata):
        if 'details' in message.keys() and 'hostname' in message['details'].keys():
            hostnamesplit= str.lower(message['details']['hostname'].encode('ascii', 'ignore')).split('.')
            if len(hostnamesplit) == 5:
                if 'mozilla' == hostnamesplit[-2]:
                    message['details']['site']=hostnamesplit[-3]
                    if message['details']['site'] in dc_code_list:
                        message['details']['sitetype']='datacenter'
                    elif message['details']['site'] in offices_code_list:
                        message['details']['sitetype']='office'
                    else:
                        message['details']['sitetype']='unknown'
        return (message, metadata)