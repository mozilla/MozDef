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


ALERTS = {
    'bruteforce_ssh.AlertBruteforceSsh': {'schedule': timedelta(minutes=1)},
    'unauth_ssh.AlertUnauthSSH': {'schedule': timedelta(minutes=1)},
    'confluence_shell.AlertConfluenceShellUsage': {'schedule': timedelta(minutes=1)},
    'unauth_scan.AlertUnauthInternalScan': {'schedule': timedelta(minutes=1)},
    'auditd_sftp.AlertSFTPEvent': {'schedule': timedelta(minutes=1)},
    'proxy_drop.AlertProxyDrop': {'schedule': timedelta(minutes=1)},
    'duo_authfail.AlertDuoAuthFail': {'schedule': timedelta(seconds=60)},
    'vpn_duo_auth_failures.AlertManyVPNDuoAuthFailures': {'schedule': timedelta(minutes=20)},
    'ssh_access_signreleng.AlertAuthSignRelengSSH': {'schedule': timedelta(minutes=10)},
    'cloudtrail_new_vpn.AlertCloudtrailNewVPN': {'schedule': timedelta(minutes=25)},
    'cloudtrail_delete_bucket.AlertCloudtrailDeleteBucket': {'schedule': timedelta(minutes=25)},
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
    'servers': ['http://localhost:9200']
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
