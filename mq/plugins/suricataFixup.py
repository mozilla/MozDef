# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2018 Mozilla Corporation

import json
from datetime import datetime
from platform import node
from mozdef_util.utilities.toUTC import toUTC


class message(object):
    def __init__(self):
        '''
        takes an incoming suricata event
        and parses the message to extract
        data points, and sets the type
        field
        '''

        self.registration = ['suricata']
        self.priority = 5
        try:
            self.mozdefhostname = '{0}'.format(node())
        except:
            self.mozdefhostname = 'failed to fetch mozdefhostname'
            pass

    def onMessage(self, message, metadata):

        # make sure I really wanted to see this message
        # bail out early if not
        if 'customendpoint' not in message:
            return message, metadata
        if 'category' not in message:
            return message, metadata
        if message['category'] != 'suricata':
            return message, metadata

        # move Suricata specific fields under 'details' while preserving metadata
        newmessage = dict()

        # Set NSM as type for categorical filtering of events.
        newmessage["type"] = "nsm"

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
        newmessage['source'] = 'unknown'
        if 'source' in message:
            newmessage['source'] = message['source']
        logtype = newmessage['source']
        newmessage['event_type'] = 'unknown'
        if 'event_type' in message:
            newmessage['event_type'] = message['event_type']
        eventtype = newmessage['event_type']

        # add mandatory fields
        if 'flow' in newmessage['details']:
            if 'start' in newmessage['details']['flow']:
                newmessage['utctimestamp'] = toUTC(newmessage['details']['flow']['start']).isoformat()
                newmessage['timestamp'] = toUTC(newmessage['details']['flow']['start']).isoformat()
        else:
            # a malformed message somehow managed to crawl to us, let's put it somewhat together
            newmessage['utctimestamp'] = toUTC(datetime.now()).isoformat()
            newmessage['timestamp'] = toUTC(datetime.now()).isoformat()

        newmessage['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
        newmessage['eventsource'] = 'nsm'
        newmessage['severity'] = 'INFO'
        newmessage['mozdefhostname'] = self.mozdefhostname

        if 'details' in newmessage:
            newmessage['details']['sourceipaddress'] = "0.0.0.0"
            newmessage['details']['destinationipaddress'] = "0.0.0.0"
            newmessage['details']['sourceport'] = 0
            newmessage['details']['destinationport'] = 0
            if 'alert' in newmessage['details']:
                newmessage['details']['suricata_alert'] = newmessage['details']['alert']
                del(newmessage['details']['alert'])
            if 'src_ip' in newmessage['details']:
                newmessage['details']['sourceipaddress'] = newmessage['details']['src_ip']
                del(newmessage['details']['src_ip'])
            if 'src_port' in newmessage['details']:
                newmessage['details']['sourceport'] = newmessage['details']['src_port']
                del(newmessage['details']['src_port'])
            if 'dest_ip' in newmessage['details']:
                newmessage['details']['destinationipaddress'] = newmessage['details']['dest_ip']
                del(newmessage['details']['dest_ip'])
            if 'dest_port' in newmessage['details']:
                newmessage['details']['destinationport'] = newmessage['details']['dest_port']
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
                    if 'packet' in newmessage['details']:
                        newmessage['details']['packet'] = newmessage['details']['packet'][0:4095]
                    if 'payload' in newmessage['details']:
                        newmessage['details']['payload'] = newmessage['details']['payload'][0:4095]
                    if 'payload_printable' in newmessage['details']:
                        newmessage['details']['payload_printable'] = newmessage['details']['payload_printable'][0:4095]
                    # Match names to Bro
                    newmessage['details']['originipbytes'] = 0
                    newmessage['details']['responseipbytes'] = 0
                    newmessage['details']['orig_pkts'] = 0
                    newmessage['details']['resp_pkts'] = 0
                    if 'flow' in newmessage['details']:
                        if 'bytes_toserver' in newmessage['details']['flow']:
                            newmessage['details']['originipbytes'] = newmessage['details']['flow']['bytes_toserver']
                            del(newmessage['details']['flow']['bytes_toserver'])
                        if 'bytes_toclient' in newmessage['details']['flow']:
                            newmessage['details']['responseipbytes'] = newmessage['details']['flow']['bytes_toclient']
                            del(newmessage['details']['flow']['bytes_toclient'])
                        if 'pkts_toserver' in newmessage['details']['flow']:
                            newmessage['details']['orig_pkts'] = newmessage['details']['flow']['pkts_toserver']
                            del(newmessage['details']['flow']['pkts_toserver'])
                        if 'pkts_toclient' in newmessage['details']['flow']:
                            newmessage['details']['resp_pkts'] = newmessage['details']['flow']['pkts_toclient']
                            del(newmessage['details']['flow']['pkts_toclient'])
                    if 'http' in newmessage['details']:
                        if 'hostname' in newmessage['details']['http']:
                            newmessage['details']['host'] = newmessage['details']['http']['hostname']
                            del(newmessage['details']['http']['hostname'])
                        if 'http_method' in newmessage['details']['http']:
                            newmessage['details']['method'] = newmessage['details']['http']['http_method']
                            del(newmessage['details']['http']['http_method'])
                        if 'http_user_agent' in newmessage['details']['http']:
                            newmessage['details']['user_agent'] = newmessage['details']['http']['http_user_agent']
                            del(newmessage['details']['http']['http_user_agent'])
                        if 'status' in newmessage['details']['http']:
                            newmessage['details']['status_code'] = newmessage['details']['http']['status']
                            del(newmessage['details']['http']['status'])
                        if 'url' in newmessage['details']['http']:
                            newmessage['details']['uri'] = newmessage['details']['http']['url']
                            del(newmessage['details']['http']['url'])
                        if 'redirect' in newmessage['details']['http']:
                            newmessage['details']['redirect_dst'] = newmessage['details']['http']['redirect']
                            del(newmessage['details']['http']['redirect'])
                        if 'length' in newmessage['details']['http']:
                            newmessage['details']['request_body_len'] = newmessage['details']['http']['length']
                            del(newmessage['details']['http']['length'])
                        if 'http_response_body' in newmessage['details']['http']:
                            newmessage['details']['http_response_body'] = newmessage['details']['http']['http_response_body'][0:4095]
                            del(newmessage['details']['http']['http_response_body'])
                        if 'http_response_body_printable' in newmessage['details']['http']:
                            newmessage['details']['http_response_body_printable'] = newmessage['details']['http']['http_response_body_printable'][0:4095]
                            del(newmessage['details']['http']['http_response_body_printable'])
                    if 'app_proto' in newmessage['details']:
                        newmessage['details']['service'] = newmessage['details']['app_proto']
                        del(newmessage['details']['app_proto'])
                    if 'email' in newmessage['details'] and type(newmessage['details']['email']) == dict:
                        # If smtp info is already defined, just delete the email list
                        if 'smtp' in newmessage['details']:
                            del(newmessage['details']['email'])
                    # Make sure details.vars.flowbits exceptions are handled
                    if 'vars' in newmessage['details']:
                        if 'flowbits' in newmessage['details']['vars']:
                            if 'ET.http.javaclient' in newmessage['details']['vars']['flowbits']:
                                if 'ET.http.javaclient.vulnerable':
                                    del(newmessage['details']['vars']['flowbits']['ET.http.javaclient'])
                                    newmessage['details']['vars']['flowbits']['ET.http.javaclient.vulnerable'] = "True"
                    newmessage['summary'] = (
                        '{sourceipaddress}:'+
                        '{sourceport} -> '+
                        '{destinationipaddress}:'
                        '{destinationport}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

        return (newmessage, metadata)
