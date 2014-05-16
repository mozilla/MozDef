# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

import os
import json

def flattenDict(inDict, pre=None, values=True):
    '''given a dictionary, potentially with multiple sub dictionaries
       return a period delimited version of the dict with or without values
       i.e. {'something':'value'} becomes something=value
            {'something':{'else':'value'}} becomes something.else=value
    '''
    pre = pre[:] if pre else []
    if isinstance(inDict, dict):
        for key, value in inDict.iteritems():
            if isinstance(value, dict):
                for d in flattenDict(value, pre + [key], values):
                    yield d
            else:
                if pre:
                    if values:
                        if isinstance(value, str):
                            yield '.'.join(pre) + '.' + key + '=' + str(value)
                        elif isinstance(value, unicode):
                            yield '.'.join(pre) + '.' + key + '=' + value.encode('ascii', 'ignore')
                        elif value is True:
                            yield '.'.join(pre) + '.' + key + '=None'
                    else:
                        yield '.'.join(pre) + '.' + key
                else:
                    if values:
                        if isinstance(value, str):
                            yield key + '=' + str(value)
                        elif isinstance(value, unicode):
                            yield key + '=' + value.encode('ascii', 'ignore')
                        elif value is True:
                            yield key + '=None'
                    else:
                        yield key
    else:
        yield '-'.join(pre) + '.' + inDict

class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           return a dict with fieldname:None to be sent anything with that field
           return a dict with fieldname:Value to be sent anything with that field/value
           return a string to be sent anything with any field matching that string evaluated as a regex.
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''

        self.loadconfig()
        self.registration = self.get_registration()
        self.priority = 20


    def loadconfig(self):
        """
        Load the config file
        """
        configfile = os.path.abspath(__file__).replace('.pyc', '.json')
        # if os.path.isfile(configfile):
        confighandler = open(configfile)
        data = json.load(confighandler)
        self.data = data
        confighandler.close()
        self.data_fields = []
        self.data_ttl = []
        for ttl_config in data['ttl']:
            flatdict = flattenDict(ttl_config['fields'])
            self.data_fields.append([e for e in flatdict])
            self.data_ttl.append(ttl_config['ttl'])

        # else:
        #     return {}

    def get_registration(self):
        """
        Gets registration by replacing ttl dict values by None
        """
        def recur_replace(d):
            for k, v in d.iteritems():
                if isinstance(v, dict):
                    d[k] = recur_replace(v)
                elif v is True:
                    d[k] = None
            return d

        registration = self.data['registration']
        # Replace true in json by None in python
        registration = recur_replace(registration)
        return registration

    def onMessage(self, message):
        for i in range(len(self.data_fields)):
            match = True
            # Flatten dict structure

            flatdict = flattenDict(message)
            flatten_message = [e for e in flatdict]

            # print flatten_ttl_fields
            # print flatten_message

            for field_ttl in self.data_fields[i]:
                # Consider when None
                if field_ttl.endswith('=None'):
                    match_none = False
                    for field_message in flatten_message:
                        if field_message.startswith(field_ttl[:-4]):
                            match_none = True
                            break
                    match = match_none
                else:
                    # Consider when value
                    if field_ttl not in flatten_message:
                        match = False
                        break

            if match:
                # configure the ttl
                message['ttl'] = self.data_ttl[i]
                break

        # print message

        return message


# M = message()
# M.onMessage({
#     "timestamp": "2014-04-17T05:31:33.631170+00:00",
#     "summary": "Unix Exec",
#     "receivedtimestatmp": "2014-04-17T05:33:33.637966+00:00",
#     "utctimestamp": "2014-04-17T05:33:33.631170+00:00",
#     "tags": [
#       "example"
#     ],
#     "details": {
#       "auid": "0",
#       "parentprocess": "java",
#       "severity": "3",
#       "duid": "2317",
#       "truncated": "Yes",
#       "deviceversion": "2",
#       "auditkey": "exec ",
#       "devicevendor": "Unix",
#       "tty": "(none)",
#       "duser": "mapred",
#       "dproc": "/usr/java/jdk1.6.0_31/jre/bin/java",
#       "version": "0",
#       "command": "",
#       "signatureid": "EXECVE",
#       "suser": "root",
#       "msg": "",
#       "dhost": "node33.example.com",
#       "fname": "/usr/java/jdk1.6.0_31/jre/bin/java",
#       "deviceproduct": "auditd",
#       "name": "Unix Exec"
#     }
# })

# M.onMessage({
#     "eventVersion": "1.01",
#     "eventID": "8d5840cf-6ne3-4947-be6b-cb5147856719",
#     "eventTime": "2014-04-17T06:32:05Z",
#     "utctimestamp": "2014-04-17T06:32:05+00:00",
#     "responseElements": None,
#     "awsRegion": "us-east-1",
#     "eventName": "DescribeInstances",
#     "userIdentity": {
#       "userName": "John",
#       "principalId": "XXXXXXXXXXXXXXXXXXXXX",
#       "accessKeyId": "XXXXXXXXXXXXXXXXXXXXX",
#       "type": "IAMUser",
#       "arn": "arn:aws:iam::646131927850:user/John",
#       "accountId": "646131927850"
#     },
#     "eventSource": "ec2.amazonaws.com",
#     "requestID": "eaa5966a-5d22-43f2-b2bf-4930afe601a4",
#     "userAgent": "aws-sdk-dotnet/1.4.11.0 .NET Runtime/4.0 .NET Framework/4.0 OS/6.1.7601.65536",
#     "sourceIPAddress": "59.15.171.43",
#     "tags": [
#       "example"
#     ]
# })

# M.onMessage({
#     "category": "syslog",
#     "processid": "0",
#     "severity": "INFO",
#     "utctimestamp": "2014-04-17T06:06:52+00:00",
#     "timestamp": "2014-04-17T06:06:52+00:00",
#     "hostname": "syslog.example.com",
#     "receivedtimestatmp": "2014-04-17T06:06:52.825668+00:00",
#     "summary": "Did not receive identification string from 10.0.0.210\n",
#     "eventsource": "systemslogs",
#     "tags": [
#       "example"
#     ],
#     "details": {
#       "processid": "1939",
#       "program": "sshd",
#       "hostname": "git",
#       "payload": "",
#       "timestamp": "Apr 17 06:06:51"
#     }
# })

