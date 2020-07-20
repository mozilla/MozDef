# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.remove_dots import message


class TestRemoveDotsPlugin():
    def setup(self):
        self.plugin = message()

    def test_first_dot_removal(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'fileuploadurls': {
                        '.ds_store': 'astringvalue',
                        'js/app.js': 'astringvalue'
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'fileuploadurls': {
                        'ds_store': 'astringvalue',
                        'js/app.js': 'astringvalue'
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_last_dot_removal(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'fileuploadurls': {
                        'ds_store.': 'astringvalue',
                        'js/app.js': 'astringvalue'
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'fileuploadurls': {
                        'ds_store': 'astringvalue',
                        'js/app.js': 'astringvalue'
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_list_dot_removal(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'fileuploadurls': {
                        'ds_store.': 'astringvalue',
                        'js/app.js': 'astringvalue'
                    },
                    '.randomlist.': [
                        'weird_case',
                        'random_case',
                    ],
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'fileuploadurls': {
                        'ds_store': 'astringvalue',
                        'js/app.js': 'astringvalue'
                    },
                    'randomlist': [
                        'weird_case',
                        'random_case',
                    ],
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
