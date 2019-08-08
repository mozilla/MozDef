from importlib import import_module
from pymongo import MongoClient
from bson.objectid import ObjectId
from celery.schedules import crontab, timedelta
from mozdef_util.utilities.logger import logger

from lib.config import MONGO_URL
from lib.celery_config import CELERY_MONGODB_SCHEDULER_DB, CELERY_MONGODB_SCHEDULER_COLLECTION


def load_and_register_alerts(available_alerts, celery_app):
    client = MongoClient(MONGO_URL)
    celery_db = client[CELERY_MONGODB_SCHEDULER_DB]
    schedulers_db = celery_db[CELERY_MONGODB_SCHEDULER_COLLECTION]

    for alert_name, params in available_alerts.items():
        # Register alerts in celery
        try:
            alert_tokens = alert_name.split(".")
            alert_module_name = alert_tokens[0]
            alert_classname = alert_tokens[-1]
            alert_module = import_module(alert_module_name)
            alert_class = getattr(alert_module, alert_classname)
            celery_app.register_task(alert_class())
        except ImportError as e:
            logger.exception("Error importing {0}: {1}".format(alert_name, e))
            pass
        except Exception as e:
            logger.exception("Generic error registering {0}: {1}".format(alert_name, e))
            pass

        full_path_name = "{0}.{1}".format(alert_module_name, alert_classname)
        alert_schedule = {
            "_cls": "PeriodicTask",
            "name": full_path_name,
            "task": full_path_name,
            "enabled": True,
        }
        if isinstance(params['schedule'], timedelta):
            alert_schedule['interval'] = {
                "every": params['schedule'].total_seconds(),
                "period": "seconds"
            }
        elif isinstance(params['schedule'], crontab):
            alert_schedule['crontab'] = {
                "minute": params['schedule']._orig_minute,
                "hour": params['schedule']._orig_hour,
                "day_of_week": params['schedule']._orig_day_of_week,
                "day_of_month": params['schedule']._orig_day_of_month,
                "month_of_year": params['schedule']._orig_month_of_year,
            }

        # Manage enabled alerts in mongodb and make sure schedule is synced up
        found_alert_schedule = schedulers_db.find_one({'name': full_path_name})
        if not found_alert_schedule:
            alert_schedule['_id'] = ObjectId()
            logger.debug("Inserting schedule for {0} into mongodb".format(full_path_name))
            schedulers_db.insert(alert_schedule)
        else:
            if schedule_differs(alert_schedule, found_alert_schedule):
                logger.debug("Updating schedule for {0} in mongodb".format(full_path_name))
                schedulers_db.replace_one({'name': found_alert_schedule['name']}, alert_schedule)

    # Handle any enabled via web UA and no longer in the alerts file
    mongodb_alerts = schedulers_db.find()
    for mongodb_alert in mongodb_alerts:
        alert_name = mongodb_alert['name']
        if alert_name not in available_alerts:
            logger.info("Removing {0} from mongodb".format(alert_name))
            schedulers_db.delete_one({'name': alert_name})

    log_alert_schedule(schedulers_db)


def log_alert_schedule(schedulers_db):
    mongodb_alerts = schedulers_db.find()
    logger.info("**** Current Alert Schedule ****")
    for mongodb_alert in mongodb_alerts:
        schedule_str = 'UNKNOWN'
        if 'crontab' in mongodb_alert:
            schedule_str = 'crontab: {0} {1} {2} {3} {4}'.format(
                mongodb_alert['crontab']['minute'],
                mongodb_alert['crontab']['hour'],
                mongodb_alert['crontab']['day_of_week'],
                mongodb_alert['crontab']['day_of_month'],
                mongodb_alert['crontab']['month_of_year'],
            )
        elif 'interval' in mongodb_alert:
            schedule_str = 'interval: {0} {1}'.format(
                mongodb_alert['interval']['every'],
                mongodb_alert['interval']['period'],
            )
        logger.info("\t{0}: {1}".format(mongodb_alert['name'], schedule_str))


def schedule_differs(proposed_alert, found_db_alert):
    potential_schedule_keys = ['interval', 'crontab']
    schedules_differ = False
    for keyname in potential_schedule_keys:
        if keyname in proposed_alert:
            if keyname not in found_db_alert:
                schedules_differ = True
            elif found_db_alert[keyname] != proposed_alert[keyname]:
                schedules_differ = True
    return schedules_differ
