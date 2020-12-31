#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import os
from operator import itemgetter
from datetime import datetime
import pynsive
import importlib

from mozdef_util.utilities.dict2List import dict2List
from mozdef_util.utilities.logger import logger


def is_subset(subset, superset):
    """
    Test if :subset: is a subset of :superset:.
    Recursive inside dict and list objects.

    # Value strict equality
    >>> is_subset({"id": 2}, {"id": 2.0})
    False
    >>> is_subset({"id": 2}, {"id": 2})
    True
    # Strings must match
    >>> is_subset({"id": "abcd"}, {"id": "abc"})
    False
    # Dict subset
    >>> is_subset({"id": "abc"}, {"id": "abc", "type": "event"})
    True
    # List subset
    >>> is_subset(["tag1"], ["tag1", "tag2"])
    True
    # Recursive inside dict-like and list-like objects
    >>> is_subset({"details": {"tags": ["tag2"]}}, {"details": {"tags": ["tag1", "tag2"], "k": "v"}})
    True
    # Empty dict and lists are assumed to mean the superset must also be empty
    >>> is_subset({"tags": []}, {"tags": ["tag1", "tag2"]})
    False
    >>> is_subset({"tags": []}, {"tags": []})
    True
    >>> is_subset({"tags": []}, {"tags": {}})
    False
    >>> is_subset({"details": {}}, {"details": {"key": "value"}})
    False
    """
    if subset and isinstance(subset, dict):
        return all(key in superset and is_subset(val, superset[key]) for key, val in subset.items())

    if subset and isinstance(subset, list):
        return all(any(is_subset(subitem, superitem) for superitem in superset) for subitem in subset)

    return type(subset) == type(superset) and subset == superset


def sendEventToPlugins(anevent, metadata, pluginList):
    """
    Send an event to the matching plugins and return the updated event.

    Plugins register with a list of keys or values they want to match on,
    or with a dict that represents a sub-dict of the event that should match.
    This function compares that registration list or dict to the current event
    and sends the event to matching plugins in priority order.
    """
    if not isinstance(anevent, dict):
        raise TypeError('event is type {0}, should be a dict'.format(type(anevent)))

    # expecting tuple of module,criteria,priority in pluginList
    # sort the plugin list by priority
    executed_plugins = []
    for plugin in sorted(pluginList, key=itemgetter(2), reverse=False):
        # assume we don't run this event through the plugin
        send = False
        plugin_class = plugin[0]
        registration_criteria = plugin[1]
        if isinstance(registration_criteria, list):
            try:
                plugin_matching_keys = set([item.lower() for item in registration_criteria])
                event_tokens = [e for e in dict2List(anevent)]
                if plugin_matching_keys.intersection(event_tokens):
                    send = True
            except TypeError:
                logger.error('TypeError on set intersection for dict {0}'.format(anevent))
                return (anevent, metadata)
        elif isinstance(registration_criteria, dict):
            try:
                send = is_subset(registration_criteria, anevent)
            except Exception:
                logger.error('Error on subset matching for dict {0}'.format(anevent))
                return (anevent, metadata)
        if send:
            (anevent, metadata) = plugin_class.onMessage(anevent, metadata)
            if anevent is None:
                # plug-in is signalling to drop this message
                # early exit
                return (anevent, metadata)
            plugin_name = plugin_class.__module__.replace('plugins.', '')
            executed_plugins.append(plugin_name)
    # Tag all events with what plugins ran on it
    if 'mozdef' not in anevent:
        anevent['mozdef'] = {}
        anevent['mozdef']['plugins'] = executed_plugins

    return (anevent, metadata)


def registerPlugins():
    pluginList = list()   # tuple of module,registration dict,priority
    if os.path.exists('plugins'):
        modules = pynsive.list_modules('plugins')
        for mname in modules:
            module = pynsive.import_module(mname)
            importlib.reload(module)
            if not module:
                raise ImportError('Unable to load module {}'.format(mname))
            else:
                if 'message' in dir(module):
                    mclass = module.message()
                    mreg = mclass.registration
                    if type(mreg) not in (list, dict):
                        raise ImportError('Plugin {0} registration needs to be a list or a dict'.format(mname))
                    if 'priority' in dir(mclass):
                        mpriority = mclass.priority
                    else:
                        mpriority = 100
                    if isinstance(mreg, (list, dict)):
                        logger.info('[*] plugin {0} registered to receive messages with {1}'.format(mname, mreg))
                        pluginList.append((mclass, mreg, mpriority))
    return pluginList


def checkPlugins(pluginList, lastPluginCheck, checkFrequency):
    if abs(datetime.now() - lastPluginCheck).seconds > checkFrequency:
        # print('[*] checking plugins')
        lastPluginCheck = datetime.now()
        pluginList = registerPlugins()
        return pluginList, lastPluginCheck
    else:
        return pluginList, lastPluginCheck
