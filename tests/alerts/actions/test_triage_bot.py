import io
from unittest.mock import patch
import zipfile

import alerts.actions.triage_bot as bot

import boto3
import moto
import requests_mock


def _ssh_sensitive_host_alert():
    return {
      '_index': 'alerts-201911',
      '_type': '_doc',
      '_id': 'jY29OGBBCfj908U9z3kd',
      '_version': 1,
      '_score': None,
      '_source': {
        'utctimestamp': '2019-11-04T23:04:36.351726+00:00',
        'severity': 'WARNING',
        'summary': 'Session opened on sensitive host by (1): tester [test@website.com]',
        'category': 'session',
        'tags': [
          'session',
          'successful'
        ],
        'events': [
          {
            'documentindex': 'events-20191104',
            'documentsource': {
              'receivedtimestamp': '2019-11-04T23:03:17.740981+00:00',
              'mozdefhostname': 'website.com',
              'details': {
                'program': 'sshd',
                'eventsourceipaddress': '1.2.3.4',
                'username': 'tester'
              },
              'tags': [
                '.source.moz_net'
              ],
              'source': 'authpriv',
              'processname': 'sshd',
              'severity': 'INFO',
              'processid': '27767',
              'summary': 'pam_unix(sshd:session): session opened for user tester by (uid=0)',
              'hostname': 'a.host.website.com',
              'facility': 'authpriv',
              'utctimestamp': '2019-11-04T23:03:17+00:00',
              'timestamp': '2019-11-04T23:03:17+00:00',
              'category': 'syslog',
              'type': 'event',
              'plugins': [
                'parse_sshd',
                'parse_su',
                'sshdFindIP'
              ]
            },
            'documentid': 'X8-tOG4B-YuPuGRRXQta'
          }
        ],
        'ircchannel': None,
        'url': 'website.com',
        'notify_mozdefbot': True,
        'details': {
          'sites': []
        }
      },
      'fields': {
        'utctimestamp': [
          '2019-11-04T23:04:36.351Z'
        ],
        'events.documentsource.utctimestamp': [
          '2019-11-04T23:03:17.000Z'
        ],
        'events.documentsource.receivedtimestamp': [
          '2019-11-04T23:03:17.740Z'
        ],
        'events.documentsource.timestamp': [
          '2019-11-04T23:03:17.000Z'
        ]
      },
      'highlight': {
        'category': [
          '@kibana-highlighted-field@session@/kibana-highlighted-field@'
        ],
        'tags': [
          '@kibana-highlighted-field@session@/kibana-highlighted-field@'
        ]
      },
      'sort': [
        1572908676351
      ]
    }


def _duo_bypass_code_gen_alert():
    return {
      '_index': 'alerts-201911',
      '_type': '_doc',
      '_id': 'Rd8h4ukN9Ob7umH452xl',
      '_version': 1,
      '_score': None,
      '_source': {
        'utctimestamp': '2019-11-04T23:36:36.966791+00:00',
        'severity': 'NOTICE',
        'summary': 'DuoSecurity MFA Bypass codes generated (1): tester@website.com [a.website.com]',
        'category': 'duo',
        'tags': [
          'duosecurity'
        ],
        'events': [
          {
            'documentindex': 'events-20191104',
            'documentsource': {
              'receivedtimestamp': '2019-11-04T23:35:02.313328+00:00',
              'mozdefhostname': 'mozdef.website.com',
              'details': {
                'auto_generated': [],
                'bypass': '',
                'bypass_code_ids': 2,
                'count': 10,
                'eventtype': 'administrator',
                'object': 'tester@website.com',
                'remaining_uses': 1,
                'user_id': '',
                'username': 'API',
                'valid_secs': 0
              },
              'category': 'administration',
              'hostname': 'mozdef.website.com',
              'processid': '23285',
              'processname': '/opt/mozdef/envs/mozdef/cron/duo_logpull.py',
              'severity': 'INFO',
              'summary': 'bypass_create',
              'tags': [
                'duosecurity'
              ],
              'utctimestamp': '2019-11-04T23:31:32+00:00',
              'timestamp': '2019-11-04T23:31:32+00:00',
              'type': 'event',
              'plugins': [],
              'source': 'UNKNOWN'
            },
            'documentid': 'wPPKOG4B-YuPuGRRc2s7'
          }
        ],
        'ircchannel': None,
        'url': 'website.com',
        'notify_mozdefbot': False,
        'details': {
          'sites': []
        }
      },
      'fields': {
        'utctimestamp': [
          '2019-11-04T23:36:36.966Z'
        ],
        'events.documentsource.utctimestamp': [
          '2019-11-04T23:31:32.000Z'
        ],
        'events.documentsource.receivedtimestamp': [
          '2019-11-04T23:35:02.313Z'
        ],
        'events.documentsource.timestamp': [
          '2019-11-04T23:31:32.000Z'
        ]
      },
      'highlight': {
        'category': [
          '@kibana-highlighted-field@duo@/kibana-highlighted-field@'
        ],
        'tags': [
          '@kibana-highlighted-field@duosecurity@/kibana-highlighted-field@'
        ]
      },
      'sort': [
        1572910596966
      ]
    }


