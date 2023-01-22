from django.contrib import admin, messages
from parsers.models import NewsLinks


@admin.register(NewsLinks)
class NewsLinksAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_sent', 'site', 'created_at', 'published_at', 'url')
    list_filter = ('site', 'is_sent')
    search_fields = ('url',)
    actions = ('resend_to_api',)

    @admin.action(description="resend to API")
    def resend_to_api(self, request, queryset):
        sended_posts = queryset.filter(is_sent=True)
        if sended_posts.exists():
            self.message_user(request, "Faqat jo'natilmagan postlarni jo'natish mumkin.", messages.ERROR)
            return
        from parsers.tasks import resend_post_info
        for post in queryset:
            resend_post_info.apply_async(args=(post.id,))
        self.message_user(request, "Qayta jo'natishga yuborildi", messages.INFO)
