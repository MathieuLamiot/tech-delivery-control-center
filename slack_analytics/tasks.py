import logging
from datetime import date, timedelta

from celery import shared_task
from django.conf import settings

from .models import SlackChannelConfig, SlackMessageCount
from .slack_client import SlackAnalyticsClient

logger = logging.getLogger(__name__)


@shared_task
def fetch_and_save_message_counts(target_date=None):
    """
    Celery task to fetch and store message counts for all active channels for a given date.
    If no date is provided, defaults to yesterday.

    Returns early if Slack tokens are not configured.
    """
    # Early bailout if Slack feature is not activated
    if not getattr(settings, "SLACK_BOT_TOKEN", None):
        logger.info(
            "Slack analytics feature is not activated "
            "(SLACK_BOT_TOKEN not configured). Skipping task."
        )
        return {"success": False, "reason": "Feature not activated"}

    if target_date:
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError as e:
            raise ValueError(
                f"Invalid date format for target_date: {target_date}. Expected YYYY-MM-DD."
            ) from e
    else:
        target_date = date.today() - timedelta(days=1)

    client = SlackAnalyticsClient()
    channels = SlackChannelConfig.objects.filter(is_active=True)

    if not channels.exists():
        logger.info("No active Slack channels configured. Skipping task.")
        return {"success": False, "reason": "No active channels"}

    for channel in channels:
        count = client.get_message_count(channel_id=channel.channel_id, date=target_date)
        SlackMessageCount.objects.update_or_create(
            channel=channel, date=target_date, defaults={"message_count": count}
        )
        logger.info(
            f"Saved message count for channel {channel.channel_name}: "
            f"{count} messages on {target_date}"
        )

    return {"success": True, "date": str(target_date), "channels_processed": channels.count()}
