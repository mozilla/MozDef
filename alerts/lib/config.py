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

ALERTS = {
# 'pythonfile.pythonclass':{'schedule': crontab(minute='*/10')},
# 'pythonfile.pythonclass':{'schedule': timedelta(minutes=10),'kwargs':dict(hostlist=['nsm3', 'nsm5'])},
}

ALERT_PLUGINS = [
    # 'relative pythonfile name (exclude the .py) - EX: sso_dashboard',
]

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
