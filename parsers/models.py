from django.db import models
from django.utils import timezone


class NewsLinks(models.Model):
    class Sites(models.TextChoices):
        ANIQ = 'ANIQ'
        BBC = 'BBC'
        BUGUN = 'BUGUN'
        CHAMPIONAT = 'CHAMPIONAT'
        DARYO = 'DARYO'
        GAZETA = 'GAZETA'
        GOAL24 = 'GOAL24'
        KUN = 'KUN'
        OLAMSPORT = 'OLAMSPORT'
        QALAMPIR = 'QALAMPIR'
        SPORTS = 'SPORTS'
        SPUTNIKNEWS = 'SPUTNIKNEWS'
        STADION = 'STADION'
        UZA = 'UZA'
        ZAMIN = 'ZAMIN'

    site = models.CharField(max_length=100, choices=Sites.choices)

    url = models.URLField(max_length=600)
    content = models.JSONField(null=True, blank=True)

    is_sent = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    err_msg = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

