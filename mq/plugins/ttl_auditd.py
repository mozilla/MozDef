# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        register our criteria for being passed a message
        '''

        # this plugin inspects messages for whitelist stuff that
        # should be stored with a TTL so we keep it for a little while
        # and delete rather than waiting for the index purge
        self.registration = ['auditd', 'command']
        self.priority = 1

    def onMessage(self, message, metadata):
        # ganglia monitor daemon -> 3d
        if ('details' in message and
                'parentprocess' in message['details'] and
                message['details']['parentprocess'] == 'gmond' and
                'duser' in message['details'] and
                message['details']['duser'] == 'nobody' and
                'command' in message['details'] and
                message['details']['command'] == '/bin/sh -c netstat -t -a -n'):
            message['_ttl'] = '3d'

        # rabbitmq -> 3d
        if (
            ('details' in message and
                'parentprocess' in message['details'] and
                message['details']['parentprocess'] == 'beam.smp' and
                'duser' in message['details'] and
                message['details']['duser'] == 'rabbitmq' and
                'command' in message['details']
             ) and
            (
                message['details']['command'] == '/usr/lib64/erlang/erts-5.8.5/bin/epmd -daemon' or
                message['details']['command'].startswith('inet_gethost 4') or
                message['details']['command'].startswith('sh -c exec inet_gethost 4') or
                message['details']['command'].startswith('/bin/sh -s unix:cmd') or
                message['details']['command'].startswith('sh -c exec /bin/sh -s unix:cmd'))):
            message['_ttl'] = '3d'

        # sshd -> 3d
        if ('details' in message and
                'parentprocess' in message['details'] and
                message['details']['parentprocess'] == 'sshd' and
                'duser' in message['details'] and
                message['details']['duser'] == 'root' and
                'command' in message['details'] and
                message['details']['command'] == '/usr/sbin/sshd -R'):
            message['_ttl'] = '3d'

        # chkconfig -> 3d
        if (
            ('details' in message and
                'parentprocess' in message['details'] and
                message['details']['parentprocess'] == 'chkconfig' and
                'suser' in message['details'] and
                message['details']['suser'] == 'root' and
                'command' in message['details']
             ) and
            (
                message['details']['command'].startswith('/sbin/runlevel') or
                message['details']['command'].startswith('sh -c /sbin/runlevel'))):
            message['_ttl'] = '3d'

        # nagios -> 3d
        if (
            ('details' in message and
                'duser' in message['details'] and
                message['details']['duser'] == 'nagios' and
                'suser' in message['details'] and
                message['details']['suser'] == 'root' and
                'command' in message['details']
             ) and
            (
                message['details']['command'].startswith('/usr/lib64/nagios/plugins') or
                message['details']['command'].startswith('sh -c /usr/lib64/nagios/plugins'))):
            message['_ttl'] = '3d'

        return (message, metadata)
