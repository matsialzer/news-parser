from __future__ import absolute_import, unicode_literals
from celery import Celery
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.conf import settings

app = Celery("core")

app.conf.update(timezone='Asia/Tashkent')

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks(['parsers'])
