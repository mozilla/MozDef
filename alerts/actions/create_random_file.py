# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import os
import json
from configlib import getConfig, OptionParser
from tempfile import mkstemp


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an event
        by creating a random file
        with an alert content in it
        '''

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = os.path.join(os.path.dirname(__file__), 'create_random_file.conf')
        self.options = None
        if os.path.exists(self.configfile):
            self.initConfiguration()

        self.registration = self.options.keywords.split(" ")
        self.priority = 1

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options
        # change this to your default zone for when it's not specified
        self.options.keywords = getConfig('keywords', 'KEYWORDS', self.configfile)
        self.options.prefix = getConfig('prefix', 'tmp_alert_', self.configfile)
        self.options.tmpdirname = getConfig('tmpdirname', 'tmp', self.configfile)
        self.options.tmpdirpath = os.path.join(os.path.dirname(__file__), self.options.tmpdirname)

    def onMessage(self, message):
        # here is where you do something with the incoming alert message
        if 'summary' in message.keys():
            (fd, filename) = mkstemp(prefix=self.options.prefix, dir=self.options.tmpdirpath)
            try:
                out = os.fdopen(fd, "w")
                out.write(json.dumps(message))
                out.write('\n')
                out.flush()
                out.close()
                # It is not cool to leak a file descriptor
                os.close(fd)
            except:
                pass

        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message
