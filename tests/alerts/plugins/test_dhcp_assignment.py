from alerts.plugins.dhcp_assignment import enrich


def mock_search_fn(result_sets):
    '''Creates a search function that returns a new set of results on each
    call, cycling between each set in result_sets infinitely.

    `result_sets` is a list of results.  One set of results from this list is
    returned on each call.
    '''

    calls = 0

    def search_fn(_query):
        results = result_sets[calls % len(result_sets)]
        calls += 1

        return results

    return search_fn


def test_alert_enriched(self):
    assign_results = {
        'hits': [
            {
                '_source': {
                    'details': {
                        'ts': 1,
                        'mac': 'deadbeef'
                    }
                }
            }
        ]
    }

    user_results = {
        'hits': [
            {
                '_source': {
                    'receivedtimestamp': '2020-01-14T18:56:18.589623+00:00',
                    'summary': 'test=a string,user_name=tester@mozilla.com,o=32'
                }
            }
        ]
    }

    alert = {
        'summary': 'prefix',
        'events': [
            {
                'documentsource': {
                    'details': {
                        'sourceipaddress': '1.2.3.4'
                    }
                }
            }
        ],
        'details': {
            'something': 'original'
        }
    }

    search_window_hours = 1

    search_fn = mock_search_fn([assign_results, user_results])

    enriched = enrich(alert, search_window_hours, search_fn)

    assert enriched['details']['something'] == 'original'
    assert 'ipassignment' in enriched['details']

    assign = enriched['details']['ipassignment']

    assert assign.get('mac') == 'deadbeef'
    assert assign.get('user') == 'tester@mozilla.com'

    assert alert['summary'].startswith('prefix')
    assert 'deadbeef' in alert['summary']
    assert 'tester@mozilla.com' in alert['summary']
