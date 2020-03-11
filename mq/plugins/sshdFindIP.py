# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

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


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''
        # get events that may include an unparsed IP in the summary
        self.registration = ['sshd', 'fail2ban']
        self.priority = 5

    def onMessage(self, message, metadata):
        # if we don't have a source IP address
        # look for words that are IP addresses,
        # move to details.sourceipaddress
        doSearch = False
        detailsExists = True
        foundIPv4 = ''
        if 'summary' in message:
            if 'details' in message and isinstance(message['details'], dict):
                if 'sourceipaddress' not in message['details']:
                    doSearch = True
            else:
                doSearch = True
                detailsExists = False

            if doSearch:
                for word in message['summary'].strip().split():
                    # strip any surrounding quotes, commas, etc.
                    saneword = word.strip().strip('"').strip("'").strip(",")
                    if isIPv4(saneword):
                        foundIPv4 = saneword
                        break

            if len(foundIPv4):
                if not detailsExists:
                    message['details'] = dict()
                message['details']['sourceipaddress'] = foundIPv4

        return (message, metadata)
