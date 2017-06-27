# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Brandon Myers bmyers@mozilla.com

import netaddr


def isIPv4(ip):
    try:
        # netaddr on it's own considers 1 and 0 to be valid_ipv4
        # so a little sanity check prior to netaddr.
        # Use IPNetwork instead of valid_ipv4 to allow CIDR
        if '.' in ip and len(ip.split('.'))==4:
            # some ips are quoted
            netaddr.IPNetwork(ip)
            return True
        else:
            return False
    except:
        return False


def findIPv4(words):
    for word in words.strip().split():
        saneword = word.strip().strip('"').strip("'").strip(",")
        if isIPv4(saneword):
            yield saneword


class message(object):
    def __init__(self):
        '''
        takes an incoming bro message
        and sets the doc_type
        '''

        self.registration = ['bro', 'nsm']
        self.priority = 5

    def onMessage(self, message, metadata):
        # set the doc type to bro
        # to avoid data type conflicts with other doc types
        # (int v string, etc)
        metadata['doc_type']= 'bro'

        # re-arrange the position of some fields
        # {} vs {'details':{}}
        if 'details' in message.keys():
            # details.tags -> tags
            if 'tags' in message['details'].keys():
                message['tags'] = message['details']['tags']
                del message['details']['tags']

            # details.summary -> summary
            if 'summary' in message['details'].keys():
                message['summary'] = message['details']['summary']
                del message['details']['summary']

            # clean up the action notice IP addresses
            if 'actions' in message['details'].keys():
                if message['details']['actions'] == "Notice::ACTION_LOG":
                    # retrieve indicator ip addresses from the sub field
                    # "sub": "Indicator: 1.2.3.4, Indicator: 5.6.7.8"
                    message['details']['indicators'] = [ip for ip
                                                        in findIPv4(message['details']['sub'])]

                    # remove the details.src field and add it to indicators
                    # as it may not be the actual source.
                    if 'src' in message['details'].keys():
                        if isIPv4(message['details']['src']):
                            message['details']['indicators'].append(message['details']['src'])
                            del message['details']['src']

        return (message, metadata)