from celery import Celery
from . import config
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_api.settings")


app = Celery("meiduo")

app.config_from_object(config)
app.autodiscover_tasks([
    'celery_tasks.sms',
])