def _duo_bypass_code_used_alert():
    return {
      '_index': 'alerts-201910',
      '_type': '_doc',
      '_id': 'n8uK26b1hx3f9OcLa72n',
      '_version': 1,
      '_score': None,
      '_source': {
        'utctimestamp': '2019-10-21T15:55:46.033838+00:00',
        'severity': 'NOTICE',
        'summary': 'DuoSecurity MFA Bypass codes used to log in (1): tester@website.com [website.com]',
        'category': 'bypassused',
        'tags': [
          'duosecurity',
          'used',
          'duo_bypass_codes_used'
        ],
        'events': [
          {
            'documentindex': 'events-20191021',
            'documentsource': {
              'receivedtimestamp': '2019-10-21T15:50:02.339453+00:00',
              'mozdefhostname': 'mozdef.website.com',
              'details': {
                'auto_generated': [],
                'bypass': '',
                'bypass_code_ids': 2,
                'count': 10,
                'eventtype': 'administrator',
                'object': 'tester@website.com',
                'remaining_uses': 1,
                'user_id': '',
                'username': 'API',
                'valid_secs': 0
              },
              'category': 'administration',
              'hostname': 'mozdef.website.com',
              'processid': '15428',
              'processname': '/opt/mozdef/envs/mozdef/cron/duo_logpull.py',
              'severity': 'INFO',
              'summary': 'bypass_create',
              'tags': [
                'duosecurity'
              ],
              'utctimestamp': '2019-10-21T15:48:43+00:00',
              'timestamp': '2019-10-21T15:48:43+00:00',
              'type': 'event',
              'plugins': [],
              'source': 'UNKNOWN',
              'alerts': [
                {
                  'index': 'alerts-201910',
                  'id': 'J8b2dR63-kMa62bd-92E'
                }
              ],
              'alert_names': [
                'AlertGenericLoader:duosecurity_bypass_generated'
              ]
            },
            'documentid': '8iMaT3vSO0ddbCe7eaNQ'
          }
        ],
        'ircchannel': None,
        'url': 'website.com',
        'notify_mozdefbot': False,
        'details': {
          'sites': []
        }
      },
      'fields': {
        'events.documentsource.utctimestamp': [
          '2019-10-21T15:48:43.000Z'
        ],
        'events.documentsource.receivedtimestamp': [
          '2019-10-21T15:50:02.339Z'
        ],
        'events.documentsource.timestamp': [
          '2019-10-21T15:48:43.000Z'
        ],
        'utctimestamp': [
          '2019-10-21T15:55:46.033Z'
        ]
      },
      'highlight': {
        'category': [
          '@kibana-highlighted-field@bypassused@/kibana-highlighted-field@'
        ]
      },
      'sort': [
        1571673346033
      ]
    }


