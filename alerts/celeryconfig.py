from celery import Celery
from lib.config import ALERTS, LOGGING
from logging.config import dictConfig

print ALERTS

# Alert files to include
alerts_include = []
for alert in ALERTS.keys():
    alerts_include.append('.'.join((alert).split('.')[:-1]))
alerts_include = list(set(alerts_include))

print alerts_include

app = Celery('alerts',
             broker='amqp://',
             backend='amqp://',
             include=alerts_include)


CELERY_DISABLE_RATE_LIMITS = True
CELERYD_CONCURRENCY = 1
CELERY_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_DEFAULT_QUEUE = 'celery-default'
CELERY_QUEUES = {
    'celery-default': {
        "exchange": "celery-default",
        "binding_key": "celery-default",
    },
}


CELERYBEAT_SCHEDULE = {}

# Register frequency of the tasks in the scheduler
for alert in ALERTS.keys():
    CELERYBEAT_SCHEDULE[alert] = {
        'task': alert,
        'schedule': ALERTS[alert],
        'options': {'queue': 'celery-default', "exchange": "celery-default"},
    }

# Load logging config
dictConfig(LOGGING)

# print CELERYBEAT_SCHEDULE

# Optional configuration, see the application user guide.
# app.conf.update(
#     CELERY_TASK_RESULT_EXPIRES=3600,
# )

app.config_from_object('celeryconfig')

if __name__ == '__main__':
    app.start()
