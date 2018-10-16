import os
import sys
from plugin_set import PluginSet

from mozdef_util.utilities.logger import logger


class AlertPluginSet(PluginSet):

    def send_message_to_plugin(self, plugin_class, message, metadata=None):
        if 'utctimestamp' in message and 'summary' in message:
            message_log_str = u'{0} received message: ({1}) {2}'.format(plugin_class.__module__, message['utctimestamp'], message['summary'])
            logger.info(message_log_str)

        return plugin_class.onMessage(message), metadata
