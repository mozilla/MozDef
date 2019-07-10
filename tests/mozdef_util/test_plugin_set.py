import os

from mozdef_util.plugin_set import PluginSet


class TestPluginSet(object):
    def setup(self):
        self.plugin_dir = os.path.join(os.path.dirname(__file__), 'test_plugins')
        self.plugin_set = PluginSet(self.plugin_dir)
        self.metadata = {
            'index': 'test',
        }

    def test_registered_plugins(self):
        total_num_plugins = 0
        for name in os.listdir(self.plugin_dir):
            if name.startswith('plugin'):
                total_num_plugins += 1
        assert len(self.plugin_set.enabled_plugins) == total_num_plugins

    def test_registered_plugins_specific_enabled_plugins(self):
        enabled_plugins = ['plugin1']
        plugin_set = PluginSet(self.plugin_dir, enabled_plugins)
        assert len(plugin_set.enabled_plugins) == 1

    def test_registered_plugins_other_enabled_plugins(self):
        enabled_plugins = ['someotherplugin']
        plugin_set = PluginSet(self.plugin_dir, enabled_plugins)
        assert len(plugin_set.enabled_plugins) == 0

    def test_run_plugins_empty_set_plugins(self):
        enabled_plugins = []
        plugin_set = PluginSet(self.plugin_dir, enabled_plugins)
        assert len(plugin_set.enabled_plugins) == 0

    def test_ordered_enabled_plugins(self):
        ordered_plugins = self.plugin_set.ordered_enabled_plugins
        assert ordered_plugins[0]['registration'] == ['apples']
        assert ordered_plugins[1]['registration'] == 'bananas'
        assert ordered_plugins[2]['registration'] == ['*']
        assert ordered_plugins[3]['registration'] == ['oranges']
        assert ordered_plugins[4]['registration'] == ['pears']
        assert ordered_plugins[5]['registration'] == ['grapes']
        assert ordered_plugins[6]['registration'] == ['somesecretvalue']
        assert ordered_plugins[7]['registration'] == ['*']

    def test_run_plugins_matching_key_plugin1(self):
        '''
            Checks to see that we can match on a key
        '''
        message = {'apples': 'sometext', 'otherkey': 'abcd'}

        assert 'unit_test_key' not in message
        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        # Verify that our first plugin ran and was able
        # to modify the message
        assert parsed_message['unit_test_key'] == 'apples'
        assert parsed_message == message
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin1(self):
        '''
            Checks to see that we can match on a value
        '''
        message = {'test': 'apples', 'otherkey': 'abcd'}

        assert 'unit_test_key' not in message
        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert parsed_message['unit_test_key'] == 'apples'
        assert parsed_message == message
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin2(self):
        '''
            Checks to see that we run a second plugin
            that can match individually of the first
            and can individually overwrite the same
            key plugin1 set
        '''
        message = {'bananas': 'test', 'otherkey': 'abcd'}

        assert 'unit_test_key' not in message
        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert parsed_message['unit_test_key'] == 'bananas'
        assert parsed_message == message
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin3(self):
        message = {'test': 'oranges', 'otherkey': 'abcd'}

        assert 'unit_test_key' not in message
        assert 'plugin3_key' not in message
        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert parsed_message['plugin3_key'] == 'oranges'
        assert parsed_message == message
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin4(self):
        '''
            Checks to see that a plugin can return None
            to signal the caller to drop the message
        '''
        message = {'test': 'pears', 'otherkey': 'abcd'}

        assert message is not None
        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert parsed_message is None
        # This is the interesting part here, because we return None
        # I couldn't get message to get assigned to None and have it bubble
        # up back here, so we have to deal with the return as the indicator for when to
        # drop an event
        assert message is not None
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin5(self):
        '''
            Checks to see if we will can modify metadata in a plugin
        '''
        message = {'test': 'grapes', 'otherkey': 'abcd'}

        assert 'plugin5_key' not in self.metadata
        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert parsed_message == message
        assert self.metadata['plugin5_key'] == 'grapes'
        assert parsed_metadata['plugin5_key'] == 'grapes'

    def test_run_plugins_matching_value_plugin6(self):
        '''
            This unit tests checks to see if we modify a message
            in a plugin, that a plugin further down the 'line'
            can register and get the updated message
        '''
        message = {'apples': 'test', 'testkey': 'othervalue'}

        assert 'plugin6_key' not in message
        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert parsed_message['plugin6_key'] == 'plums'
        assert parsed_message == message
        assert parsed_metadata == self.metadata

    def test_run_plugins_matching_value_plugin7(self):
        '''
            Checks to see if we will match on any text using *
        '''
        message = {'test': 'testerson', 'otherkey': 'abcd'}

        assert 'plugin7_key' not in message
        parsed_message, parsed_metadata = self.plugin_set.run_plugins(message, self.metadata)
        assert parsed_message['plugin7_key'] == 'lime'
        assert parsed_message == message
        assert parsed_metadata == self.metadata
