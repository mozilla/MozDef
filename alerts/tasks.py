from celery import Celery

from lib import celery_config
from lib.config import ALERTS as available_alerts
from lib.celery_helper import load_and_register_alerts


app = Celery("alerts")
app.config_from_object(celery_config, force=True)

load_and_register_alerts(available_alerts, app)

if __name__ == "__main__":
    app.start()
