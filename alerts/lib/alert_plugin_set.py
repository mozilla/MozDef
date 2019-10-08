from mozdef_util.plugin_set import PluginSet


class AlertPluginSet(PluginSet):

    def send_message_to_plugin(self, plugin_class, message, metadata=None):
        return plugin_class.onMessage(message), metadata
