#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


class DotDict(dict):
    '''dict.item notation for dict()'s'''
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct={}):
        for key, value in dct.items():
            if hasattr(value, 'keys'):
                value = DotDict(value)
            self[key] = value

    def get(self, key):
        """get to allow for dot string notation
        :param str key: Key in dot-notation (e.g. 'foo.lol').
        :return: value. None if no value was found.
        """
        try:
            return self.__lookup(self, key)
        except KeyError:
            return None

    def __lookup(self, dct, key):
        """Checks dct recursive to find the value for key.
        Is used by get() interanlly.
        :param dict dct: input dictionary
        :param str key: The key we are looking for.
        :return: The  value.
        :raise KeyError: If the given key is not found
        """
        if '.' in key:
            key, node = key.split('.', 1)
            return self.__lookup(dct[key], node)
        else:
            return dct[key]
