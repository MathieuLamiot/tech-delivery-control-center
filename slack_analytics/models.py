from django.db import models
from django.utils import timezone


class SlackChannelConfig(models.Model):
    """Configuration for which Slack channels to monitor"""

    channel_id = models.CharField(max_length=32, unique=True)
    channel_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "slack_channel_configs"
        verbose_name = "Slack Channel Configuration"
        verbose_name_plural = "Slack Channel Configurations"

    def __str__(self):
        return f"{self.channel_name} ({self.channel_id})"


class SlackMessageCount(models.Model):
    """Daily message count for Slack channels"""

    channel = models.ForeignKey(SlackChannelConfig, on_delete=models.CASCADE)
    date = models.DateField()
    message_count = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "slack_message_counts"
        verbose_name = "Slack Message Count"
        verbose_name_plural = "Slack Message Counts"
        unique_together = ("channel", "date")

    def __str__(self):
        return f"{self.channel.channel_name} - {self.date}: {self.message_count} messages"
