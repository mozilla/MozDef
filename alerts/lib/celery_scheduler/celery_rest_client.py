from celery.utils.log import get_logger
from celery import current_app
from requests_jwt import JWTAuth
import requests
import json

from importlib import import_module
from bson.objectid import ObjectId
from celery.schedules import crontab, timedelta
from mozdef_util.utilities.logger import logger
from lib.config import ALERTS, RESTAPI_URL


class CeleryRestClient(object):
    def __init__(self):
        if hasattr(current_app.conf, "CELERY_RESTAPI_JWT"):
            self._restapi_jwt = JWTAuth(current_app.conf.CELERY_RESTAPI_JWT)
            self._restapi_jwt.set_header_format('Bearer %s')
        else:
            self._restapi_jwt = None

        if hasattr(current_app.conf, "CELERY_RESTAPI_URL"):
            self._restapi_url = current_app.conf.CELERY_RESTAPI_URL
            get_logger(__name__).info("alert scheduler using {0}".format(self._restapi_url))
        else:
            raise Exception("Need to define CELERY_RESTAPI_URL")

    def fetch_schedule_dict(self):
        resp = requests.get(self._restapi_url + "/alertsschedules", auth=self._restapi_jwt)
        if not resp.ok:
            raise Exception("Received error {0} from rest api when fetching alerts schedules".format(resp.status_code))
        api_results = json.loads(resp.text)
        return api_results

    def print_schedule(self):
        schedule = self.fetch_schedule_dict()
        get_logger(__name__).info("**** Current Alert Schedule ****")
        for alert_name, details in schedule.items():
            schedule_str = 'UNKNOWN'
            if 'crontab' in details:
                schedule_str = 'crontab: {0} {1} {2} {3} {4}'.format(
                    details['crontab']['minute'],
                    details['crontab']['hour'],
                    details['crontab']['day_of_week'],
                    details['crontab']['day_of_month'],
                    details['crontab']['month_of_year'],
                )
            elif 'interval' in details:
                schedule_str = 'interval: {0} {1}'.format(
                    details['interval']['every'],
                    details['interval']['period'],
                )
            get_logger(__name__).info("\t{0}: {1}".format(alert_name, schedule_str))

    def load_and_register_alerts(self):
        existing_alerts_schedules = self.fetch_schedule_dict()
        alerts_schedules = {}
        for alert_name, params in ALERTS.items():
            # Register alerts in celery
            try:
                alert_tokens = alert_name.split(".")
                alert_module_name = alert_tokens[0]
                alert_classname = alert_tokens[-1]
                alert_module = import_module(alert_module_name)
                alert_class = getattr(alert_module, alert_classname)
                current_app.register_task(alert_class())
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
                alert_schedule['schedule_type'] = 'interval'
                alert_schedule['interval'] = {
                    "every": params['schedule'].total_seconds(),
                    "period": "seconds"
                }
            elif isinstance(params['schedule'], crontab):
                alert_schedule['schedule_type'] = 'crontab'
                alert_schedule['crontab'] = {
                    "minute": params['schedule']._orig_minute,
                    "hour": params['schedule']._orig_hour,
                    "day_of_week": params['schedule']._orig_day_of_week,
                    "day_of_month": params['schedule']._orig_day_of_month,
                    "month_of_year": params['schedule']._orig_month_of_year,
                }

            if alert_name not in existing_alerts_schedules:
                alert_schedule['_id'] = str(ObjectId())
                logger.debug("Inserting schedule for {0} into mongodb".format(full_path_name))
                updated_alert_schedule = alert_schedule
            else:
                # Update schedule if it differs from file to api
                del existing_alerts_schedules[alert_name][existing_alerts_schedules[alert_name]['schedule_type']]
                existing_alerts_schedules[alert_name]['schedule_type'] = alert_schedule['schedule_type']
                existing_alerts_schedules[alert_name][alert_schedule['schedule_type']] = alert_schedule[alert_schedule['schedule_type']]
                updated_alert_schedule = existing_alerts_schedules[alert_name]
            alerts_schedules[alert_name] = updated_alert_schedule
        resp = requests.post(url=RESTAPI_URL + "/updatealertsschedules", data=json.dumps(alerts_schedules), auth=self._restapi_jwt)
        if not resp.ok:
            raise Exception("Received error {0} from rest api when updating alerts schedules".format(resp.status_code))
