from alerts.plugins.ip_source_enrichment import enrich

good_ipv4 = '255.0.1.2'
good_ipv6 = '3001:4d9c:b29:12f0::'
bad_ipv4 = '192.168.0.1'
bad_ipv6 = '2001:db8:a0b:12f0::'

known_ips = [
    {
        'range': good_ipv4 + '/8',
        'site': 'office1',
        'format': '{0} known',
    },
    {
        'range': good_ipv6 + '/64',
        'site': 'office2',
        'format': '{0} known',
    }
]

alert_with_ipv4 = {
    'category': 'bro',
    'tags': ['portscan'],
    'summary': 'this is a test alert',
    'details': {
        'sourceipaddress': good_ipv4,
        'destinationipaddress': bad_ipv4,
        'ports': [22, 9001, 25505, 65534]
    }
}

alert_with_ipv6 = {
    'category': 'bro',
    'tags': ['test'],
    'summary': 'Another test alert',
    'details': {
        'sourceipaddress': good_ipv6,
        'destinationipaddress': bad_ipv6,
        'port': [22, 9001, 24404, 65532]
    }
}

alert_with_ipv4_in_summary = {
    'category': 'test',
    'tags': ['ip', 'in', 'summary'],
    'summary': 'Testing:{0} is a random IP in a poorly formatted string'.format(good_ipv4),
    'details': {}
}

alert_with_ipv6_in_summary = {
    'category': 'test',
    'tags': ['ip', 'in', 'summary'],
    'summary': 'Found IPs ["{0}"]'.format(good_ipv6),
    'details': {}
}


class TestIPSourceEnrichment(object):
    def test_ipv4_addrs_enriched(self):
        enriched = enrich(alert_with_ipv4, known_ips)

        assert '{0} known'.format(good_ipv4) in enriched['summary']
        assert len(enriched['details']['sites']) == 1
        assert enriched['details']['sites'][0]['site'] == 'office1'

    def test_ipv6_addrs_enriched(self):
        enriched = enrich(alert_with_ipv6, known_ips)

        assert '{0} known'.format(good_ipv6) in enriched['summary']
        assert len(enriched['details']['sites']) == 1
        assert enriched['details']['sites'][0]['site'] == 'office2'

    def test_ipv4_addrs_in_summary_enriched(self):
        enriched = enrich(alert_with_ipv4_in_summary, known_ips)

        assert '{0} known'.format(good_ipv4) in enriched['summary']
        assert len(enriched['details']['sites']) == 1
        assert enriched['details']['sites'][0]['site'] == 'office1'

    def test_ipv6_addrs_in_summary_enriched(self):
        enriched = enrich(alert_with_ipv6_in_summary, known_ips)

        assert '{0} known'.format(good_ipv6) in enriched['summary']
        assert len(enriched['details']['sites']) == 1
        assert enriched['details']['sites'][0]['site'] == 'office2'

    def test_unrecognized_ipv4_addrs_not_enriched(self):
        enriched = enrich(alert_with_ipv4, known_ips)

        assert '{0} known'.format(bad_ipv4) not in enriched['summary']

    def test_unrecognized_ipv6_addrs_not_enriched(self):
        enriched = enrich(alert_with_ipv6, known_ips)

        assert '{0} known'.format(bad_ipv6) not in enriched['summary']
