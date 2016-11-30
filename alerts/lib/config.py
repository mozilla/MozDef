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
    # QA and Prod both
    'bruteforce_ssh.AlertBruteforceSsh': {'schedule': crontab(minute='*/2')}
    'unauth_ssh.AlertUnauthSSH': {'schedule': timedelta(minutes=1)},
    'confluence_shell.AlertConfluenceShellUsage': {'schedule': timedelta(minutes=1)},
    'unauth_scan.AlertUnauthInternalScan': {'schedule': timedelta(minutes=1)},
    'duo_authfail.AlertDuoAuthFail': {'schedule': timedelta(minutes=1)},
    'ssh_access_signreleng.AlertAuthSignRelengSSH': {'schedule': timedelta(minutes=20)},
    'cloudtrail_new_vpn.AlertCloudtrailNewVPN': {'schedule': timedelta(minutes=25)},
    'cloudtrail_delete_bucket.AlertCloudtrailDeleteBucket': {'schedule': timedelta(minutes=25)},
    # Prod only
    'httperrors.AlertHTTPErrors': {'schedule': crontab(minute='*/1')},
    'duo_fail_open.AlertDuoFailOpen': {'schedule': crontab(minute='*/2')},
    'multiple_intel_hits.AlertMultipleIntelHits': {'schedule':crontab(minute='*/2')},
    'correlated_alerts.AlertCorrelatedIntelNotice': {'schedule':crontab(minute='*/2')},
    'ssl_blacklist_hit.AlertSSLBlacklistHit': {'schedule':crontab(minute='*/2')},
    'sshbruteforce_bro.AlertSSHManyConns': {'schedule':crontab(minute='*/2')},
    'amoFailedLogins.AlertFailedAMOLogin': {'schedule':crontab(minute='*/2')},
    'ldapAdd.ldapAdd': {'schedule':crontab(minute='*/2')},
    'ldapDelete.ldapDelete': {'schedule':crontab(minute='*/2')},
    'hostScannerAlerts.AlertHostScannerFinding': {'schedule':crontab(minute='*/5')},
    'ldapGroup.ldapGroupModify': {'schedule':crontab(minute='*/5')},
    'fxaAlerts.AlertAccountCreations': {'schedule': crontab(minute= '*/10')},
    'deadman.broNSM': {'schedule':timedelta(minutes=40),'kwargs':dict(hostlist=['nsm1-yvr1-em4-1', 'nsm1-pdx1-em2-1', 'nsm1-tor1-em4-1', 'nsm1-mtv2-p1p1-1', 'nsm1-sfo1-p2p1-1', 'nsmserver1-manager'])},
    'httpauthbruteforce.AlertHTTPBruteforce': {'schedule': crontab(minute='*/2')},
    'bugzillaauthbruteforce.AlertBugzillaPBruteforce': {'schedule': crontab(minute='*/2')},
    'geomodel.AlertGeomodel': {'schedule': timedelta(minutes=1)},
    'sshioc.AlertSSHIOC': {'schedule': timedelta(minutes=1)},
    'ldapLockout.ldapLockout': {'schedule': timedelta(minutes=1)},
    'unauth_portscan.AlertUnauthPortScan': {'schedule': timedelta(minutes=1)},
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
