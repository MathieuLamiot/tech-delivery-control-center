from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.db import IntegrityError

from .models import SlackChannelConfig, SlackMessageCount
from .slack_client import SlackAnalyticsClient
from .tasks import fetch_and_save_message_counts


@pytest.mark.django_db
class TestSlackChannelConfig:
    """Tests for SlackChannelConfig model"""

    def test_create_channel_config(self):
        """Test creating a Slack channel configuration"""
        channel = SlackChannelConfig.objects.create(
            channel_id="C12345678", channel_name="general", is_active=True
        )
        assert channel.channel_id == "C12345678"
        assert channel.channel_name == "general"
        assert channel.is_active is True
        assert channel.created_at is not None
        assert channel.updated_at is not None

    def test_channel_id_unique_constraint(self):
        """Test that channel_id must be unique"""
        SlackChannelConfig.objects.create(channel_id="C12345678", channel_name="general")
        with pytest.raises(IntegrityError):
            SlackChannelConfig.objects.create(channel_id="C12345678", channel_name="duplicate")


@pytest.mark.django_db
class TestSlackMessageCount:
    """Tests for SlackMessageCount model"""

    def test_create_message_count(self):
        """Test creating a message count record"""
        channel = SlackChannelConfig.objects.create(channel_id="C12345678", channel_name="general")
        message_count = SlackMessageCount.objects.create(
            channel=channel, date=date.today(), message_count=42
        )
        assert message_count.channel == channel
        assert message_count.date == date.today()
        assert message_count.message_count == 42
        assert message_count.created_at is not None

    def test_unique_together_constraint(self):
        """Test that channel and date combination must be unique"""
        channel = SlackChannelConfig.objects.create(channel_id="C12345678", channel_name="general")
        SlackMessageCount.objects.create(channel=channel, date=date.today(), message_count=10)
        with pytest.raises(IntegrityError):
            SlackMessageCount.objects.create(channel=channel, date=date.today(), message_count=20)


class TestSlackAnalyticsClient:
    """Tests for SlackAnalyticsClient"""

    @patch("slack_analytics.slack_client.WebClient")
    def test_get_message_count_single_page(self, mock_web_client):
        """Test getting message count with single page of results"""
        # Mock the Slack API response
        mock_client_instance = MagicMock()
        mock_web_client.return_value = mock_client_instance
        mock_client_instance.conversations_history.return_value = {
            "ok": True,
            "messages": [{"text": "msg1"}, {"text": "msg2"}, {"text": "msg3"}],
            "has_more": False,
        }

        with patch.object(settings, "SLACK_BOT_TOKEN", "xoxb-test-token"):
            client = SlackAnalyticsClient()
            count = client.get_message_count("C12345678", date(2024, 1, 15))

        assert count == 3
        mock_client_instance.conversations_history.assert_called_once()

    @patch("slack_analytics.slack_client.WebClient")
    def test_get_message_count_pagination(self, mock_web_client):
        """Test getting message count with pagination"""
        mock_client_instance = MagicMock()
        mock_web_client.return_value = mock_client_instance

        # Mock paginated responses
        mock_client_instance.conversations_history.side_effect = [
            {
                "ok": True,
                "messages": [{"text": "msg1"}, {"text": "msg2"}],
                "has_more": True,
                "response_metadata": {"next_cursor": "cursor123"},
            },
            {"ok": True, "messages": [{"text": "msg3"}, {"text": "msg4"}], "has_more": False},
        ]

        with patch.object(settings, "SLACK_BOT_TOKEN", "xoxb-test-token"):
            client = SlackAnalyticsClient()
            count = client.get_message_count("C12345678", date(2024, 1, 15))

        assert count == 4
        assert mock_client_instance.conversations_history.call_count == 2

    @patch("slack_analytics.slack_client.WebClient")
    def test_get_message_count_api_error(self, mock_web_client):
        """Test handling of Slack API errors"""
        mock_client_instance = MagicMock()
        mock_web_client.return_value = mock_client_instance
        mock_client_instance.conversations_history.side_effect = Exception("API Error")

        with patch.object(settings, "SLACK_BOT_TOKEN", "xoxb-test-token"):
            client = SlackAnalyticsClient()
            count = client.get_message_count("C12345678", date(2024, 1, 15))

        # Should return 0 on error
        assert count == 0