def _ssh_access_releng_alert():
    return {
      '_index': 'alerts-201911',
      '_type': '_doc',
      '_id': '8UtbAqm0dFl4qd9GwkA2',
      '_version': 1,
      '_score': None,
      '_source': {
        'utctimestamp': '2019-11-05T01:14:57.912292+00:00',
        'severity': 'NOTICE',
        'summary': 'SSH login from 10.49.48.100 on releng.website.com as user tester',
        'category': 'access',
        'tags': [
          'ssh'
        ],
        'events': [
          {
            'documentindex': 'events-20191105',
            'documentsource': {
              'receivedtimestamp': '2019-11-05T01:13:25.818826+00:00',
              'mozdefhostname': 'mozdef4.private.mdc1.mozilla.com',
              'details': {
                'id': '9637193494562349801',
                'source_ip': '4.3.2.1',
                'program': 'sshd',
                'message': 'Accepted publickey for tester from 4.3.2.1 port 36998 ssh2',
                'received_at': '2019-11-05T01:08:17Z',
                'generated_at': '2019-11-04T17:08:17Z',
                'display_received_at': 'Nov 05 01:08:17',
                'source_id': 835214730,
                'source_name': 'other.website.com',
                'hostname': 'releng.website.com',
                'severity': 'Info',
                'facility': 'Auth',
                'sourceipaddress': '4.3.2.1',
                'sourceipv4address': '4.3.2.1'
              },
              'tags': [
                'papertrail',
                'releng'
              ],
              'utctimestamp': '2019-11-04T17:08:17+00:00',
              'timestamp': '2019-11-04T17:08:17+00:00',
              'hostname': 'releng.website.com',
              'summary': 'Accepted publickey for tester from 4.3.2.1 port 36998 ssh2',
              'severity': 'INFO',
              'category': 'syslog',
              'type': 'event',
              'plugins': [
                'parse_sshd',
                'parse_su',
                'sshdFindIP',
                'ipFixup',
                'geoip'
              ],
              'processid': 'UNKNOWN',
              'processname': 'UNKNOWN',
              'source': 'UNKNOWN'
            },
            'documentid': 'hsudfg92123ASDf234rm'
          }
        ],
        'ircchannel': 'infosec-releng-alerts',
        'notify_mozdefbot': True,
        'details': {
          'sourceipv4address': '4.3.2.1',
          'sourceipaddress': '4.3.2.1',
          'sites': []
        }
      },
      'fields': {
        'utctimestamp': [
          '2019-11-05T01:14:57.912Z'
        ],
        'events.documentsource.details.generated_at': [
          '2019-11-04T17:08:17.000Z'
        ],
        'events.documentsource.details.received_at': [
          '2019-11-05T01:08:17.000Z'
        ],
        'events.documentsource.utctimestamp': [
          '2019-11-04T17:08:17.000Z'
        ],
        'events.documentsource.receivedtimestamp': [
          '2019-11-05T01:13:25.818Z'
        ],
        'events.documentsource.timestamp': [
          '2019-11-04T17:08:17.000Z'
        ]
      },
      'highlight': {
        'category': [
          '@kibana-highlighted-field@access@/kibana-highlighted-field@'
        ],
        'tags': [
          '@kibana-highlighted-field@ssh@/kibana-highlighted-field@'
        ]
      },
      'sort': [
        1572916497912
      ]
    }


def _person_api_profile():
    return {
        'created': {
            'value': '2019-02-27T11:23:00.000Z',
        },
        'identities': {
            'mozilla_ldap_primary_email': {
                'value': 'test@email.com'
            }
        },
        'first_name': {
            'value': 'tester'
        },
        'last_name': {
            'value': 'mctestperson'
        },
        'alternative_name': {
            'value': 'testing'
        },
        'primary_email': {
            'value': 'test@email.com'
        }
    }


