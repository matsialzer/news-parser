from django.db import models



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

    url = models.URLField(max_length=600)
    site = models.CharField(max_length=100, choices=Sites.choices)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

