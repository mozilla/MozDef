import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from plugin_set import PluginSet

from utilities.logger import logger


class AlertPluginSet(PluginSet):

    def send_message_to_plugin(self, plugin_class, message, metadata=None):
        if 'utctimestamp' in message and 'summary' in message:
            message_log_str = '{0} received message: ({1}) {2}'.format(plugin_class.__module__, message['utctimestamp'], message['summary'])
            logger.error(message_log_str)

        return plugin_class.onMessage(message), metadata
