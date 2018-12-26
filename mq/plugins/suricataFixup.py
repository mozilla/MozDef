# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2018 Mozilla Corporation

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

        self.registration = ['suricata']
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
        if message['category'] != 'suricata':
            return message, metadata

        # set the doc type to nsm
        # to avoid data type conflicts with other doc types
        # (int v string, etc)
        # index holds documents of type 'type'
        # index -> type -> doc
        metadata['doc_type']= 'nsm'

        # move Suricata specific fields under 'details' while preserving metadata
        newmessage = dict()

        try:
            newmessage['details'] = json.loads(message['message'])
        except:
            newmessage['details'] = {}
            newmessage['rawdetails'] = message

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
        if 'event_type' in message:
            newmessage[u'event_type'] = message['event_type']
        eventtype = newmessage['event_type']

        # add mandatory fields
        if 'flow' in newmessage['details']:
            if 'start' in newmessage['details']['flow']:
                newmessage[u'utctimestamp'] = toUTC(newmessage['details']['flow']['start']).isoformat()
                newmessage[u'timestamp'] = toUTC(newmessage['details']['flow']['start']).isoformat()
        else:
            # a malformed message somehow managed to crawl to us, let's put it somewhat together
            newmessage[u'utctimestamp'] = toUTC(datetime.now()).isoformat()
            newmessage[u'timestamp'] = toUTC(datetime.now()).isoformat()

        newmessage[u'receivedtimestamp'] = toUTC(datetime.now()).isoformat()
        newmessage[u'eventsource'] = u'nsm'
        newmessage[u'severity'] = u'INFO'
        newmessage[u'mozdefhostname'] = self.mozdefhostname

        if 'details' in newmessage:
            newmessage[u'details'][u'sourceipaddress'] = "0.0.0.0"
            newmessage[u'details'][u'destinationipaddress'] = "0.0.0.0"
            newmessage[u'details'][u'sourceport'] = 0
            newmessage[u'details'][u'destinationport'] = 0
            if 'alert' in newmessage[u'details']:
                newmessage[u'details'][u'suricata_alert'] = newmessage[u'details'][u'alert']
                del(newmessage[u'details'][u'alert'])
            if 'src_ip' in newmessage['details']:
                newmessage[u'details'][u'sourceipaddress'] = newmessage['details']['src_ip']
                del(newmessage['details']['src_ip'])
            if 'src_port' in newmessage['details']:
                newmessage[u'details'][u'sourceport'] = newmessage['details']['src_port']
                del(newmessage['details']['src_port'])
            if 'dest_ip' in newmessage['details']:
                newmessage[u'details'][u'destinationipaddress'] = newmessage['details']['dest_ip']
                del(newmessage['details']['dest_ip'])
            if 'dest_port' in newmessage['details']:
                newmessage[u'details'][u'destinationport'] = newmessage['details']['dest_port']
                del(newmessage['details']['dest_port'])

            if 'file_name' in newmessage['details']:
                del(newmessage['details']['file_name'])
            if 'message' in newmessage['details']:
                del(newmessage['details']['message'])
            if 'source' in newmessage['details']:
                del(newmessage['details']['source'])

            if logtype == 'eve-log':
                if eventtype == 'alert':
                    # Truncate packet, payload and payload_printable to reasonable sizes
                    if 'packet' in newmessage[u'details']:
                        newmessage[u'details'][u'packet'] = newmessage[u'details'][u'packet'][0:4095]
                    if 'payload' in newmessage[u'details']:
                        newmessage[u'details'][u'payload'] = newmessage[u'details'][u'payload'][0:4095]
                    if 'payload_printable' in newmessage[u'details']:
                        newmessage[u'details'][u'payload_printable'] = newmessage[u'details'][u'payload_printable'][0:4095]
                    # Match names to Bro
                    newmessage[u'details'][u'originipbytes'] = 0
                    newmessage[u'details'][u'responseipbytes'] = 0
                    newmessage[u'details'][u'orig_pkts'] = 0
                    newmessage[u'details'][u'resp_pkts'] = 0
                    if 'flow' in newmessage[u'details']:
                        if 'bytes_toserver' in newmessage[u'details'][u'flow']:
                            newmessage[u'details'][u'originipbytes'] = newmessage['details']['flow']['bytes_toserver']
                            del(newmessage['details']['flow']['bytes_toserver'])
                        if 'bytes_toclient' in newmessage[u'details'][u'flow']:
                            newmessage[u'details'][u'responseipbytes'] = newmessage['details']['flow']['bytes_toclient']
                            del(newmessage['details']['flow']['bytes_toclient'])
                        if 'pkts_toserver' in newmessage[u'details'][u'flow']:
                            newmessage[u'details'][u'orig_pkts'] = newmessage['details']['flow']['pkts_toserver']
                            del(newmessage['details']['flow']['pkts_toserver'])
                        if 'pkts_toclient' in newmessage[u'details'][u'flow']:
                            newmessage[u'details'][u'resp_pkts'] = newmessage['details']['flow']['pkts_toclient']
                            del(newmessage['details']['flow']['pkts_toclient'])
                    if 'http' in newmessage[u'details']:
                        if 'hostname' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'host'] = newmessage[u'details'][u'http'][u'hostname']
                            del(newmessage[u'details'][u'http'][u'hostname'])
                        if 'http_method' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'method'] = newmessage[u'details'][u'http'][u'http_method']
                            del(newmessage[u'details'][u'http'][u'http_method'])
                        if 'http_user_agent' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'user_agent'] = newmessage[u'details'][u'http'][u'http_user_agent']
                            del(newmessage[u'details'][u'http'][u'http_user_agent'])
                        if 'status' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'status_code'] = newmessage[u'details'][u'http'][u'status']
                            del(newmessage[u'details'][u'http'][u'status'])
                        if 'url' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'uri'] = newmessage[u'details'][u'http'][u'url']
                            del(newmessage[u'details'][u'http'][u'url'])
                        if 'redirect' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'redirect_dst'] = newmessage[u'details'][u'http'][u'redirect']
                            del(newmessage[u'details'][u'http'][u'redirect'])
                        if 'length' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'request_body_len'] = newmessage[u'details'][u'http'][u'length']
                            del(newmessage[u'details'][u'http'][u'length'])
                        if 'http_response_body' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'http_response_body'] = newmessage[u'details'][u'http'][u'http_response_body'][0:4095]
                            del(newmessage[u'details'][u'http'][u'http_response_body'])
                        if 'http_response_body_printable' in newmessage[u'details'][u'http']:
                            newmessage[u'details'][u'http_response_body_printable'] = newmessage[u'details'][u'http'][u'http_response_body_printable'][0:4095]
                            del(newmessage[u'details'][u'http'][u'http_response_body_printable'])
                    if 'app_proto' in newmessage[u'details']:
                        newmessage['details']['service'] = newmessage['details']['app_proto']
                        del(newmessage['details']['app_proto'])
                    # Make sure details.vars.flowbits exceptions are handled
                    if 'vars' in newmessage['details']:
                        if 'flowbits' in newmessage['details']['vars']:
                            if 'ET.http.javaclient' in newmessage['details']['vars']['flowbits']:
                                if 'ET.http.javaclient.vulnerable':
                                    del(newmessage['details']['vars']['flowbits']['ET.http.javaclient'])
                                    newmessage['details']['vars']['flowbits']['ET.http.javaclient.vulnerable'] = "True"
                    newmessage[u'summary'] = (
                        u'{sourceipaddress}:'+
                        u'{sourceport} -> '+
                        u'{destinationipaddress}:'
                        u'{destinationport}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

        return (newmessage, metadata)
