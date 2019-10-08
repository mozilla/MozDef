from .positive_test_suite import PositiveTestSuite
from .negative_test_suite import NegativeTestSuite

from mozdef_util.query_models import SubnetMatch


class TestSubnetMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = [
            [
                SubnetMatch('details.sourceipaddress', '10.1.1.0/24'), [
                    {
                        'details': {
                            'sourceipaddress': '10.1.1.1'
                        }
                    },
                    {
                        'details': {
                            'sourceipaddress': '10.1.1.200'
                        }
                    },
                    {
                        'details': {
                            'sourceipaddress': '10.1.1.255'
                        }
                    },
                ],
            ],
        ]
        return tests


class TestSubnetMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = [
            [
                SubnetMatch('details.sourceipaddress', '10.1.2.0/24'), [
                    {
                        'details': {
                            'sourceipaddress': '10.1.1.1'
                        }
                    },
                    {
                        'details': {
                            'sourceipaddress': '10.1.1.200'
                        }
                    },
                    {
                        'details': {
                            'sourceipaddress': '10.1.1.255'
                        }
                    },
                    {
                        'details': {
                            'sourceipaddress': '8.1.1.2'
                        }
                    },
                ],
            ],
        ]
        return tests
