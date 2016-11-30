#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com

from celery.schedules import crontab, timedelta
import time
import logging

# dictionary of alerts/parameters
# examples:
# 'pythonfile.pythonclass':{'schedule': crontab(minute='*/10')},
# 'pythonfile.pythonclass':{'schedule': timedelta(minutes=10),'kwargs':dict(hostlist=['nsm3', 'nsm5'])},

ALERTS={
    'httperrors_pyes.AlertHTTPErrors': {'schedule': crontab(minute='*/1')},
    'duo_fail_open.AlertDuoFailOpen': {'schedule': crontab(minute='*/2')},
    'bruteforce_ssh_pyes.AlertBruteforceSsh': {'schedule': crontab(minute='*/2')},
    'multiple_intel_hits_pyes.AlertMultipleIntelHits': {'schedule':crontab(minute='*/2')},
    'correlated_alerts_pyes.AlertCorrelatedIntelNotice': {'schedule':crontab(minute='*/2')},
    'ssl_blacklist_hit_pyes.AlertSSLBlacklistHit': {'schedule':crontab(minute='*/2')},
    'sshbruteforce_bro_pyes.AlertSSHManyConns': {'schedule':crontab(minute='*/2')},
    'amoFailedLogins_pyes.AlertFailedAMOLogin': {'schedule':crontab(minute='*/2')},
    'ldapAdd_pyes.ldapAdd': {'schedule':crontab(minute='*/2')},
    'ldapDelete_pyes.ldapDelete': {'schedule':crontab(minute='*/2')},
    'hostScannerAlerts_pyes.AlertHostScannerFinding': {'schedule':crontab(minute='*/5')},
    'ldapGroup_pyes.ldapGroupModify': {'schedule':crontab(minute='*/5')},
    'fxaAlerts.AlertAccountCreations': {'schedule': crontab(minute= '*/10')},
    'unauth_ssh_pyes.AlertUnauthSSH': {'schedule': timedelta(minutes=1)},
    'deadman.broNSM': {'schedule':timedelta(minutes=40),'kwargs':dict(hostlist=['nsm1-yvr1-em4-1', 'nsm1-pdx1-em2-1', 'nsm1-tor1-em4-1', 'nsm1-mtv2-p1p1-1', 'nsm1-sfo1-p2p1-1', 'nsmserver1-manager'])},
    'httpauthbruteforce_pyes.AlertHTTPBruteforce': {'schedule': crontab(minute='*/1')},
    'sshbruteforce_bro_pyes.AlertSSHManyConns': {'schedule': crontab(minute='*/2')},
    'httpauthbruteforce_pyes.AlertHTTPBruteforce': {'schedule': crontab(minute='*/2')},
    'bugzillaauthbruteforce_pyes.AlertBugzillaPBruteforce': {'schedule': crontab(minute='*/2')},
    'ssl_blacklist_hit_pyes.AlertSSLBlacklistHit': {'schedule': crontab(minute='*/5')},
    'geomodel.AlertGeomodel': {'schedule': timedelta(minutes=1)},
    'sshioc.AlertSSHIOC': {'schedule': timedelta(minutes=1)},
    'ldapLockout.ldapLockout': {'schedule': timedelta(minutes=1)},
    'confluence_shell_pyes.AlertConfluenceShellUsage': {'schedule': timedelta(minutes=1)},
    'unauth_scan_pyes.AlertUnauthInternalScan': {'schedule': timedelta(minutes=1)},
    'unauth_portscan_pyes.AlertUnauthPortScan': {'schedule': timedelta(minutes=1)},
    'duo_authfail_pyes.AlertDuoAuthFail': {'schedule': timedelta(minutes=1)},
    'ssh_access_signreleng_pyes.AlertAuthSignRelengSSH': {'schedule': timedelta(minutes=20)},
}

RABBITMQ = {
	'mqserver': 'localhost',
	'mquser': 'mozdef',
	'mqpassword': 'UXDv8awNjYt2orxkFUg4t6qm76',
	'mqport': 5672,
	'alertexchange': 'alerts',
	'alertqueue': 'mozdef.alert'
}

ES = {
	'servers': ['http://mozdefes1.private.scl3.mozilla.com:9200',
                'http://mozdefes2.private.scl3.mozilla.com:9200',
                'http://mozdefes3.private.scl3.mozilla.com:9200',
                'http://mozdefes4.private.scl3.mozilla.com:9200',
                'http://mozdefes5.private.scl3.mozilla.com:9200']
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s',
            'datefmt': '%y %b %d, %H:%M:%S',
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'celery.log',
            'formatter': 'standard',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['celery', 'console'],
            'level': 'INFO',
        },
    }
}

logging.Formatter.converter = time.gmtime
