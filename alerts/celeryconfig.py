import os
from celery import Celery
from importlib import import_module
from lib.config import ALERTS, LOGGING, RABBITMQ
from logging.config import dictConfig

# Alert files to include
alerts_include = []
for alert in ALERTS.keys():
    alerts_include.append(".".join((alert).split(".")[:-1]))
alerts_include = list(set(alerts_include))

# XXX TBD this should get wrapped into an object that provides pyconfig
if os.getenv("OPTIONS_MQPROTOCOL", "amqp") == "sqs":
    BROKER_URL = "sqs://@"
    BROKER_TRANSPORT_OPTIONS = {'region': os.getenv('OPTIONS_ALERTSQSQUEUEURL').split('.')[1]}
    CELERY_RESULT_BACKEND = None
    alert_queue_name = os.getenv('OPTIONS_ALERTSQSQUEUEURL').split('/')[4]
    CELERY_DEFAULT_QUEUE = alert_queue_name
    CELERY_QUEUES = {
        {alert_queue_name}: {"exchange": "alert_queue_name, "binding_key": alert_queue_name}
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
CELERYBEAT_SCHEDULE = {}

# Register frequency of the tasks in the scheduler
for alert in ALERTS.keys():
    CELERYBEAT_SCHEDULE[alert] = {
        "task": alert,
        "schedule": ALERTS[alert]["schedule"],
        "options": {"queue": "celery-default", "exchange": "celery-default"},
    }
    # add optional parameters:
    if "args" in ALERTS[alert]:
        CELERYBEAT_SCHEDULE[alert]["args"] = ALERTS[alert]["args"]
    if "kwargs" in ALERTS[alert]:
        CELERYBEAT_SCHEDULE[alert]["kwargs"] = ALERTS[alert]["kwargs"]

# Load logging config
dictConfig(LOGGING)

# print CELERYBEAT_SCHEDULE

# Optional configuration, see the application user guide.
# app.conf.update(
#     CELERY_TASK_RESULT_EXPIRES=3600,
# )
app = Celery("alerts", include=alerts_include)
app.config_from_object("celeryconfig", force=True)

# As a result of celery 3 to celery 4, we need to dynamically
# register all of the alert tasks specifically
for alert_namespace in CELERYBEAT_SCHEDULE:
    try:
        alert_tokens = alert_namespace.split(".")
        alert_module_name = alert_tokens[0]
        alert_classname = alert_tokens[1]
        alert_module = import_module(alert_module_name)
        alert_class = getattr(alert_module, alert_classname)
        app.register_task(alert_class())
    except ImportError as e:
        print("Error importing {}").format(alert_namespace)
        print(e)
        pass
    except Exception as e:
        print("Error addding alert")
        print(e)

if __name__ == "__main__":
    app.start()
