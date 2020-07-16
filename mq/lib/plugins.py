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


def sendEventToPlugins(anevent, metadata, pluginList):
    '''compare the event to the plugin registrations.
       plugins register with a list of keys or values
       or values they want to match on
       this function compares that registration list
       to the current event and sends the event to plugins
       in order
    '''
    if not isinstance(anevent, dict):
        raise TypeError('event is type {0}, should be a dict'.format(type(anevent)))

    # expecting tuple of module,criteria,priority in pluginList
    # sort the plugin list by priority
    executed_plugins = []
    for plugin in sorted(pluginList, key=itemgetter(2), reverse=False):
        # assume we don't run this event through the plugin
        send = False
        if isinstance(plugin[1], list):
            try:
                plugin_matching_keys = set([item.lower() for item in plugin[1]])
                event_tokens = [e for e in dict2List(anevent)]
                if plugin_matching_keys.intersection(event_tokens):
                    send = True
            except TypeError:
                logger.error('TypeError on set intersection for dict {0}'.format(anevent))
                return (anevent, metadata)
        if send:
            (anevent, metadata) = plugin[0].onMessage(anevent, metadata)
            if anevent is None:
                # plug-in is signalling to drop this message
                # early exit
                return (anevent, metadata)
            plugin_name = plugin[0].__module__.replace('plugins.', '')
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
                    if type(mreg) != list:
                        raise ImportError('Plugin {0} registration needs to be a list'.format(mname))
                    if 'priority' in dir(mclass):
                        mpriority = mclass.priority
                    else:
                        mpriority = 100
                    if isinstance(mreg, list):
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
