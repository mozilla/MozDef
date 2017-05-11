# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Alicia Smith <asmith@mozilla.com>
# Michal Purzynski <mpurzynski@mozilla.com>
# Brandon Myers <bmyers@mozilla.com>

import os
import sys
from datetime import datetime
from configlib import getConfig, OptionParser
import smtplib
from email.mime.text import MIMEText


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an email sent to
        the releng signing server team
        '''

        self.registration = ['access']
        self.priority = 2

        # set my own conf file
        # relative path to the alerts alertWorker.py file
        self.configfile = './plugins/ssh_access_signreleng.conf'
        self.options = None
        if os.path.exists(self.configfile):
            sys.stdout.write('found conf file {0}\n'.format(self.configfile))
            self.initConfiguration()

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # email settings
        self.options.smtpserver = getConfig('smtpserver', 'localhost', self.configfile)
        self.options.sender = getConfig('sender', 'donotreply@localhost.com', self.configfile)
        recipients_str = getConfig('recipients', 'noone@localhost.com', self.configfile)
        self.options.recipients = recipients_str.split(',')

    def onMessage(self, message):
        # here is where you do something with the incoming alert message

        emailMessage = MIMEText(message['summary'] + ' on ' + message['events'][0]['documentsource']['utctimestamp'])
        emailMessage['Subject'] = 'MozDef Alert: Releng Restricted Servers Successful SSH Access'
        emailMessage['From'] = self.options.sender
        emailMessage['To'] = self.options.recipients
        emailMessage['Date'] = datetime.utcnow().isoformat()
        smtpObj = smtplib.SMTP(self.options.smtpserver, 25)
        try:
            smtpObj.sendmail(self.options.sender, self.options.recipients, emailMessage.as_string())
            smtpObj.quit()
        except smtplib.SMTPException as e:
            sys.stderr.write('Error: failed to send email {0}\n'.format(e))

        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message
