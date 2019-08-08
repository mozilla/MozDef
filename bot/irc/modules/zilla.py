#!/usr/bin/env python
# Inspired by https://github.com/ayust/kitnirc/blob/master/kitnirc/contrib/healthcheck.py
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import logging
from kitnirc.modular import Module
import threading
import time
import json
import bugzilla

# get a logger for the module
# via the Python logging library.
_log = logging.getLogger(__name__)


# KitnIRC modules subclass kitnirc.modular.Module
class Zilla(Module):
    def __init__(self, *args, **kwargs):
        super(Zilla, self).__init__(*args, **kwargs)
        self._stop = False
        self.thread = threading.Thread(target=self.loop, name='zilla')
        self.thread.daemon = True

        config = self.controller.config
        try:
            self.url = config.get("zilla", "url")
            self.api_key = config.get("zilla", "api_key")
            self.interval = config.getint("zilla", "interval")
            self.channel = config.get('zilla', 'channel')
        except AttributeError:
            _log.warning("Couldn't load the Zilla module, check your configuration.")
            self.url = "https://example.com"
            self.api_key = "DEADBEEF"
            self.interval = 9999999
            self.channel = '#test'

        self._bugzilla = bugzilla.Bugzilla(url=self.url + 'rest/', api_key=self.api_key)

        _log.info("zilla module initialized for {}, pooling every {} seconds.".format(self.url, self.interval))

    def loop(self):
        last = 0
        while not self._stop:
            now = time.time()
            if ((now - last) > self.interval):
                # Add all the actions you want to do with bugzilla here ;)
                self.bugzilla_search()
                last = now
            time.sleep(1)

    def bugzilla_search(self):
            config = self.controller.config
            try:
                terms = json.loads(config.get('zilla', 'search_terms'))
            except AttributeError:
                _log.warning("zilla could not load search terms")
                return

            for search_group in terms:
                try:
                    res = self._bugzilla.search_bugs(search_group)
                except Exception as e:
                    _log.error('Error querying bugzilla' + str(e))
                    return
                for bug in res['bugs']:
                    bugsummary = bug['summary'].encode('utf-8', 'replace')
                    self.controller.client.msg(
                        self.channel,
                        "\x037\x02WARNING\x03\x02 \x032\x02NEW\x03\x02 bug: {url}{bugid} {summary}".format(
                            summary=bugsummary,
                            url=self.url,
                            bugid=bug['id']
                        )
                    )

    def start(self, *args, **kwargs):
        super(Zilla, self).start(*args, **kwargs)
        self._stop = False
        self.thread.start()

    def stop(self, *args, **kwargs):
        super(Zilla, self).stop(*args, **kwargs)
        self._stop = True
        self.thread.join()


# Let KitnIRC know what module class it should be loading.
module = Zilla
