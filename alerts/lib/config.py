#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from celery.schedules import crontab, timedelta
import time
import logging

#ALERTS = {
    #'bro_intel.AlertBroIntel': crontab(minute='*/1'),
    #'bro_notice.AlertBroNotice': crontab(minute='*/1'),
    #'bruteforce_ssh.AlertBruteforceSsh': crontab(minute='*/1'),
    #'cloudtrail.AlertCloudtrail': crontab(minute='*/1'),
    #'fail2ban.AlertFail2ban': crontab(minute='*/1'),
    #'duo_fail_open.AlertDuoFailOpen': crontab(minute='*/2'),
    #'amoFailedLogins_pyes.AlertFailedAMOLogin': crontab(minute='*/2'),
    #'hostScannerAlerts_pyes.AlertHostScannerFinding': crontab(minute='*/10'),
    #'deadman.broNSM3': crontab(minute='*/5'),
#}

ALERTS = {
    #'deadman.broNSM': {'schedule': timedelta(minutes=1),'kwargs':dict(hostlist=['nsm3', 'nsm5'])},
    'bruteforce_ssh_pyes.AlertBruteforceSsh': {'schedule': timedelta(minutes=1)},
    'unauth_ssh_pyes.AlertUnauthSSH': {'schedule': timedelta(minutes=1)},
    'confluence_shell_pyes.AlertConfluenceShellUsage': {'schedule': timedelta(minutes=1)},
    'unauth_scan_pyes.AlertUnauthInternalScan': {'schedule': timedelta(minutes=1)},
    'auditd_sftp_pyes.AlertSFTPEvent': {'schedule': timedelta(minutes=1)},
    'proxy_drop_pyes.AlertProxyDrop': {'schedule': timedelta(minutes=1)},
    'duo_authfail_pyes.AlertDuoAuthFail': {'schedule': timedelta(seconds=60)},
    'vpn_duo_auth_failures_pyes.AlertManyVPNDuoAuthFailures': {'schedule': timedelta(minutes=20)},
}


RABBITMQ = {
	'mqserver': 'localhost',
	'mquser': 'mozdef',
	'mqpassword': 'mozdef',
	'mqport': 5672,
	'alertexchange': 'alerts',
	'alertqueue': 'mozdef.alert'
}

ES = {
	'servers': ['http://mozdefqa1.private.scl3.mozilla.com:9200']
}

OPTIONS = {
    'defaulttimezone': 'UTC',
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
            'level': 'DEBUG',
        },
    }
}

logging.Formatter.converter = time.gmtime
