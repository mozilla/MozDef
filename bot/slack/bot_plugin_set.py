import os
import pynsive
import importlib

from mozdef_util.utilities.logger import logger


class BotPluginSet():

    def __init__(self, plugin_location, enabled_plugins=None):
        self.plugin_location = plugin_location
        self.enabled_plugins = self.identify_plugins(enabled_plugins)

    def identify_plugins(self, enabled_plugins):
        if not os.path.exists(self.plugin_location):
            return []

        module_name = os.path.basename(self.plugin_location)
        root_plugin_directory = self.plugin_location

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

            module_obj = pynsive.import_module(found_module)
            importlib.reload(module_obj)
            plugin_class_obj = module_obj.Command()
            logger.info('Plugin {0} registered to receive command with {1}'.format(module_name, plugin_class_obj.command_name))
            plugins.append(
                {
                    'plugin_class': plugin_class_obj,
                    'command_name': plugin_class_obj.command_name,
                    'help_text': plugin_class_obj.help_text
                }
            )
        return plugins
