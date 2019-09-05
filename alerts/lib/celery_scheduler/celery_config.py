import os
from logging.config import dictConfig

from lib.config import LOGGING, RABBITMQ, RESTAPI_URL, RESTAPI_TOKEN


# XXX TBD this should get wrapped into an object that provides pyconfig
if os.getenv("OPTIONS_MQPROTOCOL", "amqp") == "sqs":
    BROKER_URL = "sqs://@"
    BROKER_TRANSPORT_OPTIONS = {'region': os.getenv('OPTIONS_ALERTSQSQUEUEURL').split('.')[1], 'is_secure': True, 'port': 443}
    CELERY_RESULT_BACKEND = None
    alert_queue_name = os.getenv('OPTIONS_ALERTSQSQUEUEURL').split('/')[4]
    CELERY_DEFAULT_QUEUE = alert_queue_name
    CELERY_QUEUES = {
        alert_queue_name: {"exchange": alert_queue_name, "binding_key": alert_queue_name}
    }
else:
    BROKER_URL = "amqp://{0}:{1}@{2}:{3}//".format(
        RABBITMQ["mquser"], RABBITMQ["mqpassword"], RABBITMQ["mqserver"], RABBITMQ["mqport"]
    )
    CELERY_QUEUES = {
        "celery-default": {"exchange": "celery-default", "binding_key": "celery-default"}
    }
    CELERY_DEFAULT_QUEUE = 'celery-default'

CELERY_DISABLE_RATE_LIMITS = True
CELERYD_CONCURRENCY = 1
CELERY_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

# Custom Alert Scheduler
CELERYBEAT_SCHEDULER = "lib.celery_scheduler.alerts_scheduler.AlertsScheduler"
CELERY_RESTAPI_URL = RESTAPI_URL
CELERY_RESTAPI_JWT = RESTAPI_TOKEN

# Load logging config
dictConfig(LOGGING)
