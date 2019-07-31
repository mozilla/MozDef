import pytest

import os
from mozdef_util.state import State, StateParsingError

states_directory_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'states')


class TestStateBasicInit(object):
    def test_basic_initializer(self):
        state_path = os.path.join(states_directory_location, 'example_state.json')
        state = State(state_path)
        assert state_path in state.filename
        assert state.data['lastrun'] == '2017-04-18T16:30:02.446816+00:00'

    def test_nonexisting_state_file(self):
        state_path = os.path.join(states_directory_location, 'nofileexists.json')
        state = State(state_path)
        assert state.data == {}

    def test_bad_state_file(self):
        state_path = os.path.join(states_directory_location, 'malformed_state.json')
        with pytest.raises(StateParsingError) as state_exception:
            State(state_path)
        expected_message = state_path + " state file found but isn't a recognized json format"
        assert str(state_exception.value) == expected_message


class TestStateSave(object):
    def delete_state_file(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def setup(self):
        self.filepath = os.path.join(states_directory_location, 'writable_state.json')
        self.delete_state_file()

    def teardown(self):
        self.delete_state_file()

    def test_write_state_file(self):
        state = State(self.filepath)
        assert not os.path.exists(self.filepath)
        assert state.data == {}
        state.data['randomkey'] = 'randomvalue'
        state.save()
        assert os.path.exists(self.filepath)
        state = State(self.filepath)
        assert state.data['randomkey'] == 'randomvalue'
