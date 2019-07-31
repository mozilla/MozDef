from .positive_test_suite import PositiveTestSuite
from .negative_test_suite import NegativeTestSuite

from mozdef_util.query_models import QueryStringMatch


hostname_test_regex = r'hostname: /(.*\.)*(groupa|groupb)\.(.*\.)*subdomain\.(.*\.)*.*/'
filename_matcher = r'summary: /.*\.(exe|sh)/'

# Note that this has potential for over-matching on foo.bar.baz.com, which needs further validation in alerts
ip_matcher = r'destination: /.*\..{1,3}\..{1,3}\..{1,3}(:.*|\/.*)/'


class TestQueryStringMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = [
            [
                QueryStringMatch('summary: test'), [
                    {'summary': 'test'},
                ]
            ],
            [
                QueryStringMatch('summary: test conf'), [
                    {'summary': 'test'},
                    {'summary': 'conf'},
                    {'summary': 'test conf'},
                ]
            ],
            [
                QueryStringMatch(hostname_test_regex), [
                    {'hostname': 'host.groupa.test.def.subdomain.company.com'},
                    {'hostname': 'host.groupa.test.def.subdomain.company.com'},
                    {'hostname': 'host.groupa.subdomain.domain.company.com'},
                    {'hostname': 'host.groupa.subdomain.domain1.company.com'},
                    {'hostname': 'host.groupa.subdomain.company.com'},
                    {'hostname': 'host1.groupa.subdomain.company.com'},
                    {'hostname': 'host1.groupa.test.subdomain.company.com'},
                    {'hostname': 'host-1.groupa.test.subdomain.domain.company.com'},
                    {'hostname': 'host-v2-test6.groupa.test.subdomain.domain.company.com'},
                    {'hostname': 'host1.groupa.subdomain.domain.company.com'},
                    {'hostname': 'someotherhost1.hgi.groupa.subdomain.domain1.company.com'},
                    {'hostname': 'host2.groupb.subdomain.domain.company.com'},
                ]
            ],
            [
                QueryStringMatch(filename_matcher), [
                    {'summary': 'test.exe'},
                    {'summary': 'test.sh'},
                ]
            ],
            [
                QueryStringMatch(ip_matcher), [
                    {'destination': 'http://1.2.3.4/somepath'},
                    {'destination': 'https://1.2.3.4/somepath'},
                    {'destination': '1.2.3.4/somepath'},
                    {'destination': '1.2.3.4/somepath'},
                    {'destination': '1.2.3.4:443'},
                    {'destination': '1.2.3.4:80'},
                    # Over-match examples (which need to be validated further in alerts)
                    {'destination': 'https://foo.bar.baz.com/somepath'},
                    {'destination': 'foo.bar.baz.com:80'},
                ]
            ],
        ]
        return tests


class TestQueryStringMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = [
            [
                QueryStringMatch('summary: test'), [
                    {'summary': 'example summary'},
                    {'summary': 'example summary tes'},
                    {'summary': 'testing'},
                    {'note': 'test'},
                ]
            ],
            [
                QueryStringMatch('summary: test conf'), [
                    {'summary': 'testing'},
                    {'summary': 'configuration'},
                    {'summary': 'testing configuration'},
                ]
            ],
            [
                QueryStringMatch(hostname_test_regex), [
                    {'hostname': ''},
                    {'hostname': 'host.subdomain.company.com'},
                    {'hostname': 'host.subdomain.domain1.company.com'},
                    {'hostname': 'groupa.abc.company.com'},
                    {'hostname': 'asub.subdomain.company.com'},
                    {'hostname': 'example.com'},
                    {'hostname': 'abc.company.com'},
                    {'hostname': 'host1.groupa.asubdomain.company.com'},
                    {'hostname': 'host1.groupa.subdomaina.company.com'},
                    {'hostname': 'host1.groupaa.subdomain.company.com'},
                    {'hostname': 'host1.agroupb.subdomain.company.com'},
                ]
            ],
            [
                QueryStringMatch(filename_matcher), [
                    {'summary': 'test.exe.abcd'},
                    {'summary': 'testexe'},
                    {'summary': 'test.1234'},
                    {'summary': '.exe.test'},
                ]
            ],
            [
                QueryStringMatch(ip_matcher), [
                    {'destination': 'https://foo.bar.mozilla.com/somepath'},
                    {'destination': 'foo.bar.mozilla.com:80'},
                    {'destination': 'http://example.com/somepath'},
                    {'destination': 'example.com:443'}
                ]
            ],
        ]
        return tests