class TestTriageBot(object):
    '''Unit tests for the triage bot alert plugin.
    '''

    def test_declines_unrecognized_alert(self):
        msg = _ssh_sensitive_host_alert()

        # Without the `session` tag, the alert should not fire.
        msg['_source']['tags'] = ['test']

        action = bot.message()
        action._test_flag = False
        action.onMessage(msg)

        assert not action._test_flag


    def test_recognizes_ssh_sensitive_host(self):
        msg = _ssh_sensitive_host_alert()

        action = bot.message()
        action._test_flag = False
        action.onMessage(msg)

        assert action._test_flag


    def test_recognizes_duo_bypass_codes_generated(self):
        msg = _duo_bypass_code_gen_alert()

        action = bot.message()
        action._test_flag = False
        action.onMessage(msg)

        assert action._test_flag


    def test_recognizes_duo_bypass_codes_used(self):
        msg = _duo_bypass_code_used_alert()

        action = bot.message()
        action._test_flag = False
        action.onMessage(msg)
        
        assert action._test_flag


    def test_recognizes_ssh_access_releng(self):
        msg = _ssh_access_releng_alert()

        action = bot.message()
        action._test_flag = False
        action.onMessage(msg)

        assert action._test_flag


class TestPersonAPI:
    '''Unit tests for the Person API client code specific to the triage bot.
    '''

    def test_authenticate_handles_well_formed_responses(self):
        params = bot.AuthParams(
            client_id='testid',
            client_secret='secret',
            audience='wonderful',
            scope='client:read',
            grants='read_acccess')

        with requests_mock.mock() as mock_http:
            mock_http.post('http://person.api.com', json={
                'access_token': 'testtoken'
            })

            tkn = bot.authenticate('http://person.api.com', params)

            assert tkn == 'testtoken'


    def test_authenticate_handles_unexpected_response(self):
        params = bot.AuthParams(
            client_id='testid',
            client_secret='secret',
            audience='wonderful',
            scope='client:read',
            grants='read_acccess')

        with requests_mock.mock() as mock_http:
            mock_http.post('http://person.api.com', text='Not authenticated')

            tkn = bot.authenticate('http://person.api.com', params)

            assert tkn is None


    def test_primary_username_handles_well_formed_responses(self):
        with requests_mock.mock() as mock_http:
            mock_http.get(
                'http://person.api.com/v2/user/primary_username/testuser',
                json=_person_api_profile())

            profile = bot.primary_username(
                'http://person.api.com', 'testtoken', 'testuser')

            assert profile.primary_email == 'test@email.com'
            assert profile.first_name == 'tester'
            assert profile.alternative_name == 'testing'


    def test_primary_username_handles_unexpected_response(self):
        with requests_mock.mock() as mock_http:
            mock_http.get(
                'http://person.api.com/v2/user/primary_username/testuser',
                json={})

            profile = bot.primary_username(
                'http://person.api.com', 'testtoken', 'testuser')

            assert profile is None


    @moto.mock_lambda
    def test_dispatch(self):
        region = 'us-west-2'
        fn_name = 'test_fn'

        raw_code = 'def lambda_handler(event, context):\n\treturn event'
        zip_output = io.BytesIO()
        zip_file = zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED)
        zip_file.writestr('lambda_function.py', raw_code)
        zip_file.close()
        zip_output.seek(0)
        code = zip_output.read()

        cfg = bot.DispatchConfig(
            access_key_id='',
            secret_access_key='',
            region=region,
            function_name=fn_name
        )

        request = bot.AlertTriageRequest(
            identifier='abcdef0123',
            alert=bot.AlertLabel.SSH_ACCESS_SIGN_RELENG,
            summary='test alert',
            user='test@user.com'
        )

        conn = boto3.client('lambda', region)
        conn.create_function(
            FunctionName=fn_name,
            Runtime='python3.6',
            Role='test-iam-role',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': code},
            Description='Test function',
            Timeout=5,
            MemorySize=128,
            Publish=True
        )

        status = bot.dispatch(request, cfg)

        assert status == bot.DispatchResult.SUCCESS
