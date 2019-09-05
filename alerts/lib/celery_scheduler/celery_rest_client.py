from celery.utils.log import get_logger
from celery import current_app
from requests_jwt import JWTAuth
import requests
import json

from importlib import import_module
from celery.schedules import crontab, timedelta
from mozdef_util.utilities.logger import logger
from lib.config import ALERTS, RESTAPI_URL

from .periodic_task import PeriodicTask


class CeleryRestClient():
    def __init__(self):
        if hasattr(current_app.conf, "CELERY_RESTAPI_JWT") and current_app.conf.CELERY_RESTAPI_JWT != "":
            self._restapi_jwt = JWTAuth(current_app.conf.CELERY_RESTAPI_JWT)
            self._restapi_jwt.set_header_format('Bearer %s')
            get_logger(__name__).info("setting JWT value")
        else:
            self._restapi_jwt = None

        if hasattr(current_app.conf, "CELERY_RESTAPI_URL"):
            self._restapi_url = current_app.conf.CELERY_RESTAPI_URL
            get_logger(__name__).info("alert scheduler using {0}".format(self._restapi_url))
        else:
            raise Exception("Need to define CELERY_RESTAPI_URL")

    def fetch_schedule_dict(self):
        resp = requests.get(self._restapi_url + "/alertschedules", auth=self._restapi_jwt)
        if not resp.ok:
            raise Exception("Received error {0} from rest api when fetching alert schedules: {1}".format(resp.status_code, resp.text))
        return json.loads(resp.text)

    def sync_schedules(self, current_schedule):
        resp = requests.post(url=RESTAPI_URL + "/syncalertschedules", data=json.dumps(current_schedule), auth=self._restapi_jwt)
        if not resp.ok:
            raise Exception("Received error {0} from rest api when updating alerts schedules {1}".format(resp.status_code, resp.data))

    def update_schedules(self, current_schedule):
        resp = requests.post(url=RESTAPI_URL + "/updatealertschedules", data=json.dumps(current_schedule), auth=self._restapi_jwt)
        if not resp.ok:
            raise Exception("Received error {0} from rest api when updating alerts schedules {1}".format(resp.status_code, resp.data))

    def load_and_register_alerts(self):
        existing_alert_schedules = self.fetch_schedule_dict()
        alert_schedules = {}
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
            alert_schedule = {
                "name": alert_name,
                "task": alert_name,
                "enabled": True,
            }
            if 'args' in params:
                alert_schedule['args'] = params['args']
            if 'kwargs' in params:
                alert_schedule['kwargs'] = params['kwargs']

            if isinstance(params['schedule'], timedelta):
                alert_schedule['schedule_type'] = 'interval'
                alert_schedule['celery_schedule'] = {
                    "every": params['schedule'].total_seconds(),
                    "period": "seconds"
                }
            elif isinstance(params['schedule'], crontab):
                alert_schedule['schedule_type'] = 'crontab'
                alert_schedule['celery_schedule'] = {
                    "minute": params['schedule']._orig_minute,
                    "hour": params['schedule']._orig_hour,
                    "day_of_week": params['schedule']._orig_day_of_week,
                    "day_of_month": params['schedule']._orig_day_of_month,
                    "month_of_year": params['schedule']._orig_month_of_year,
                }

            if alert_name not in existing_alert_schedules:
                logger.debug("Inserting schedule for {0} into mongodb".format(alert_name))
                updated_alert_schedule = alert_schedule
            else:
                existing_schedule = existing_alert_schedules[alert_name]
                logger.debug("Updating existing schedule ({0}) with new information into mongodb".format(alert_name))
                existing_schedule['schedule_type'] = alert_schedule['schedule_type']
                existing_schedule['celery_schedule'] = alert_schedule['celery_schedule']
                updated_alert_schedule = existing_schedule

            alert_schedules[alert_name] = PeriodicTask(**updated_alert_schedule).to_dict()
        self.update_schedules(alert_schedules)
