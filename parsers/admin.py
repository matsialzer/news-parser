from parsers.models import NewsLinks
from django.contrib import admin


@admin.register(NewsLinks)
class NewsLinksAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_sent', 'site', 'created_at', 'published_at', 'url')
    list_filter = ('site', 'is_sent')
    search_fields = ('url',)