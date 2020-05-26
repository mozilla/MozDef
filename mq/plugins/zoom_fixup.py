# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import os
import jmespath
import yaml
from mozdef_util.utilities.key_exists import key_exists


class message(object):
    def __init__(self):
        '''
        register our criteria for being passed a message
        as a list of lower case strings or values to match with an event's dictionary of keys or values
        set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''

        # get zoom event data
        self.registration = ['zoom_host']
        self.priority = 2

        with open(os.path.join(os.path.dirname(__file__), 'zoom_mapping.yml'), 'r') as f:
            mapping_map = f.read()

        yap = yaml.safe_load(mapping_map)
        self.eventtypes = list(yap.keys())
        self.yap = yap
        del(mapping_map)

    def onMessage(self, message, metadata):

        if key_exists('tags', message):
            if 'zoom' not in message['tags']:
                return (message, metadata)

        newmessage = {}
        newmessage['details'] = {}

        newmessage['category'] = 'zoom'
        newmessage['eventsource'] = 'MozDef-EF-zoom'
        newmessage['source'] = 'api_aws_lambda'
        newmessage['hostname'] = 'zoom_host'
        newmessage['severity'] = 'info'
        newmessage['processname'] = 'zoom_webhook_api'
        if key_exists('tags', message):
            newmessage['tags'] = message['tags']
        if key_exists('details.event', message):
            newmessage['details']['event'] = message['details']['event']
        else:
            newmessage['details']['event'] = 'UNKNOWN'
        if key_exists('details.payload.account_id', message):
            newmessage['details']['account_id'] = message['details']['payload']['account_id']
            if key_exists('details.payload.object.account_id', message):
                if newmessage.get('details.account_id') != message.get('details.payload.object.account_id'):
                    newmessage['details']['meeting_account_id'] = message['details']['payload']['object']['account_id']
        elif key_exists('details.payload.object.account_id', message):
            newmessage['details']['account_id'] = message['details']['payload']['object']['account_id']

        # rewrite summary to be more informative
        newmessage['summary'] = ""
        if key_exists('details.event', newmessage):
            newmessage['summary'] = "zoom: {0}".format(message['details']['event'])
            if key_exists('details.payload.object.participant.user_name', message):
                newmessage['summary'] += " triggered by user {0}".format(message['details']['payload']['object']['participant']['user_name'])
            elif key_exists('details.payload.operator', message):
                newmessage['summary'] += " triggered by user {0}".format(message['details']['payload']['operator'])

        # iterate through top level keys - push, etc
        if newmessage['source'] in self.eventtypes:
            for key in self.yap[newmessage['source']]:
                mappedvalue = jmespath.search(self.yap[newmessage['source']][key], message)
                # JMESPath likes to silently return a None object
                if mappedvalue is not None:
                    newmessage['details'][key] = mappedvalue
            # Some zoom messages don't contain values within details.payload.object.start_time or details.payload.old_object.start_time.
            # so we set it to original start time, if there is no time data, we remove the key from the message.
            if key_exists('details.payload.object.start_time', message):
                if message['details']['payload']['object']['start_time'] != '':
                    newmessage['details']['start_time'] = message['details']['payload']['object']['start_time']
                else:
                    del newmessage['details']['start_time']
            if key_exists('details.payload.old_object.start_time', message):
                if message['details']['payload']['old_object']['start_time'] != '':
                    newmessage['details']['original_sched_start_time'] = message['details']['payload']['old_object']['start_time']
                else:
                    del newmessage['details']['original_sched_start_time']
            # Some zoom messages do not contain values in details.recording_file_end or details.recording_files_end, so we'll remove the key from the message if it's empty
            if key_exists('details.payload.object.recording_files.recording_end', message):
                if message['details']['payload']['object']['recording_files']['recording_end'] != '':
                    newmessage['details']['recording_files_end'] = message['details']['payload']['object']['recording_files']['recording_end']
                else:
                    del newmessage['details']['recording_files_end']
            if key_exists('details.payload.object.recording_file.recording_end', message):
                if message['details']['payload']['object']['recording_file']['recording_end'] != '':
                    newmessage['details']['recording_file_end'] = message['details']['payload']['object']['recording_file']['recording_end']
                else:
                    del newmessage['details']['recording_file_end']
            # Duration can exist in details.payload.object and details.payload.old_object, let's ensure we are capturing these correctly for updated meetings.
            if key_exists('details.payload.object.duration', message):
                newmessage['details']['duration'] = message['details']['payload']['object']['duration']
            if key_exists('details.payload.old_object.duration', message):
                newmessage['details']['original_sched_duration'] = message['details']['payload']['old_object']['duration']

        else:
            newmessage = None

        return (newmessage, metadata)
