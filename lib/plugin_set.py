import os
import pynsive
from operator import itemgetter
from utilities.dict2List import dict2List
import copy


class PluginSet(object):
    def __init__(self, plugin_location, enabled_plugins=[]):
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
            if module_name not in enabled_plugins and len(enabled_plugins) > 0:
                # Skip this plugin since it's not listed as enabled plugins
                # or don't skip plugin if we don't have any enabled plugins set (which means all)
                continue

            module_obj = pynsive.import_module(found_module)
            reload(module_obj)
            plugin_class_obj = module_obj.message()

            if 'priority' in dir(plugin_class_obj):
                priority = plugin_class_obj.priority
            else:
                priority = 100

            plugins.append(
                {
                    'plugin_class': plugin_class_obj,
                    'registration': plugin_class_obj.registration,
                    'priority': priority
                }
            )
        return plugins

    @property
    def ordered_enabled_plugins(self):
        return sorted(self.enabled_plugins, key=itemgetter('priority'), reverse=False)

    def run_plugins(self, message, metadata):
        '''compare the message to the plugin registrations.
           plugins register with a list of keys or values
           or values they want to match on
           this function compares that registration list
           to the current message and sends the message to plugins
           in order
        '''
        if not isinstance(message, dict):
            raise TypeError('event is type {0}, should be a dict'.format(type(message)))

        # We deep copy the message in case the caller of this function wants
        # to reference the original one (so we don't change it in here)
        message_copy = copy.deepcopy(message)
        for plugin in self.ordered_enabled_plugins:
            send = False
            try:
                if isinstance(plugin['registration'], list):
                    if (set(plugin['registration']).intersection([e for e in dict2List(message_copy)])):
                        send = True
                elif isinstance(plugin['registration'], str):
                    if plugin['registration'] in [e for e in dict2List(message_copy)]:
                        send = True
            except TypeError:
                # If we can't parse the message, then return the original message and metadata
                return (message, metadata)
            if send:
                (message_copy, metadata) = self.send_message_to_plugin(plugin_class=plugin['plugin_class'], message=message_copy, metadata=metadata)
                if message_copy is None:
                    return (message_copy, metadata)
        return (message_copy, metadata)

    def send_message_to_plugin(self, plugin_class, message, metadata):
        return plugin_class.onMessage(message, metadata)
