import os
import sys
import mock
import importlib
from configlib import OptionParser
from pymongo import MongoClient

from mozdef_util.utilities.dot_dict import DotDict

from tests.http_test_suite import HTTPTestSuite


class RestTestDict(DotDict):
    @property
    def __dict__(self):
        return self


class RestTestSuite(HTTPTestSuite):
    def teardown(self):
        sys.path.remove(self.rest_path)

    def setup(self):
        sample_config = RestTestDict()
        sample_config.configfile = os.path.join(os.path.dirname(__file__), 'index.conf')
        OptionParser.parse_args = mock.Mock(return_value=(sample_config, {}))

        self.rest_path = os.path.join(os.path.dirname(__file__), "../../rest")
        sys.path.insert(0, self.rest_path)
        import plugins
        importlib.reload(plugins)
        from rest import index as rest_index
        self.application = rest_index.application

        super().setup()

        self.mongoclient = MongoClient(
            self.options.mongohost, self.options.mongoport)
