# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import netaddr
import json
from datetime import datetime
from platform import node
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.key_exists import key_exists


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
        and parses it to extract data
        points and sets the type field
        '''

        self.registration = ['bro']
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
        if 'SOURCE' not in message:
            return message, metadata
        if message['category'] != 'bro':
            return message, metadata

        # move Bro specific fields under 'details' while preserving metadata
        newmessage = dict()

        # default replacement for old _type subcategory.
        # to preserve filtering capabilities
        newmessage['type']= 'nsm'

        try:
            newmessage['details'] = json.loads(message['MESSAGE'])
        except:
            newmessage['details'] = {}
            newmessage['rawdetails'] = message

        newmessage['customendpoint'] = 'bro'
        # move some fields that are expected at the event 'root' where they belong
        if 'HOST_FROM' in message:
            newmessage['hostname'] = message['HOST_FROM']
        if 'tags' in message:
            newmessage['tags'] = message['tags']
        if 'category' in message:
            newmessage['category'] = message['category']
        if 'SOURCE' in message:
            # transform bro_files into files fast
            newmessage['source'] = message['SOURCE'][4:]
        if 'resp_cc' in newmessage['details']:
            del(newmessage['details']['resp_cc'])

        # add mandatory fields
        if 'ts' in newmessage['details']:
            newmessage['utctimestamp'] = toUTC(float(newmessage['details']['ts'])).isoformat()
            newmessage['timestamp'] = toUTC(float(newmessage['details']['ts'])).isoformat()
            # del(newmessage['details']['ts'])
        else:
            # a malformed message somehow managed to crawl to us, let's put it somewhat together
            newmessage['utctimestamp'] = toUTC(datetime.now()).isoformat()
            newmessage['timestamp'] = toUTC(datetime.now()).isoformat()

        newmessage['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
        newmessage['eventsource'] = 'nsm'
        newmessage['severity'] = 'INFO'
        newmessage['mozdefhostname'] = self.mozdefhostname

        if 'id.orig_h' in newmessage['details']:
            newmessage['details']['sourceipaddress'] = newmessage['details']['id.orig_h']
            del(newmessage['details']['id.orig_h'])
        if 'id.orig_p' in newmessage['details']:
            newmessage['details']['sourceport'] = newmessage['details']['id.orig_p']
            del(newmessage['details']['id.orig_p'])
        if 'id.resp_h' in newmessage['details']:
            newmessage['details']['destinationipaddress'] = newmessage['details']['id.resp_h']
            del(newmessage['details']['id.resp_h'])
        if 'id.resp_p' in newmessage['details']:
            newmessage['details']['destinationport'] = newmessage['details']['id.resp_p']
            del(newmessage['details']['id.resp_p'])

        if 'details' in newmessage:
            if 'FILE_NAME' in newmessage['details']:
                del(newmessage['details']['FILE_NAME'])
            if 'MESSAGE' in newmessage['details']:
                del(newmessage['details']['MESSAGE'])
            if 'SOURCE' in newmessage['details']:
                del(newmessage['details']['SOURCE'])

            # All Bro logs need special treatment, so we provide it
            # Not a known log source? Mark it as such and return
            if 'source' not in newmessage:
                newmessage['source'] = 'unknown'
                return newmessage, metadata
            else:
                logtype = newmessage['source']

                if logtype == 'conn':
                    newmessage['details']['originipbytes'] = newmessage['details']['orig_ip_bytes']
                    newmessage['details']['responseipbytes'] = newmessage['details']['resp_ip_bytes']
                    del(newmessage['details']['orig_ip_bytes'])
                    del(newmessage['details']['resp_ip_bytes'])
                    if 'history' not in newmessage['details']:
                        newmessage['details']['history'] = ''
                    newmessage['summary'] = (
                        '{sourceipaddress}:'+
                        '{sourceport} -> '+
                        '{destinationipaddress}:'
                        '{destinationport} '+
                        '{history} '+
                        '{originipbytes} bytes / '
                        '{responseipbytes} bytes'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'files':
                    if 'rx_hosts' in newmessage['details']:
                        newmessage['details']['sourceipaddress'] = '{0}'.format(newmessage['details']['rx_hosts'][0])
                    if 'tx_hosts' in newmessage['details']:
                        newmessage['details']['destinationipaddress'] = '{0}'.format(newmessage['details']['tx_hosts'][0])
                    if 'mime_type' not in newmessage['details']:
                        newmessage['details']['mime_type'] = 'unknown'
                    if 'filename' not in newmessage['details']:
                        newmessage['details']['filename'] = 'unknown'
                    if 'total_bytes' not in newmessage['details']:
                        newmessage['details']['total_bytes'] = '0'
                    if 'md5' not in newmessage['details']:
                        newmessage['details']['md5'] = 'None'
                    if 'filesource' not in newmessage['details']:
                        newmessage['details']['filesource'] = 'None'
                    newmessage['summary'] = (
                        '{rx_hosts[0]} '
                        'downloaded (MD5) '
                        '{md5} '
                        'MIME {mime_type} '
                        '({total_bytes} bytes) '
                        'from {tx_hosts[0]} '
                        'via {filesource}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'dns':
                    if 'qtype_name' not in newmessage['details']:
                        newmessage['details']['qtype_name'] = 'unknown'
                    if 'query' not in newmessage['details']:
                        newmessage['details']['query'] = ''
                    if 'rcode_name' not in newmessage['details']:
                        newmessage['details']['rcode_name'] = ''
                    newmessage['summary'] = (
                        'DNS {qtype_name} type query '
                        '{sourceipaddress} -> '
                        '{destinationipaddress}:{destinationport}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'http':
                    if 'method' not in newmessage['details']:
                        newmessage['details']['method'] = ''
                    if 'host' not in newmessage['details']:
                        newmessage['details']['host'] = ''
                    if 'uri' not in newmessage['details']:
                        newmessage['details']['uri'] = ''
                    newmessage['details']['uri'] = newmessage['details']['uri'][:1024]
                    if 'status_code' not in newmessage['details']:
                        newmessage['details']['status_code'] = ''
                    newmessage['summary'] = (
                        'HTTP {method} '
                        '{sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'ssl':
                    if 'server_name' not in newmessage['details']:
                        # fake it till you make it
                        newmessage['details']['server_name'] = newmessage['details']['destinationipaddress']
                    newmessage['summary'] = (
                        'SSL: {sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'dhcp':
                    if 'assigned_addr' not in newmessage['details']:
                        newmessage['details']['assigned_addr'] = "0.0.0.0"
                    if 'mac' not in newmessage['details']:
                        newmessage['details']['mac'] = "000000000000"
                    newmessage['details']['mac'] = newmessage['details']['mac'].replace(':', '')
                    newmessage['summary'] = (
                        '{assigned_addr} assigned to '
                        '{mac}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'ftp':
                    if 'command' not in newmessage['details']:
                        newmessage['details']['command'] = ''
                    if 'user' not in newmessage['details']:
                        newmessage['details']['user'] = ''
                    newmessage['summary'] = (
                        'FTP: {sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'pe':
                    if 'os' not in newmessage['details']:
                        newmessage['details']['os'] = ''
                    if 'subsystem' not in newmessage['details']:
                        newmessage['details']['subsystem'] = ''
                    newmessage['summary'] = (
                        'PE file: {os} '
                        '{subsystem}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'smtp':
                    newmessage['summary'] = (
                        'SMTP: {sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport}'
                    ).format(**newmessage['details'])
                    if key_exists('details.tls', newmessage):
                        newmessage['details']['tls_encrypted'] = newmessage['details']['tls']
                        del(newmessage['details']['tls'])
                    return (newmessage, metadata)

                if logtype == 'ssh':
                    summary = (
                        'SSH: {sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport}'
                    ).format(**newmessage['details'])
                    if 'auth_success' in newmessage['details']:
                        summary += ' success {0}'.format(newmessage['details']['auth_success'])
                    newmessage['summary'] = summary
                    return (newmessage, metadata)

                if logtype == 'tunnel':
                    if 'tunnel_type' not in newmessage['details']:
                        newmessage['details']['tunnel_type'] = ''
                    if 'action' not in newmessage['details']:
                        newmessage['details']['action'] = ''
                    newmessage['summary'] = (
                        '{sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport} '
                        '{tunnel_type} '
                        '{action}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'intel':
                    if 'seen.indicator' in newmessage['details']:
                        newmessage['details']['seenindicator'] = newmessage['details']['seen.indicator']
                        del(newmessage['details']['seen.indicator'])
                    else:
                        newmessage['details']['seenindicator'] = ''
                    if 'seen.node' in newmessage['details']:
                        newmessage['details']['seennode'] = newmessage['details']['seen.node']
                        del(newmessage['details']['seen.node'])
                    if 'seen.where' in newmessage['details']:
                        newmessage['details']['seenwhere'] = newmessage['details']['seen.where']
                        del(newmessage['details']['seen.where'])
                    if 'seen.indicator_type' in newmessage['details']:
                        newmessage['details']['seenindicatortype'] = newmessage['details']['seen.indicator_type']
                        del(newmessage['details']['seen.indicator_type'])
                    newmessage['summary'] = (
                        'Bro intel match '
                        'of {seenindicatortype} '
                        'in {seenwhere}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'known_certs':
                    if 'serial' not in newmessage['details']:
                        newmessage['details']['serial'] = '0'
                    newmessage['summary'] = (
                        'Certificate X509 seen from: '
                        '{host}:'
                        '{port_num}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'known_devices':
                    if 'mac' not in newmessage['details']:
                        newmessage['details']['mac'] = ''
                    if 'dhcp_host_name' not in newmessage['details']:
                        newmessage['details']['dhcp_host_name'] = ''
                    newmessage['summary'] = (
                        'New host: '
                        '{mac}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'known_hosts':
                    if 'host' not in newmessage['details']:
                        newmessage['details']['host'] = ''
                    newmessage['summary'] = (
                        'New host: '
                        '{host}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'known_services':
                    if 'service' not in newmessage['details']:
                        newmessage['details']['service'] = []
                    if not newmessage['details']['service']:
                        newmessage['details']['service'] = ['Unknown']
                    if 'host' not in newmessage['details']:
                        newmessage['details']['host'] = 'unknown'
                    if 'port_num' not in newmessage['details']:
                        newmessage['details']['port_num'] = '0'
                    if 'port_proto' not in newmessage['details']:
                        newmessage['details']['port_proto'] = ''
                    newmessage['summary'] = (
                        'New service: '
                        '{service[0]} '
                        'on host '
                        '{host}:'
                        '{port_num} / '
                        '{port_proto}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'notice':
                    newmessage['details']['indicators'] = []
                    if 'sub' not in newmessage['details']:
                        newmessage['details']['sub'] = ''
                    if 'msg' not in newmessage['details']:
                        newmessage['details']['msg'] = ''
                    if 'note' not in newmessage['details']:
                        newmessage['details']['note'] = ''
                    # clean up the action notice IP addresses
                    if 'actions' in newmessage['details']:
                        if newmessage['details']['actions'] == "Notice::ACTION_LOG":
                            # retrieve indicator ip addresses from the sub field
                            # "sub": "Indicator: 1.2.3.4, Indicator: 5.6.7.8"
                            newmessage['details']['indicators'] = [ip for ip in findIPv4(newmessage['details']['sub'])]
                    # remove the details.src field and add it to indicators
                    # as it may not be the actual source.
                    if 'src' in newmessage['details']:
                        if isIPv4(newmessage['details']['src']):
                            newmessage['details']['indicators'].append(newmessage['details']['src'])
                            # If details.src is present overwrite the source IP address with it
                            newmessage['details']['sourceipaddress'] = newmessage['details']['src']
                            newmessage['details']['sourceipv4address'] = newmessage['details']['src']
                        if isIPv6(newmessage['details']['src']):
                            newmessage['details']['indicators'].append(newmessage['details']['src'])
                            # If details.src is present overwrite the source IP address with it
                            newmessage['details']['sourceipv6address'] = newmessage['details']['src']
                        del newmessage['details']['src']
                    sumstruct = {}
                    sumstruct['note'] = newmessage['details']['note']
                    if 'sourceipv6address' in newmessage['details']:
                        sumstruct['src'] = newmessage['details']['sourceipv6address']
                    else:
                        if 'sourceipv4address' in newmessage['details']:
                            sumstruct['src'] = newmessage['details']['sourceipv4address']
                        else:
                            sumstruct['src'] = 'unknown'
                    if 'dst' in newmessage['details']:
                        sumstruct['dst'] = newmessage['details']['dst']
                        del(newmessage['details']['dst'])
                        if isIPv4(sumstruct['dst']):
                            newmessage['details']['destinationipaddress'] = sumstruct['dst']
                            newmessage['details']['destinationipv4address'] = sumstruct['dst']
                        if isIPv6(sumstruct['dst']):
                            newmessage['details']['destinationipv6address'] = sumstruct['dst']
                    else:
                        sumstruct['dst'] = 'unknown'
                    if 'p' in newmessage['details']:
                        sumstruct['p'] = newmessage['details']['p']
                    else:
                        sumstruct['p'] = 'unknown'
                    newmessage['summary'] = (
                        '{note} '
                        'source {src} '
                        'destination {dst} '
                        'port {p}'
                    ).format(**sumstruct)
                    # Thank you for your service
                    return (newmessage, metadata)

                if logtype == 'rdp':
                    if 'cookie' not in newmessage['details']:
                        newmessage['details']['cookie'] = 'unknown'
                    newmessage['summary'] = (
                        'RDP: {sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'sip':
                    if 'status_msg' not in newmessage['details']:
                        newmessage['details']['status_msg'] = 'unknown'
                    if 'uri' not in newmessage['details']:
                        newmessage['details']['uri'] = 'unknown'
                    if 'method' not in newmessage['details']:
                        newmessage['details']['method'] = 'unknown'
                    newmessage['summary'] = (
                        'SIP: {sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport} '
                        'method {method} '
                        'status {status_msg}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'software':
                    newmessage['details']['parsed_version'] = {}
                    if 'name' not in newmessage['details']:
                        newmessage['details']['name'] = 'unparsed'
                    if 'software_type' not in newmessage['details']:
                        newmessage['details']['software_type'] = 'unknown'
                    if 'host' not in newmessage['details']:
                        newmessage['details'] = ''
                    if 'version.addl' in newmessage['details']:
                        newmessage['details']['parsed_version']['addl'] = newmessage['details']['version.addl']
                        del(newmessage['details']['version.addl'])
                    if 'version.major' in newmessage['details']:
                        newmessage['details']['parsed_version']['major'] = newmessage['details']['version.major']
                        del(newmessage['details']['version.major'])
                    if 'version.minor' in newmessage['details']:
                        newmessage['details']['parsed_version']['minor'] = newmessage['details']['version.minor']
                        del(newmessage['details']['version.minor'])
                    if 'version.minor2' in newmessage['details']:
                        newmessage['details']['parsed_version']['minor2'] = newmessage['details']['version.minor2']
                        del(newmessage['details']['version.minor2'])
                    if 'version.minor3' in newmessage['details']:
                        newmessage['details']['parsed_version']['minor3'] = newmessage['details']['version.minor3']
                        del(newmessage['details']['version.minor3'])
                    newmessage['summary'] = (
                        'Found {software_type} software '
                        'on {host}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'socks':
                    if 'version' not in newmessage['details']:
                        newmessage['details']['version'] = '0'
                    if 'status' not in newmessage['details']:
                        newmessage['details']['status'] = 'unknown'
                    newmessage['summary'] = (
                        'SOCKSv{version}: '
                        '{sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport} '
                        'status {status}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'dce_rpc':
                    if 'endpoint' not in newmessage['details']:
                        newmessage['details']['endpoint'] = 'unknown'
                    if 'operation' not in newmessage['details']:
                        newmessage['details']['operation'] = 'unknown'
                    newmessage['summary'] = (
                        'DCERPC: {sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport}'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'kerberos':
                    if 'request_type' not in newmessage['details']:
                        newmessage['details']['request_type'] = 'unknown'
                    if 'client' not in newmessage['details']:
                        newmessage['details']['client'] = 'unknown'
                    if 'service' not in newmessage['details']:
                        newmessage['details']['service'] = 'unknown'
                    if 'error_msg' not in newmessage['details']:
                        newmessage['details']['error_msg'] = ''
                    newmessage['summary'] = (
                        '{sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport} '
                        'request {request_type}'
                    ).format(**newmessage['details'])
                    if 'success' in newmessage['details']:
                        newmessage['summary'] += ' success {0}'.format(newmessage['details']['success'])
                    else:
                        newmessage['summary'] += ' success unknown'
                    return (newmessage, metadata)

                if logtype == 'ntlm':
                    newmessage['details']['ntlm'] = {}
                    if 'domainname' in newmessage['details']:
                        newmessage['details']['ntlm']['domainname'] = newmessage['details']['domainname']
                        del(newmessage['details']['domainname'])
                    else:
                        newmessage['details']['ntlm']['domainname'] = 'unknown'
                    if 'hostname' in newmessage['details']:
                        newmessage['details']['ntlm']['hostname'] = newmessage['details']['hostname']
                        del(newmessage['details']['hostname'])
                    else:
                        newmessage['details']['ntlm']['hostname'] = 'unknown'
                    if 'username' in newmessage['details']:
                        newmessage['details']['ntlm']['username'] = newmessage['details']['username']
                        del(newmessage['details']['username'])
                    else:
                        newmessage['details']['ntlm']['username'] = 'unknown'
                    if 'status' not in newmessage['details']:
                        newmessage['details']['status'] = 'unknown'
                    newmessage['summary'] = (
                        'NTLM: {sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport} '
                    ).format(**newmessage['details'])
                    if 'success' in newmessage['details']:
                        newmessage['summary'] += 'success {0} status {1}'.format(newmessage['details']['success'],newmessage['details']['status'])
                    else:
                        newmessage['summary'] += 'success unknown status {0}'.format(newmessage['details']['status'])
                    return (newmessage, metadata)

                if logtype == 'smb_files':
                    newmessage['details']['smbtimes'] = {}
                    if 'path' not in newmessage['details']:
                        newmessage['details']['path'] = ''
                    if 'name' not in newmessage['details']:
                        newmessage['details']['name'] = ''
                    if 'action' not in newmessage['details']:
                        newmessage['details']['action'] = ''
                    if 'times.accessed' in newmessage['details']:
                        newmessage['details']['smbtimes']['accessed'] = toUTC(float(newmessage['details']['times.accessed'])).isoformat()
                        del(newmessage['details']['times.accessed'])
                    if 'times.changed' in newmessage['details']:
                        newmessage['details']['smbtimes']['changed'] = toUTC(float(newmessage['details']['times.changed'])).isoformat()
                        del(newmessage['details']['times.changed'])
                    if 'times.created' in newmessage['details']:
                        newmessage['details']['smbtimes']['created'] = toUTC(float(newmessage['details']['times.created'])).isoformat()
                        del(newmessage['details']['times.created'])
                    if 'times.modified' in newmessage['details']:
                        newmessage['details']['smbtimes']['modified'] = toUTC(float(newmessage['details']['times.modified'])).isoformat()
                        del(newmessage['details']['times.modified'])
                    newmessage['summary'] = (
                        'SMB file: '
                        '{sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport} '
                        '{action}'
                    ).format(**newmessage['details'])
                    return(newmessage, metadata)

                if logtype == 'smb_mapping':
                    if 'share_type' not in newmessage['details']:
                        newmessage['details']['share_type'] = ''
                    if 'path' not in newmessage['details']:
                        newmessage['details']['path'] = ''
                    newmessage['summary'] = (
                        'SMB mapping: '
                        '{sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport} '
                        '{share_type}'
                    ).format(**newmessage['details'])
                    return(newmessage, metadata)

                if logtype == 'snmp':
                    if 'version' not in newmessage['details']:
                        newmessage['details']['version'] = 'Unknown'
                    if 'get_bulk_requests' not in newmessage['details']:
                        newmessage['details']['get_bulk_requests'] = 0
                    if 'get_requests' not in newmessage['details']:
                        newmessage['details']['get_requests'] = 0
                    if 'set_requests' not in newmessage['details']:
                        newmessage['details']['set_requests'] = 0
                    if 'get_responses' not in newmessage['details']:
                        newmessage['details']['get_responses'] = 0
                    newmessage['details']['getreqestssum'] = '{0}'.format(newmessage['details']['get_bulk_requests'] + newmessage['details']['get_requests'])
                    newmessage['summary'] = (
                        'SNMPv{version}: '
                        '{sourceipaddress} -> '
                        '{destinationipaddress}:'
                        '{destinationport} '
                        '({getreqestssum} get / '
                        '{set_requests} set requests '
                        '{get_responses} get responses)'
                    ).format(**newmessage['details'])
                    return (newmessage, metadata)

                if logtype == 'x509':
                    newmessage['details']['certificate'] = {}
                    if 'basic_constraints.ca' in newmessage['details']:
                        newmessage['details']['certificate']['basic_constraints_ca'] = newmessage['details']['basic_constraints.ca']
                        del(newmessage['details']['basic_constraints.ca'])
                    if 'basic_constraints.path_len' in newmessage['details']:
                        newmessage['details']['certificate']['basic_constraints_path_len'] = newmessage['details']['basic_constraints.path_len']
                        del(newmessage['details']['basic_constraints.path_len'])
                    if 'certificate.exponent' in newmessage['details']:
                        newmessage['details']['certificate']['exponent'] = newmessage['details']['certificate.exponent']
                        del(newmessage['details']['certificate.exponent'])
                    if 'certificate.issuer' in newmessage['details']:
                        newmessage['details']['certificate']['issuer'] = newmessage['details']['certificate.issuer']
                        del(newmessage['details']['certificate.issuer'])
                    if 'certificate.key_alg' in newmessage['details']:
                        newmessage['details']['certificate']['key_alg'] = newmessage['details']['certificate.key_alg']
                        del(newmessage['details']['certificate.key_alg'])
                    if 'certificate.key_length' in newmessage['details']:
                        newmessage['details']['certificate']['key_length'] = newmessage['details']['certificate.key_length']
                        del(newmessage['details']['certificate.key_length'])
                    if 'certificate.key_type' in newmessage['details']:
                        newmessage['details']['certificate']['key_type'] = newmessage['details']['certificate.key_type']
                        del(newmessage['details']['certificate.key_type'])
                    if 'certificate.not_valid_after' in newmessage['details']:
                        newmessage['details']['certificate']['not_valid_after'] = toUTC(float(newmessage['details']['certificate.not_valid_after'])).isoformat()
                        del(newmessage['details']['certificate.not_valid_after'])
                    if 'certificate.not_valid_before' in newmessage['details']:
                        newmessage['details']['certificate']['not_valid_before'] = toUTC(float(newmessage['details']['certificate.not_valid_before'])).isoformat()
                        del(newmessage['details']['certificate.not_valid_before'])
                    if 'certificate.sig_alg' in newmessage['details']:
                        newmessage['details']['certificate']['sig_alg'] = newmessage['details']['certificate.sig_alg']
                        del(newmessage['details']['certificate.sig_alg'])
                    if 'certificate.subject' in newmessage['details']:
                        newmessage['details']['certificate']['subject'] = newmessage['details']['certificate.subject']
                        del(newmessage['details']['certificate.subject'])
                    if 'certificate.version' in newmessage['details']:
                        newmessage['details']['certificate']['version'] = newmessage['details']['certificate.version']
                        del(newmessage['details']['certificate.version'])
                    if 'certificate.serial' in newmessage['details']:
                        newmessage['details']['certificate']['serial'] = newmessage['details']['certificate.serial']
                        del(newmessage['details']['certificate.serial'])
                    else:
                        newmessage['details']['certificate']['serial'] = '0'
                    newmessage['summary'] = (
                        'X509 certificate seen'
                    ).format(**newmessage['details']['certificate'])
                    return (newmessage, metadata)

        return (newmessage, metadata)
