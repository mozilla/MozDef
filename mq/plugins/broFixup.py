# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import netaddr
from utilities.toUTC import toUTC
from datetime import datetime
from platform import node


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


def isIPv6(ip):
    try:
        return netaddr.valid_ipv6(ip)
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
        try:
            self.mozdefhostname = u'{0}'.format(node())
        except:
            self.mozdefhostname = 'failed to fetch mozdefhostname'
            pass


    def onMessage(self, message, metadata):

        # make sure I really wanted to see this message
        # bail out early if not
        if u'customendpoint' not in message:
            #message['customendpoint'] = ''
            return message, metadata
        if u'category' not in message:
            #message['category'] = 'DUPA'
            return message, metadata
        if u'source' not in message:
            #message['source'] = 'conn'
            return message, metadata
        if message['category'] != 'bro':
            return message, metadata

        # set the doc type to bro
        # to avoid data type conflicts with other doc types
        # (int v string, etc)
        # index holds documents of type 'type'
        # index -> type -> doc
        metadata['doc_type']= 'nsm'

        # move Bro specific fields under 'details' while preserving metadata
        newmessage = dict()

        newmessage['details'] = message

        newmessage['customendpoint'] = 'bro'
        # move some fields that are expected at the event 'root' where they belong
        if 'host' in newmessage['details']:
            newmessage['hostname'] = newmessage['details']['host']
            del(newmessage['details']['host'])
        if 'tags' in newmessage['details']:
            newmessage['tags'] = newmessage['details']['tags']
            del(newmessage['details']['tags'])
        if 'category' in newmessage['details']:
            newmessage['category'] = newmessage['details']['category']
            del(newmessage['details']['category'])
        if 'customendpoint' in newmessage['details']:
            del(newmessage['details']['customendpoint'])
        if 'source' in newmessage['details']:
            newmessage['source'] = newmessage['details']['source']
            del(newmessage['details']['source'])

        # add mandatory fields
        if 'ts' in newmessage['details']:
            newmessage[u'utctimestamp'] = toUTC(float(newmessage['details']['ts'])).isoformat()
            newmessage[u'timestamp'] = toUTC(float(newmessage['details']['ts'])).isoformat()
        else:
            # a malformed message somehow managed to crawl to us, let's put it somewhat together
            newmessage[u'utctimestamp'] = toUTC(datetime.now()).isoformat()
            newmessage[u'timestamp'] = toUTC(datetime.now()).isoformat()

        newmessage[u'receivedtimestamp'] = toUTC(datetime.now()).isoformat()
        newmessage[u'eventsource'] = u'nsm'
        newmessage[u'severity'] = u'INFO'
        newmessage[u'mozdefhostname'] = self.mozdefhostname

        if 'orig_h' in newmessage['details']['id']:
            newmessage[u'details'][u'sourceipaddress'] = newmessage['details']['id']['orig_h']
            del(newmessage['details']['id']['orig_h'])
        if 'orig_p' in newmessage['details']['id']:
            newmessage[u'details'][u'sourceport'] = newmessage['details']['id']['orig_p']
            del(newmessage['details']['id']['orig_p'])
        if 'resp_h' in newmessage['details']['id']:
            newmessage[u'details'][u'destinationipaddress'] = newmessage['details']['id']['resp_h']
            del(newmessage['details']['id']['resp_h'])
        if 'resp_p' in newmessage['details']['id']:
            newmessage[u'details'][u'destinationport'] = newmessage['details']['id']['resp_p']
            del(newmessage['details']['id']['resp_p'])


        # re-arrange the position of some fields
        # {} vs {'details':{}}
        if 'details' in newmessage:

            # All Bro logs need special treatment, so we provide it
            # Not a known log source? Mark it as such and return
            if 'source' not in newmessage:
                newmessage['source'] = u'unknown'
                return newmessage, metadata
            else:
                logtype = newmessage['source']

                if logtype == 'conn':
                    newmessage[u'details'][u'originipbytes'] = newmessage['details']['orig_ip_bytes']
                    newmessage[u'details'][u'responseipbytes'] = newmessage['details']['resp_ip_bytes']
                    del(newmessage['details']['orig_ip_bytes'])
                    del(newmessage['details']['resp_ip_bytes'])
                    if 'history' not in newmessage['details']:
                        newmessage['details'][u'history'] = ''
                    newmessage[u'summary'] = (
                        u'{sourceipaddress}:'+
                        u'{sourceport} -> '+
                        u'{destinationipaddress}:'
                        u'{destinationport} '+
                        u'{history} '+
                        u'{originipbytes} bytes / '
                        u'{responseipbytes} bytes'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'files':
                    if 'rx_hosts' in newmessage['details']:
                        newmessage['details'][u'sourceipaddress'] = u'{0}'.format(newmessage['details']['rx_hosts'][0])
                    if 'tx_hosts' in newmessage['details']:
                        newmessage['details'][u'destinationipaddress'] = u'{0}'.format(newmessage['details']['tx_hosts'][0])
                    if 'mime_type' not in newmessage['details']:
                        newmessage['details'][u'mime_type'] = u'unknown'
                    if 'filename' not in newmessage['details']:
                        newmessage['details'][u'filename'] = u'unknown'
                    if 'total_bytes' not in newmessage['details']:
                        newmessage['details'][u'total_bytes'] = u'0'
                    if 'md5' not in newmessage['details']:
                        newmessage['details'][u'md5'] = u'None'
                    if 'filesource' not in newmessage['details']:
                        newmessage['details'][u'filesource'] = u'None'
                    newmessage[u'summary'] = (
                        u'{rx_hosts[0]} '
                        u'downloaded (MD5) '
                        u'{md5} '
                        u'filename {filename} '
                        u'MIME {mime_type} '
                        u'({total_bytes} bytes) '
                        u'from {tx_hosts[0]} '
                        u'via {filesource}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'dns':
                    if 'qtype_name' not in newmessage['details']:
                        newmessage['details'][u'qtype_name'] = u''
                    if 'query' not in newmessage['details']:
                        newmessage['details'][u'query'] = u''
                    if 'rcode_name' not in newmessage['details']:
                        newmessage['details'][u'rcode_name'] = u''
                    newmessage[u'summary'] = (
                        u'{sourceipaddress} -> '
                        u'{destinationipaddress}:{destinationport} '
                        u'{qtype_name} '
                        u'{query} '
                        u'{rcode_name}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'http':
                    if 'method' not in newmessage['details']:
                        newmessage['details'][u'method'] = u''
                    if 'host' not in newmessage['details']:
                        newmessage['details'][u'host'] = u''
                    if 'uri' not in newmessage['details']:
                        newmessage['details'][u'uri'] = u''
                    if 'status_code' not in newmessage['details']:
                        newmessage['details'][u'status_code'] = u''
                    newmessage[u'summary'] = (
                        u'{method} '
                        u'{host} '
                        u'{uri} '
                        u'{status_code}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'ssl':
                    if 'server_name' not in newmessage['details']:
                        # fake it till you make it
                        newmessage['details'][u'server_name'] = newmessage['details']['destinationipaddress']
                    newmessage[u'summary'] = (
                        u'SSL: {sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'{server_name}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'dhcp':
                    newmessage[u'summary'] = (
                        '{assigned_ip} assigned to '
                        '{mac}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'ftp':
                    if 'command' not in newmessage['details']:
                        newmessage['details'][u'command'] = u''
                    if 'user' not in newmessage['details']:
                        newmessage['details'][u'user'] = u''
                    newmessage[u'summary'] = (
                        u'FTP: {sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'{command} '
                        u'{user}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'pe':
                    if 'os' not in newmessage['details']:
                        newmessage['details']['os'] = ''
                    if 'subsystem' not in newmessage['details']:
                        newmessage['details']['subsystem'] = ''
                    newmessage[u'summary'] = (
                        u'PE file: {os} '
                        u'{subsystem}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'smtp':
                    if 'from' in newmessage['details']:
                        from_decoded = newmessage['details'][u'from'].decode('unicode-escape')
                        newmessage['details'][u'from'] = from_decoded
                    else:
                        newmessage['details'][u'from'] = u''
                    if 'to' not in newmessage['details']:
                        newmessage['details'][u'to'] = [u'']
                    if 'msg_id' not in newmessage['details']:
                        newmessage['details'][u'msg_id'] = u''
                    newmessage[u'summary'] = (
                        u'SMTP: {sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'from {from} '
                        u'to '
                        u'{to[0]} '
                        u'ID {msg_id}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'ssh':
                    if 'auth_success' not in newmessage['details']:
                        newmessage['details'][u'auth_success'] = u'unknown'
                    newmessage[u'summary'] = (
                        u'SSH: {sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'success {auth_success}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'tunnel':
                    if 'tunnel_type' not in newmessage['details']:
                        newmessage['details'][u'tunnel_type'] = u''
                    if 'action' not in newmessage['details']:
                        newmessage['details'][u'action'] = u''
                    newmessage[u'summary'] = (
                        u'{sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'{tunnel_type} '
                        u'{action}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'intel':
                    if 'seenindicator' not in newmessage['details']:
                        newmessage['details'][u'seenindicator'] = u''
                    newmessage[u'summary'] = (
                        u'Bro intel match: '
                        u'{seenindicator}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'knowncerts':
                    if 'serial' not in newmessage['details']:
                        newmessage['details'][u'serial'] = u'0'
                    newmessage[u'summary'] = (
                        u'Certificate seen from: '
                        u'{host}:'
                        u'{port_num} '
                        u'serial {serial}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'knowndevices':
                    if 'mac' not in newmessage['details']:
                        newmessage['details'][u'mac'] = u''
                    if 'dhcp_host_name' not in newmessage['details']:
                        newmessage['details'][u'dhcp_host_name'] = u''
                    newmessage[u'summary'] = (
                        u'New host: '
                        u'{mac} '
                        u'{dhcp_host_name}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'knownhosts':
                    if 'host' not in newmessage['details']:
                        newmessage['details'][u'host'] = u''
                    newmessage[u'summary'] = (
                        u'New host: '
                        u'{host}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'knownservices':
                    if 'service' not in newmessage['details']:
                        newmessage['details']['service'] = []
                    if not newmessage['details']['service']:
                        newmessage['details'][u'service'] = [u'Unknown']
                    if 'host' not in newmessage['details']:
                        newmessage['details'][u'host'] = u'unknown'
                    if 'port_num' not in newmessage['details']:
                        newmessage['details'][u'port_num'] = u'0'
                    if 'port_proto' not in newmessage['details']:
                        newmessage['details'][u'port_proto'] = u''
                    newmessage[u'summary'] = (
                        u'New service: '
                        u'{service[0]} '
                        u'on host '
                        u'{host}:'
                        u'{port_num} / '
                        u'{port_proto}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'notice':
                    newmessage['details'][u'indicators'] = []
                    if 'sub' not in newmessage['details']:
                        newmessage['details'][u'sub'] = u''
                    if 'msg' not in newmessage['details']:
                        newmessage['details'][u'msg'] = u''
                    if 'note' not in newmessage['details']:
                        newmessage['details'][u'note'] = u''
                    newmessage[u'summary'] = (
                        u'{note} '
                        u'{msg} '
                        u'{sub}'
                    ).format(**newmessage['details'])
                    # clean up the action notice IP addresses
                    if 'actions' in newmessage['details']:
                        if newmessage['details']['actions'] == "Notice::ACTION_LOG":
                            # retrieve indicator ip addresses from the sub field
                            # "sub": "Indicator: 1.2.3.4, Indicator: 5.6.7.8"
                            newmessage['details']['indicators'] = [ip for ip
                                in findIPv4(newmessage['details']['sub'])]
                    # remove the details.src field and add it to indicators
                    # as it may not be the actual source.
                    if 'src' in newmessage['details']:
                        if isIPv4(newmessage[u'details'][u'src']):
                            newmessage[u'details'][u'indicators'].append(newmessage[u'details'][u'src'])
                            # If details.src is present overwrite the source IP address with it
                            newmessage[u'details'][u'sourceipaddress'] = newmessage[u'details'][u'src']
                            newmessage[u'details'][u'sourceipv4address'] = newmessage[u'details'][u'src']
                        if isIPv6(newmessage[u'details'][u'src']):
                            newmessage[u'details'][u'indicators'].append(newmessage[u'details'][u'src'])
                            # If details.src is present overwrite the source IP address with it
                            newmessage[u'details'][u'sourceipv6address'] = newmessage[u'details'][u'src']
                        # Thank you for your service
                        del newmessage[u'details'][u'src']
                    return (newmessage, metadata)

                if logtype == 'rdp':
                    if 'cookie' not in newmessage['details']:
                        newmessage['details'][u'cookie'] = u'unknown'
                    newmessage[u'summary'] = (
                        u'RDP: {sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'cookie {cookie}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'sip':
                    if 'status_msg' not in newmessage['details']:
                        newmessage['details'][u'status_msg'] = u'unknown'
                    if 'uri' not in newmessage['details']:
                        newmessage['details'][u'uri'] = u'unknown'
                    if 'method' not in newmessage['details']:
                        newmessage['details'][u'method'] = u'unknown'
                    newmessage[u'summary'] = (
                        u'SIP: {sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'method {method} '
                        u'uri {uri} '
                        u'status {status_msg}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'software':
                    if 'name' not in newmessage['details']:
                        newmessage['details'][u'name'] = u'unparsed'
                    if 'software_type' not in newmessage['details']:
                        newmessage['details'][u'software_type'] = u'unknown software'
                    if 'host' not in newmessage['details']:
                        newmessage['details'] = u''
                    newmessage[u'summary'] = (
                        u'Found {software_type} '
                        u'name {name} '
                        u'on {host}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'socks':
                    if 'version' not in newmessage['details']:
                        newmessage['details'][u'version'] = u'0'
                    if 'status' not in newmessage['details']:
                        newmessage['details'][u'status'] = u'unknown'
                    newmessage[u'summary'] = (
                        u'SOCKSv{version}: '
                        u'{sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'status {status}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'dcerpc':
                    if 'endpoint' not in newmessage['details']:
                        newmessage['details'][u'endpoint'] = u'unknown'
                    if 'operation' not in newmessage['details']:
                        newmessage['details'][u'operation'] = u'unknown'
                    newmessage[u'summary'] = (
                        u'DCERPC: {sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'endpoint {endpoint} '
                        u'operation {operation}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'kerberos':
                    if 'request_type' not in newmessage['details']:
                        newmessage['details'][u'request_type'] = u'unknown'
                    if 'client' not in newmessage['details']:
                        newmessage['details'][u'client'] = u'unknown'
                    if 'service' not in newmessage['details']:
                        newmessage['details'][u'service'] = u'unknown'
                    if 'success' not in newmessage['details']:
                        newmessage['details'][u'success'] = u'unknown'
                    if 'error_msg' not in newmessage['details']:
                        newmessage['details'][u'error_msg'] = u''
                    newmessage[u'summary'] = (
                        u'{sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'client {client} '
                        u'request {request_type} '
                        u'service {service} '
                        u'success {success} '
                        u'{error_msg}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'ntlm':
                    if 'ntlmdomainname' not in newmessage['details']:
                        newmessage['details'][u'ntlmdomainname'] = u'unknown'
                    if 'ntlmhostname' not in newmessage['details']:
                        newmessage['details'][u'ntlmhostname'] = u'unknown'
                    if 'ntlmusername' not in newmessage['details']:
                        newmessage['details'][u'ntlmusername'] = u'unknown'
                    if 'success' not in newmessage['details']:
                        newmessage['details'][u'success'] = u'unknown'
                    if 'status' not in newmessage['details']:
                        newmessage['details'][u'status'] = u'unknown'
                    newmessage[u'summary'] = (
                        u'NTLM: {sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'user {ntlmusername} '
                        u'host {ntlmhostname} '
                        u'domain {ntlmdomainname} '
                        u'success {success} '
                        u'status {status}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'smbfiles':
                    if 'path' not in newmessage['details']:
                        newmessage['details'][u'path'] = u''
                    if 'name' not in newmessage['details']:
                        newmessage['details'][u'name'] = u''
                    if 'action' not in newmessage['details']:
                        newmessage['details'][u'action'] = u''
                    newmessage[u'summary'] = (
                        'SMB file: '
                        u'{sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'{action}'
                    ).format(**newmessage['details'])
                    return(newmessage, metadata)

                if logtype == 'smbmapping':
                    if 'share_type' not in newmessage['details']:
                        newmessage['details'][u'share_type'] = u''
                    if 'path' not in newmessage['details']:
                        newmessage['details'][u'path'] = u''
                    newmessage[u'summary'] = (
                        'SMB mapping: '
                        u'{sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'{share_type}'
                    ).format(**newmessage['details'])
                    return(newmessage, metadata)

                if logtype == 'snmp':
                    if 'version' not in newmessage['details']:
                        newmessage['details'][u'version'] = u'Unknown'
                    if 'get_bulk_requests' not in newmessage['details']:
                        newmessage['details']['get_bulk_requests'] = 0
                    if 'get_requests' not in newmessage['details']:
                        newmessage['details']['get_requests'] = 0
                    if 'set_requests' not in newmessage['details']:
                        newmessage['details']['set_requests'] = 0
                    if 'get_responses' not in newmessage['details']:
                        newmessage['details']['get_responses'] = 0
                    newmessage['details']['getreqestssum'] = u'{0}'.format(newmessage['details']['get_bulk_requests'] + newmessage['details']['get_requests'])
                    newmessage[u'summary'] = (
                        u'SNMPv{version}: '
                        u'{sourceipaddress} -> '
                        u'{destinationipaddress}:'
                        u'{destinationport} '
                        u'({getreqestssum} get / '
                        u'{set_requests} set requests '
                        u'{get_responses} get responses)'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'x509':
                    if 'certificateserial' not in newmessage['details']:
                        newmessage['details'][u'certificateserial'] = u'0'
                    newmessage[u'summary'] = (
                        'Certificate seen serial {certificateserial}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)


        return (newmessage, metadata)
