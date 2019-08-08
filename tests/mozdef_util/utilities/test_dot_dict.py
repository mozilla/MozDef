#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import pytest

from mozdef_util.utilities.dot_dict import DotDict

from tests.unit_test_suite import UnitTestSuite


class TestDotDict(UnitTestSuite):
    def test_blank_init(self):
        dct = DotDict()
        assert list(dct.keys()) == []

    def test_nonexisting_key(self):
        dct = DotDict()
        with pytest.raises(KeyError):
            dct.abcd

    def test_basic_init(self):
        dct = DotDict({'key1': 'value1', 'key2': 'value2'})
        assert sorted(dct.keys()) == sorted(['key1', 'key2'])
        assert dct.key1 == 'value1'
        assert dct.key2 == 'value2'

    def test_complex_init(self):
        original_dct = {
            'details': {
                'key1': 'value1'
            }
        }
        dct = DotDict(original_dct)
        assert dct.details == {'key1': 'value1'}
        assert dct.details.key1 == 'value1'

    def test_complex_get(self):
        original_dct = {
            'details': {
                'key1': 'value1',
                'subkey': {
                    'subkey': 'subvalue'
                }
            }
        }
        dct = DotDict(original_dct)
        assert dct.get('does.not.exist') is None
        assert dct.get('details') == {'key1': 'value1','subkey': {'subkey': 'subvalue'}}
        assert dct.get('details.key1') == 'value1'
        assert dct.get('details.subkey') == {'subkey':'subvalue'}
        assert dct.get('details.subkey.subkey') == 'subvalue'
