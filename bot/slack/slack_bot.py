import random
import sys
import os
import time
import websocket

from slackclient import SlackClient

from bot_plugin_set import BotPluginSet

from mozdef_util.utilities.logger import logger


greetings = [
    "mozdef bot in da house",
    "mozdef here..what's up",
    "mozdef has joined the room..no one panic",
    "mozdef bot here..nice to see everyone"
]


class SlackBot():
    def __init__(self, api_key, channels, bot_name, notify_welcome):
        self.slack_client = SlackClient(api_key)
        self.channels = channels
        self.bot_name = bot_name
        self.notify_welcome = notify_welcome
        self.load_commands()

    def load_commands(self):
        plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))
        plugin_set = BotPluginSet(plugin_dir)
        self.plugins = {}
        for plugin in plugin_set.enabled_plugins:
            self.plugins[plugin['command_name']] = plugin

    def run(self):
        if self.slack_client.rtm_connect():
            logger.info("Bot connected to slack")
            if self.notify_welcome:
                self.post_welcome_message(random.choice(greetings))
            self.listen_for_messages()
        else:
            logger.error("Unable to connect to slack")
            sys.exit(1)

    def delegate_command(self, message_text):
        response = ""
        message_tokens = message_text.split()
        command = message_tokens[0]
        parameters = message_tokens[1:len(message_tokens)]

        if command == '!help':
            response = "\nHelp is on it's way...try these:\n"
            for command_name, plugin in self.plugins.items():
                response += "\n{0} -- {1}".format(
                    command_name,
                    plugin['help_text']
                )
        else:
            if command not in self.plugins:
                response = "Unknown command: " + command + ". Try !help"
            else:
                plugin = self.plugins[command]
                logger.info("Sending to {0}".format(plugin['plugin_class'].__module__))
                try:
                    response = "\n" + plugin['plugin_class'].handle_command(parameters)
                except Exception as e:
                    response = "\nReceived an error when processing your request."
                    logger.exception(e)

        return response

    def parse_command(self, content):
        # messages look like this:
        # pwnbus: @mozdef !help
        tokens = content.split('@' + self.bot_name)
        command = tokens[1].strip()
        return command

    def handle_message(self, message):
        channel = message['channel']
        thread_ts = message['ts']
        # If we're already in a thread, reply within that thread
        if 'thread_ts' in message:
            thread_ts = message['thread_ts']
        content = message['content']
        command = self.parse_command(content)

        response = self.delegate_command(command)
        if response is not "":
            self.post_thread_message(
                text=response,
                channel=channel,
                thread_ts=thread_ts
            )

    def listen_for_messages(self):
        while True:
            try:
                for slack_message in self.slack_client.rtm_read():
                    message_type = slack_message.get('type')
                    if message_type == 'desktop_notification':
                        logger.info("Received message: {0}".format(slack_message['content']))
                        self.handle_message(slack_message)
            except websocket.WebSocketConnectionClosedException:
                logger.info("Received WebSocketConnectionClosedException exception...reconnecting")
                time.sleep(3)
                self.slack_client.rtm_connect()
            time.sleep(1)

    def post_thread_message(self, text, channel, thread_ts):
        self.slack_client.api_call(
            "chat.postMessage",
            as_user="true",
            channel=channel,
            text=text,
            thread_ts=thread_ts
        )

    def _post_attachment(self, message, channel, color, sub_fields=None):
        if channel is None:
            message_channels = self.channels
        else:
            message_channels = [channel]

        for message_channel in message_channels:
            attachment = {
                'fallback': message,
                'text': message,
                'color': color,
            }
            if sub_fields is not None:
                attachment['fields'] = sub_fields

            self.slack_client.api_call("chat.postMessage", channel=message_channel, attachments=[attachment], as_user=True)

    def post_alert_message(self, alert_dict, channel):
        severity = alert_dict['severity'].upper()
        message_text = alert_dict['summary']
        # Default to black if severity isn't known
        message_color = "#000000"
        if severity == 'CRITICAL':
            message_color = "#d04437"
        elif severity == 'ERROR':
            message_color = "#d04437"
        elif severity == 'WARNING':
            message_color = "#ffd351"
        elif severity == 'INFO':
            message_color = "#cccccc"
        elif severity == 'NOTICE':
            message_color = "#4a6785"

        sub_fields = [
            {
                "title": "Severity",
                "value": severity,
                "short": True
            },
            {
                "title": "Category",
                "value": alert_dict['category'],
                "short": True
            }
        ]
        self._post_attachment(
            message=message_text,
            channel=channel,
            color=message_color,
            sub_fields=sub_fields
        )

    def post_welcome_message(self, message, channel=None):
        self._post_attachment(message, channel, '#36a64f')
