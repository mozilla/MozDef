import json
import sys


plugin_path = os.path.join(os.path.dirname(__file__), '../../../alerts/plugins')
sys.path.append(plugin_path)

from ip_source_enrichment import enrich


known_ips = [
    {
        'ipVersion': 4,
        'range': '255.0.1.0/8',
        'format': '{1} known',
    },
    {
        'ipVersion': 6,
        'range': 'a02b:0db8:beef::/48',
        'format': '{1} known',
    }
]

alert_with_ipv4 = {
    'category': 'bro',
    'tags': ['portscan'],
    'summary': 'this is a test alert',
    'details': {
        'sourceipaddress': '255.0.1.2',
        'destinationipaddress': '192.168.0.1',
        'ports': [22, 9001, 25505, 65534]
    }
}

alert_with_ipv6 = {
    'category': 'bro',
    'tags': ['test'],
    'summary': 'Another test alert',
    'deails': {
        'sourceipaddress': 'a02b:0db8:beef:32cc:4122:0000',
        'destinationipaddress': 'abcd:beef:3232:9001:0000:1234',
        'port': [22, 9001, 24404, 65532]
    }
}

alert_with_ipv4_in_summary = {
    'category': 'test',
    'tags': ['ip', 'in', 'summary'],
    'summary': 'Testing:255.0.1.232 is a random IP in a poorly formatted string',
    'details': {}
}

alert_with_ipv6_in_summary = {
    'category': 'test',
    'tags': ['ip', 'in', 'summary'],
    'summary': 'Found IPs ["a02b:0db8:beef:32cc:4122:0000"]',
    'details': {}
}


class TestIPSourceEnrichment(object):
    def test_ipv4_addrs_enriched(self):
        enriched = enrich(alert_with_ipv4, known_ips)

        assert '255.0.1.2 known' in enriched['summary']

    
    def test_ipv6_addrs_enriched(self):
        enriched = enrich(alert_with_ipv6, known_ips)

        assert 'a02b:0db8:beef:32cc:4122:0000 known' in enriched['summary']


    def test_ipv4_addrs_in_summary_enriched(self):
        enriched = enrich(alert_with_ipv4_in_summary, known_ips)

        assert '255.0.1.232 known' in enriched['summary']


    def test_ipv6_addrs_in_summary_enriched(self):
        enriched = enrich(alert_with_ipv6_in_summary, known_ips)

        assert 'a02b:0db8:beef:32cc:4122:0000 known' in enriched['summary']


    def test_unrecognized_ipv4_addrs_not_enriched(self):
        enriched = enrich(alert_with_ipv4, known_ips)

        assert '192.168.0.1 known' not in enriched['summary']


    def test_unrecognized_ipv6_addrs_not_enriched(self):
        enriched = enrich(alert_with_ipv6, known_ips)

        assert 'abcd:beef:3232:9001:0000:1234 known' not in enriched['summary']
