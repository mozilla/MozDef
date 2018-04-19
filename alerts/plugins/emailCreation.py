# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


import os
import sys
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.Utils import formatdate
from time import mktime


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an event using
        the pager duty event api
        '''

        config_path = os.path.join(
            os.path.dirname(__file__),
            'emailCreation.json')

        # If we can't open the config file or load it as JSON,
        # propagate the error up the call chain.
        with open(config_path) as config_file:
            self.options = json.load(config_file)

        self.registration = ['bypassused']
        self.priority = 1


    def onMessage(self, message):
        # The Date field needs to be in a specific format, and we must
        # define it or gmail struggles to parse it.
        current_time = formatdate(mktime(datetime.utcnow().timetuple()))

        emailMessage = MIMEText('{0} on {1}'.format(
            message['summary'],
            message['events'][0]['documentsource']['utctimestamp']))
        emailMessage['Subject'] = self.options['subject']
        emailMessage['From'] = self.options['sender']
        emailMessage['To'] = ','.join(self.options['recipients'])
        emailMessage['Date'] = current_time

        smtpObj = smtplib.SMTP(
            self.options['mailServer'],
            self.options['mailServerPort'])

        try:
            smtpObj.sendmail(
                self.options['sender'],
                self.options['recipients'],
                emailMessage.as_string())
            smtpObj.quit()
        except smtplib.SMTPException as e:
            sys.stderr.write('Error: failed to send email {0}\n'.format(e))

        return message
