from alerts.actions.triage_bot import message


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


class TestTriageBot(object):
    def test_declines_unrecognized_alert(self):
        msg = _ssh_sensitive_host_alert()

        # Without the `session` tag, the alert should not fire.
        msg['_source']['tags'] = ['test']

        action = message()
        action._test_flag = False
        action.onMessage(msg)

        assert not action._test_flag


    def test_recognizes_ssh_sensitive_host(self):
        msg = _ssh_sensitive_host_alert()

        action = message()
        action._test_flag = False
        action.onMessage(msg)

        assert action._test_flag


    def test_recognizes_duo_bypass_codes_generated(self):
        msg = _duo_bypass_code_gen_alert()

        action = message()
        action._test_flag = False
        action.onMessage(msg)

        assert action._test_flag


    def test_recognizes_duo_bypass_codes_used(self):
        msg = _duo_bypass_code_used_alert()

        action = message()
        action._test_flag = False
        action.onMessage(msg)
        
        assert action._test_flag
