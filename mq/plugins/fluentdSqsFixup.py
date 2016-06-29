# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation
#
# This script copies the format/handling mechanism of ipFixup.py (git f5734b0c7e412424b44a6d7af149de6250fc70a2)
#
# Contributors:
# Guillaume Destuynder kang@mozilla.com
# Jeff Bryner jbryner@mozilla.com

import netaddr
import unittest
import json

def isIPv4(ip):
    try:
        return netaddr.valid_ipv4(ip)
    except:
        return False

def isIPv6(ip):
    try:
        return netaddr.valid_ipv6(ip)
    except:
        return False

def addError(message, error):
    '''add an error note to a message'''
    if 'errors' not in message.keys():
        message['errors'] = list()
    if isinstance(message['errors'], list):
        message['errors'].append(error)

class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        # ask for anything that could house an IP address
        self.registration = ['nubis_events_non_prod', 'nubis_events_prod']
        self.priority = 15

    def onMessage(self, message, metadata):
        '''
        Ensure all messages that have 'details' have the mandatory mozdef fields
        '''
        details = message['details']

        # shortcuts if we're not interested in the message
        if not 'details' in message.keys():
            return (message, metadata)

        # Making sufficiently sure this is a fluentd-forwarded message from fluentd SQS plugin, so that we don't spend
        # too much time on other message types
        if (not 'az' in details.keys()) and (not 'instance_id' in details.keys()
            and (not '__tag' in details.keys())):
            return (message, metadata)

        # host is used to store dns-style-ip entries in AWS, for ex ip-10-162-8-26 is 10.162.8.26.
        # obviously there is no strong garantee that this is always trusted. It's better than nothing though.
        # At the time of writting, there is no ipv6 support AWS-side for this kind of field.
        # It may be overriden later by a better field, if any exists.
        if 'host' in details.keys():
            tmp = details['host']
            if tmp.startswith('ip-'):
                ipText = tmp.split('ip-')[1].replace('-', '.')
                if isIPv4(ipText):
                    if 'destinationipaddress' not in details.keys():
                        details['destinationipaddress'] = ipText
                    if 'destinationipv4address' not in details.keys():
                        details['destinationipv4address'] = ipText
                else:
                    details['destinationipaddress'] = '0.0.0.0'
                    details['destinationipv4address'] = '0.0.0.0'
                    addError(message, 'plugin: {0} error: {1}:{2}'.format('fluentSqsFixUp.py', 'destinationipaddress is invalid', ipText))
            if not 'hostname' in message.keys(): message['hostname'] = tmp

        # All messages with __tag 'ec2.forward*' are actually syslog forwarded messages, so classify as such
        if '__tag' in details.keys():
            tmp = details['__tag']
            if tmp.startswith('ec2.forward'):
                message['category'] = 'syslog'
                message['source'] = 'syslog'

        if 'ident' in details.keys():
            tmp = details['ident']
            details['program'] = tmp
            if (not 'processname' in message.keys()) and ('program' in details.keys()):
                message['processname'] = details['program']
            if (not 'processid' in message.keys()) and ('pid' in details.keys()):
                message['processid'] = details['pid']
            else:
                message['processid'] = 0
            # Unknown really, but this field is mandatory.
            if not 'severity' in message.keys(): message['severity'] = 'INFO'

        return (message, metadata)

class MessageTestFunctions(unittest.TestCase):
    def setUp(self):
        self.msgobj = message()
        self.msg = json.loads("""
{
  "_index": "events-20151022",
  "_type": "event",
  "_id": "_KJo6K-dTk2MFeKK-dUKZw",
  "_score": null,
  "_source": {
    "receivedtimestamp": "2015-10-22T04:57:33.752446+00:00",
    "utctimestamp": "2015-10-22T04:57:00+00:00",
    "tags": [
      "nubis_events_non_prod"
    ],
    "timestamp": "2015-10-22T04:57:00+00:00",
    "mozdefhostname": "mozdefqa1.private.scl3.mozilla.com",
    "summary": "Connection closed by 10.10.10.10 [preauth]",
    "details": {
      "ident": "sshd",
      "__tag": "ec2.forward.system.secure",
      "region": "us-east-1",
      "pid": "24710",
      "instance_id": "i-b0a7de10",
      "instance_type": "t2.micro",
      "host": "ip-11-11-11-11",
      "sourceipgeolocation": {
        "city": null,
        "region_code": null,
        "area_code": 0,
        "time_zone": "Asia/Seoul",
        "dma_code": 0,
        "metro_code": null,
        "country_code3": "KOR",
        "latitude": 37.56999999999999,
        "postal_code": null,
        "longitude": 126.98000000000002,
        "country_code": "KR",
        "country_name": "Korea, Republic of",
        "continent": "AS"
      },
      "time": "2015-10-22T04:57:00Z",
      "message": "Connection closed by 10.10.10.10 [preauth]",
      "az": "us-east-1a"
    }
  },
  "sort": [
    1445489820000
  ]
}
""")
        self.msg2 =json.loads("""
{
  "_index": "events-20151022",
  "_type": "event",
  "_id": "3eQPX3MMRLOnGQBuX9NQiA",
  "_score": null,
  "_source": {
    "receivedtimestamp": "2015-10-22T05:24:41.721237+00:00",
    "utctimestamp": "2015-10-22T05:24:26+00:00",
    "tags": [
      "nubis_events_non_prod"
    ],
    "timestamp": "2015-10-22T05:24:26+00:00",
    "mozdefhostname": "mozdefqa1.private.scl3.mozilla.com",
    "summary": "INFO (transaction.py:150): Flushing 1 transaction during flush #377900",
    "details": {
      "ident": "dd.forwarder",
      "__tag": "ec2.forward.system.syslog",
      "region": "us-east-1",
      "pid": "1969",
      "instance_id": "i-965f8f42",
      "instance_type": "m3.medium",
      "host": "ip-10-162-17-177",
      "time": "2015-10-22T05:24:26Z",
      "message": "INFO (transaction.py:150): Flushing 1 transaction during flush #377900",
      "az": "us-east-1d"
    }
  },
  "sort": [
    1445491466000
  ]
}
""")

    def test_onMessageSSH(self):
        metadata = {}
        (retmessage, retmeta) = self.msgobj.onMessage(self.msg['_source'], metadata)
        self.assertEqual(retmessage['category'], 'syslog')
        self.assertEqual(retmessage['details']['program'], 'sshd')

    def test_onMessageGeneric(self):
        metadata = {}
        (retmessage, retmeta) = self.msgobj.onMessage(self.msg2['_source'], metadata)
        self.assertEqual(retmessage['category'], 'syslog')
        self.assertEqual(retmessage['hostname'], 'ip-10-162-17-177')

if __name__ == '__main__':
    unittest.main(verbosity=2)
