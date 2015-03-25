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
    'bro_intel.AlertBroIntel': {'schedule': crontab(minute='*/1')},
    'bro_notice.AlertBroNotice': {'schedule': crontab(minute='*/1')},
    'bruteforce_ssh.AlertBruteforceSsh': {'schedule': crontab(minute='*/1')},
    'cloudtrail.AlertCloudtrail': {'schedule': crontab(minute='*/1')},
    'fail2ban.AlertFail2ban': {'schedule': crontab(minute='*/1')},
}


RABBITMQ = {
	'mqserver': 'localhost',
	'mquser': 'guest',
	'mqpassword': 'guest',
	'mqport': 5672,
	'alertexchange': 'alerts',
	'alertqueue': 'mozdef.alert'
}

ES = {
	'servers': ['http://localhost:9200']
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
