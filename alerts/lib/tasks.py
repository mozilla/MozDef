from celery import Celery

from lib.celery_scheduler import celery_config
from lib.celery_scheduler.celery_rest_client import CeleryRestClient

app = Celery("alerts")
app.config_from_object(celery_config, force=True)

celery_rest = CeleryRestClient()
celery_rest.load_and_register_alerts()

if __name__ == "__main__":
    app.start()