@pytest.mark.django_db
class TestFetchAndSaveMessageCountsTask:
    """Tests for the Celery task"""

    @patch("slack_analytics.tasks.SlackAnalyticsClient")
    def test_task_with_no_token_configured(self, mock_client_class):
        """Test that task bails out early when SLACK_BOT_TOKEN is not configured"""
        with patch.object(settings, "SLACK_BOT_TOKEN", None):
            result = fetch_and_save_message_counts()

        assert result["success"] is False
        assert result["reason"] == "Feature not activated"
        mock_client_class.assert_not_called()

    @patch("slack_analytics.tasks.SlackAnalyticsClient")
    def test_task_with_no_active_channels(self, mock_client_class):
        """Test that task bails out when no active channels exist"""
        with patch.object(settings, "SLACK_BOT_TOKEN", "xoxb-test-token"):
            result = fetch_and_save_message_counts()

        assert result["success"] is False
        assert result["reason"] == "No active channels"

    @patch("slack_analytics.tasks.SlackAnalyticsClient")
    def test_task_fetches_and_saves_counts(self, mock_client_class):
        """Test successful message count fetching and saving"""
        # Create test channels
        channel1 = SlackChannelConfig.objects.create(
            channel_id="C111", channel_name="general", is_active=True
        )
        channel2 = SlackChannelConfig.objects.create(
            channel_id="C222", channel_name="random", is_active=True
        )

        # Mock client responses
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_message_count.side_effect = [10, 20]

        target_date = date.today() - timedelta(days=1)

        with patch.object(settings, "SLACK_BOT_TOKEN", "xoxb-test-token"):
            result = fetch_and_save_message_counts()

        assert result["success"] is True
        assert result["channels_processed"] == 2
        assert result["date"] == str(target_date)

        # Verify message counts were saved
        count1 = SlackMessageCount.objects.get(channel=channel1, date=target_date)
        count2 = SlackMessageCount.objects.get(channel=channel2, date=target_date)
        assert count1.message_count == 10
        assert count2.message_count == 20

    @patch("slack_analytics.tasks.SlackAnalyticsClient")
    def test_task_with_specific_date(self, mock_client_class):
        """Test task with a specific target date"""
        channel = SlackChannelConfig.objects.create(
            channel_id="C111", channel_name="general", is_active=True
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_message_count.return_value = 15

        target_date = "2024-01-15"

        with patch.object(settings, "SLACK_BOT_TOKEN", "xoxb-test-token"):
            result = fetch_and_save_message_counts(target_date=target_date)

        assert result["success"] is True
        assert result["date"] == target_date

        count = SlackMessageCount.objects.get(channel=channel, date=date(2024, 1, 15))
        assert count.message_count == 15

    @patch("slack_analytics.tasks.SlackAnalyticsClient")
    def test_task_skips_inactive_channels(self, mock_client_class):
        """Test that inactive channels are not processed"""
        SlackChannelConfig.objects.create(channel_id="C111", channel_name="active", is_active=True)
        SlackChannelConfig.objects.create(
            channel_id="C222", channel_name="inactive", is_active=False
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_message_count.return_value = 10

        with patch.object(settings, "SLACK_BOT_TOKEN", "xoxb-test-token"):
            result = fetch_and_save_message_counts()

        assert result["success"] is True
        assert result["channels_processed"] == 1
        assert mock_client.get_message_count.call_count == 1

    @patch("slack_analytics.tasks.SlackAnalyticsClient")
    def test_task_updates_existing_count(self, mock_client_class):
        """Test that task updates existing message count instead of creating duplicate"""
        channel = SlackChannelConfig.objects.create(
            channel_id="C111", channel_name="general", is_active=True
        )
        target_date = date.today() - timedelta(days=1)

        # Create initial count
        SlackMessageCount.objects.create(channel=channel, date=target_date, message_count=10)

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_message_count.return_value = 25

        with patch.object(settings, "SLACK_BOT_TOKEN", "xoxb-test-token"):
            result = fetch_and_save_message_counts()

        assert result["success"] is True

        # Verify count was updated, not duplicated
        counts = SlackMessageCount.objects.filter(channel=channel, date=target_date)
        assert counts.count() == 1
        assert counts.first().message_count == 25
