# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''
        # get auditd data
        self.registration = ['auditd', 'audisp-json']
        self.priority = 2

    def onMessage(self, message, metadata):
        # check for messages we have vetted as n/a and prevalent
        # from a sec standpoint and drop them

        # ganglia monitor daemon
        if ('details' in message and
                'parentprocess' in message['details'] and
                message['details']['parentprocess'] == 'gmond' and
                'duser' in message['details'] and
                message['details']['duser'] == 'nobody' and
                'command' in message['details'] and
                message['details']['command'] == '/bin/sh -c netstat -t -a -n'):
            return(None, metadata)

        # rabbitmq
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
            return(None, metadata)

        # sshd
        if ('details' in message and
                'parentprocess' in message['details'] and
                message['details']['parentprocess'] == 'sshd' and
                'duser' in message['details'] and
                message['details']['duser'] == 'root' and
                'command' in message['details'] and
                message['details']['command'] == '/usr/sbin/sshd -R'):
            return(None, metadata)

        # chkconfig
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
            return(None, metadata)

        # nagios
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
            return(None, metadata)

        # fix auid from long to int
        if 'details' in message and isinstance(message['details'], dict):
            if 'auid' in message['details'] and message['details']['auid'] == "4294967295":
                    message['details']['auid'] = '-1'
            if 'ses' in message['details'] and message['details']['ses'] == "4294967295":
                    message['details']['ses'] = '-1'
            # fix '(null)' string records to fit in a long
            for k, v in message['details'].items():
                if v == '(null)' and 'id' in k:
                    message['details'][k] = -1

        # fix occasional gid errant parsing
        if 'details' in message and isinstance(message['details'], dict):
            if 'gid' in message['details'] and ',' in message['details']['gid']:
                # gid didn't parse right, should just be an integer
                # move it to a new field to not trigger errors in ES indexing
                # as it tries to convert gid to long
                message['details']['gidstring'] = message['details']['gid']
                del message['details']['gid']

        # fix details.dhost to be hostname
        if 'details' in message and isinstance(message['details'], dict):
            if 'dhost' in message['details']:
                # details.dhost is the host that the auditd event is happening on.
                message['hostname'] = message['details']['dhost']
                del message['details']['dhost']

        # add category
        if 'category' not in message:
            message['category'] = 'auditd'
        # add type as a static entry
        message['type'] = 'auditd'

        return (message, metadata)
