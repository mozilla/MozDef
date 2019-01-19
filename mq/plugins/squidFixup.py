# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2018 Mozilla Corporation

import netaddr
import json
from datetime import datetime
from platform import node
from mozdef_util.utilities.toUTC import toUTC


class message(object):
    def __init__(self):
        '''
        takes an incoming bro message
        and sets the doc_type
        '''

        self.registration = ['squid']
        self.priority = 5
        try:
            self.mozdefhostname = u'{0}'.format(node())
        except:
            self.mozdefhostname = 'failed to fetch mozdefhostname'
            pass

    def onMessage(self, message, metadata):

        # make sure I really wanted to see this message
        # bail out early if not
        if u'customendpoint' not in message:
            return message, metadata
        if u'category' not in message:
            return message, metadata
        if message['category'] != 'proxy':
            return message, metadata

        # set the doc type to nsm
        # to avoid data type conflicts with other doc types
        # (int v string, etc)
        # index holds documents of type 'type'
        # index -> type -> doc
        metadata['doc_type']= 'nsm'

        # move Squid specific fields under 'details' while preserving metadata
        newmessage = dict()

        # import pdb;pdb.set_trace()
        newmessage['details'] = {}

        # move some fields that are expected at the event 'root' where they belong
        if 'host_from' in message:
            newmessage['hostname'] = message['host_from']
        if 'tags' in message:
            newmessage['tags'] = message['tags']
        if 'category' in message:
            newmessage['category'] = message['category']
        newmessage[u'source'] = u'unknown'
        if 'source' in message:
            newmessage[u'source'] = message['source']
        logtype = newmessage['source']
        newmessage[u'event_type'] = u'unknown'

        # add mandatory fields
        if 'PROGRAM' in message:
            newmessage[u'utctimestamp'] = toUTC(float(message['PROGRAM'])).isoformat()
            newmessage[u'timestamp'] = toUTC(float(message['PROGRAM'])).isoformat()
        else:
            # a malformed message somehow managed to crawl to us, let's put it somewhat together
            newmessage[u'utctimestamp'] = toUTC(datetime.now()).isoformat()
            newmessage[u'timestamp'] = toUTC(datetime.now()).isoformat()

        newmessage[u'receivedtimestamp'] = toUTC(datetime.now()).isoformat()
        newmessage[u'eventsource'] = u'squid'
        newmessage[u'severity'] = u'INFO'
        newmessage[u'mozdefhostname'] = self.mozdefhostname

        # Error checking, anyone??
        line = message['MESSAGE'].strip()
        tokens = line.split()

        newmessage[u'details'][u'sourceipaddress'] = tokens[1]
        newmessage[u'details'][u'proxyaction'] = tokens[2]
        newmessage[u'details'][u'tcpaction'] = tokens[4]
        newmessage[u'details'][u'destination'] = tokens[5]
        newmessage[u'details'][u'mimetype'] = tokens[8]

        return (newmessage, metadata)
