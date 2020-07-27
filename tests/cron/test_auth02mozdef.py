from cron.auth02mozdef import process_msg

import mozdef_client as mozdef

from mozdef_util.utilities.dot_dict import DotDict


class TestAuth0Messages():
    def setup(self):
        sample_event = {
            '_id': '123456789101112131415',
            'auth0_client': {
                'name': 'auth0.js',
                'version': '1.23.4'
            },
            'client_id': 'abcd12345edfg678910',
            'client_name': 'example.mozilla.org',
            'date': '2019-08-01T19:58:58.912Z',
            'description': 'None',
            'details': {'completedAt': '1564689538906',
                        'elapsedTime': 'None',
                        'initiatedAt': 'None',
                        'prompts': [],
                        'session_id': 'ABC12345defgHIJK'},
            'hostname': 'mozilla.org',
            'ip': '1.2.3.4',
            'isMobile': 'False',
            'session_connection': 'Test-Connection',
            'session_connection_id': 'None',
            'type': 'ssa',
            'user_agent': 'Firefox 68.0.0 / Linux 0.0.0',
            'user_id': 'ad|Test-Connection|ttesterson',
            'user_name': 'ttesterson@mozilla.com'
        }
        self.sample_event = DotDict(sample_event)

    def test_sample_event_username(self):
        mozmsg = mozdef.MozDefEvent('http://localhost:9090')
        process_msg(mozmsg, self.sample_event)
        assert mozmsg.details.username == 'ttesterson@mozilla.com'
        assert mozmsg.details.userid == 'ad|Test-Connection|ttesterson'
        assert mozmsg.summary == 'Success Silent Auth by ttesterson@mozilla.com to: example.mozilla.org'

    def test_sample_event_username_nonexistent(self):
        mozmsg = mozdef.MozDefEvent('http://localhost:9090')
        del(self.sample_event['user_name'])
        del(self.sample_event['user_id'])
        process_msg(mozmsg, self.sample_event)
        assert 'username' not in mozmsg.details
        assert 'userid' not in mozmsg.details
