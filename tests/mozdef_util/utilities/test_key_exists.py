#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mozdef_util.utilities.key_exists import key_exists


class TestKeyExists():
    def setup(self):
        self.default_event = {
            'details': {
                'depth1': {
                    'depth2': {
                        'depth3': {
                            'somekey': 'somevalue'
                        }
                    }
                }
            }
        }

    def test_basic_dict_positive(self):
        assert key_exists('details', {'details': 'abcd'}) is True

    def test_basic_dict_negative(self):
        assert key_exists('otherkey', {'details': 'abcd'}) is False

    def test_basic_dict_positive_complicated(self):
        assert key_exists('details.depth1.depth2.depth3.somekey', self.default_event) is True

    def test_basic_dict_positive_complicated_false(self):
        assert key_exists('details.depth2.depth1.depth3.somekey', self.default_event) is False

    def test_basic_dict_positive_complicated_2(self):
        assert key_exists('details.depth2.depth1', self.default_event) is False
