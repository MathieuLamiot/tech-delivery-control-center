from django.contrib import admin

from .models import SlackChannelConfig, SlackMessageCount


@admin.register(SlackChannelConfig)
class SlackChannelConfigAdmin(admin.ModelAdmin):
    list_display = ("channel_name", "channel_id", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("channel_name", "channel_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SlackMessageCount)
class SlackMessageCountAdmin(admin.ModelAdmin):
    list_display = ("channel", "date", "message_count", "created_at")
    list_filter = ("date", "channel")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("channel__channel_name",)
