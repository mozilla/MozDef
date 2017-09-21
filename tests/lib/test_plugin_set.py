import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from plugin_set import PluginSet


class TestPluginSet(object):
    def setup(self):
        self.plugin_dir = os.path.join(os.path.dirname(__file__), 'test_plugins')
        self.plugin_set = PluginSet(self.plugin_dir)
        self.metadata = {
            'index': 'test',
            'doc_type': 'testdoc',
        }

    def test_registered_plugins(self):
        total_num_plugins = len([name for name in os.listdir(self.plugin_dir)])
        # We exclude the __init__.py file
        assert len(self.plugin_set.enabled_plugins) == total_num_plugins - 1

    def test_registered_plugins_specific_enabled_plugins(self):
        enabled_plugins = ['plugin1']
        plugin_set = PluginSet(self.plugin_dir, enabled_plugins)
        assert len(plugin_set.enabled_plugins) == 1

    def test_registered_plugins_other_enabled_plugins(self):
        enabled_plugins = ['someotherplugin']
        plugin_set = PluginSet(self.plugin_dir, enabled_plugins)
        assert len(plugin_set.enabled_plugins) == 0

    def test_ordered_enabled_plugins(self):
        ordered_plugins = self.plugin_set.ordered_enabled_plugins
        assert ordered_plugins[0]['registration'] == ['apples']
        assert ordered_plugins[1]['registration'] == 'bananas'
        assert ordered_plugins[2]['registration'] == ['oranges']
        assert ordered_plugins[3]['registration'] == ['pears']
        assert ordered_plugins[4]['registration'] == ['grapes']

    def test_run_plugins_matching_key_plugin1(self):
        message = {'apples': 'sometext', 'otherkey': 'abcd'}

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert 'unit_test_key' not in message
        # Verify that our first plugin ran and was able
        # to modify the message
        assert parsed_message['unit_test_key'] == 'apples'
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin1(self):
        message = {'test': 'apples', 'otherkey': 'abcd'}

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert 'unit_test_key' not in message
        # Verify that our first plugin ran and was able
        # to modify the message
        assert parsed_message['unit_test_key'] == 'apples'
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin2(self):
        message = {'test': 'bananas', 'otherkey': 'abcd'}

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert 'unit_test_key' not in message
        # verify that we overwrote message object
        assert parsed_message['unit_test_key'] == 'bananas'
        assert parsed_metadata == self.metadata

    def test_run_plugins_match_multiple_plugins(self):
        message = {'test': 'bananas', 'apples': 'abcd'}

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert 'unit_test_key' not in message
        # Verify that our second plugin overwrote the field
        assert parsed_message['unit_test_key'] == 'bananas'
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin3(self):
        message = {'test': 'oranges', 'otherkey': 'abcd'}

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert 'unit_test_key' not in message
        assert 'plugin3_key' not in message
        assert parsed_message['plugin3_key'] == 'oranges'
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin4(self):
        message = {'test': 'pears', 'otherkey': 'abcd'}

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert message is not None
        assert parsed_message is None
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin5(self):
        message = {'test': 'grapes', 'otherkey': 'abcd'}

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert parsed_message == message
        assert self.metadata['plugin5_key'] == 'grapes'
        assert parsed_metadata['plugin5_key'] == 'grapes'

    def test_run_plugins_matching_value_all_normal_plugins(self):
        message = {'apples': 'bananas', 'oranges': 'grapes'}
        expected_metadata = {
            'index': 'test',
            'doc_type': 'testdoc',
            'plugin5_key': 'grapes'
        }

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert 'unit_test_key' not in message
        assert 'plugin3_key' not in message
        assert parsed_message['unit_test_key'] == 'bananas'
        assert parsed_message['plugin3_key'] == 'oranges'
        assert parsed_metadata == expected_metadata

    def test_run_plugins_modified_message_plugins(self):
        '''This unit tests checks to see if we modify a message
           in a plugin, that a plugin further down the 'line'
           can register and get the updated message
        '''
        message = {'apples': 'test', 'testkey': 'othervalue'}

        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert 'plugin6_key' not in message
        assert parsed_message['plugin6_key'] == 'plums'
        assert parsed_metadata == self.metadata
