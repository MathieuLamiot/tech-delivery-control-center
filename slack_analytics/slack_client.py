import logging
from datetime import datetime, timedelta

from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackAnalyticsClient:
    """Client for interacting with Slack API for analytics purposes"""

    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)

    def get_message_count(self, channel_id: str, date: datetime) -> int:
        """
        Get the number of messages in a channel for a specific date

        Args:
            channel_id: The Slack channel ID
            date: The date to count messages for

        Returns:
            int: Number of messages
        """
        try:
            # Calculate start and end timestamps for the day
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            start_time = start_datetime.timestamp()
            end_time = end_datetime.timestamp()

            # Initialize variables for pagination
            count = 0
            cursor = None

            while True:
                # Get messages for the time period
                result = self.client.conversations_history(
                    channel=channel_id,
                    oldest=start_time,
                    latest=end_time,
                    cursor=cursor,
                )

                if result["ok"]:
                    # Add the number of messages in this page
                    count += len(result["messages"])

                    # Check if there are more messages
                    if not result["has_more"]:
                        break

                    # Get cursor for next page
                    cursor = result["response_metadata"]["next_cursor"]
                else:
                    raise SlackApiError("Error fetching messages", result)

            return count

        except SlackApiError as e:
            logger.error(f"SlackApiError for channel {channel_id}: {e}")
            return 0
