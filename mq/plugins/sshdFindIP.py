# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import netaddr


def isIP(ip):
    try:
        # netaddr on it's own considers 1 and 0 to be valid_ipv4
        # so a little sanity check prior to netaddr.
        if '.' in ip and len(ip.split('.'))==4:
            # some ips are quoted
            netaddr.IPNetwork(ip.strip("'").strip('"'))
            return True
        else:
            return False
    except:
        return False


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''
        # get sshd events
        self.registration = ['sshd', 'fail2ban']
        self.priority = 5
        
    def onMessage(self, message, metadata):
        # if we don't have a source IP address
        # look for words that are IP addresses, 
        # move to details.sourceipaddress
        if 'summary' in message.keys():
            if 'details' in message.keys() and isinstance(message['details'], dict):
                if 'sourceipaddress' not in message['details'].keys():
                    for w in message['summary'].strip().split():
                        if isIP(w):
                            message['details']['sourceipaddress'] = w

        return (message, metadata)