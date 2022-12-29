from parsers.models import NewsLinks
from django.contrib import admin


@admin.register(NewsLinks)
class NewsLinksAdmin(admin.ModelAdmin):
    list_display = ['id', 'site', 'created_at', 'published_at', 'url']

