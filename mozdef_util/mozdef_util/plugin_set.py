import os
import pynsive
import importlib
from operator import itemgetter

from .utilities.dict2List import dict2List
from .utilities.logger import logger


class PluginSet(object):
    def __init__(self, plugin_location, enabled_plugins=None):
        self.plugin_location = plugin_location
        self.enabled_plugins = self.identify_plugins(enabled_plugins)

    def identify_plugins(self, enabled_plugins):
        if not os.path.exists(self.plugin_location):
            return []

        module_name = os.path.basename(self.plugin_location)
        root_plugin_directory = os.path.join(self.plugin_location, '..')

        plugin_manager = pynsive.PluginManager()
        plugin_manager.plug_into(root_plugin_directory)

        plugins = []

        found_modules = pynsive.list_modules(module_name)
        for found_module in found_modules:
            module_filename, module_name = found_module.split('.')
            if enabled_plugins is not None and module_name not in enabled_plugins:
                # Skip this plugin since it's not listed as enabled plugins
                # as long as we have specified some enabled plugins though
                # this allows us to specify no specific plugins and get all of them
                continue

            try:
                module_obj = pynsive.import_module(found_module)
                importlib.reload(module_obj)
                plugin_class_obj = module_obj.message()

                if 'priority' in dir(plugin_class_obj):
                    priority = plugin_class_obj.priority
                else:
                    priority = 100

                logger.info('[*] plugin {0} registered to receive messages with {1}'.format(module_name, plugin_class_obj.registration))
                plugins.append(
                    {
                        'plugin_class': plugin_class_obj,
                        'registration': plugin_class_obj.registration,
                        'priority': priority
                    }
                )
            except Exception as e:
                logger.exception('Received exception when loading {0} plugins\n{1}'.format(module_name, e))
        plugin_manager.destroy()
        return plugins

    @property
    def ordered_enabled_plugins(self):
        return sorted(self.enabled_plugins, key=itemgetter('priority'), reverse=False)

    def run_plugins(self, message, metadata=None):
        '''compare the message to the plugin registrations.
           plugins register with a list of keys or values
           or values they want to match on
           this function compares that registration list
           to the current message and sends the message to plugins
           in order
        '''
        if not isinstance(message, dict):
            raise TypeError('event is type {0}, should be a dict'.format(type(message)))

        for plugin in self.ordered_enabled_plugins:
            send = False
            message_fields = [e for e in dict2List(message)]
            # this is to make it so we can match on all fields
            message_fields.append('*')
            if isinstance(plugin['registration'], list):
                if set(plugin['registration']).intersection(message_fields):
                    send = True
            elif isinstance(plugin['registration'], str):
                if plugin['registration'] in message_fields:
                    send = True
            if send:
                try:
                    (message, metadata) = self.send_message_to_plugin(plugin_class=plugin['plugin_class'], message=message, metadata=metadata)
                except Exception as e:
                    logger.exception('Received exception in {0}: message: {1}\n{2}'.format(plugin['plugin_class'], message, e))
                if message is None:
                    return (message, metadata)
        return (message, metadata)

    def send_message_to_plugin(self, plugin_class, message, metadata=None):
        '''moving this logic to a separate function allows
           different types of plugin_sets, such as alerts that might not care
           about receiving metadata in its plugins
        '''
        return plugin_class.onMessage(message, metadata)
