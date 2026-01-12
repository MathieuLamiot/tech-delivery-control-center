# Slack Analytics - Message per Channel

The Slack Analytics feature automatically collects daily message counts from configured Slack channels. This data helps engineering leaders monitor team communication patterns and channel activity.

## User Setup Guide

### Prerequisites

- A Slack workspace where you have permission to create/install apps
- Access to Django Admin interface
- Running Celery worker and Celery Beat scheduler
- Redis instance (for Celery broker/backend)

### Step 1: Create Slack Bot Token

1. Go to [Slack API Console](https://api.slack.com/apps)
2. Create a new app or select an existing one
3. Navigate to **OAuth & Permissions**
4. Add the following Bot Token Scope:
   - `channels:history` - View messages and other content in public channels
5. Install the app to your workspace
6. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### Step 2: Configure Environment Variable

Set the `SLACK_BOT_TOKEN` environment variable with your bot token:

**For Docker (recommended)**:
Add to your `docker-compose.yml` under the `celery-beat` service:
```yaml
environment:
  - SLACK_BOT_TOKEN=xoxb-your-token-here
```

Or use a `.env` file:
```bash
SLACK_BOT_TOKEN=xoxb-your-token-here
```

**For local development**:
```bash
export SLACK_BOT_TOKEN=xoxb-your-token-here
```

### Step 3: Configure Channels to Monitor

1. Start your Django server
2. Navigate to Django Admin: `/admin/slack_analytics/slackchannelconfig/`
3. Click **Add Slack Channel Config**
4. Fill in the form:
   - **Channel ID**: The Slack channel ID (see below for how to find it)
   - **Channel name**: A human-readable name for reference
   - **Is active**: Check this box to enable monitoring
5. Save the configuration

**Finding a Channel ID in Slack**:
- Right-click on the channel name
- Select **View channel details**
- Scroll down - the Channel ID is at the bottom (format: `C12345678`)

### Step 4: Verify Setup

1. Ensure Celery services are running:
   ```bash
   # Start Celery worker
   celery -A control_center worker -l info

   # Start Celery Beat scheduler
   celery -A control_center beat -l info
   ```

2. The task runs automatically daily at 4:00 AM UTC, or you can trigger it manually:
   ```bash
   python manage.py shell
   >>> from slack_analytics.tasks import fetch_and_save_message_counts
   >>> fetch_and_save_message_counts()
   ```

3. View collected data in Django Admin: `/admin/slack_analytics/slackmessagecount/`

## Viewing Data

### Django Admin Interface

Navigate to `/admin/slack_analytics/slackmessagecount/` to view:
- Message counts by channel and date
- Filtering by date range and channel
- Date hierarchy for easy navigation

### Export to Metabase

The data is stored in the `slack_message_counts` table and can be queried directly in Metabase for visualization and reporting.

**Available fields**:
- `channel_id` - References the channel configuration
- `date` - The date messages were sent
- `message_count` - Number of messages on that date
- `created_at` / `updated_at` - Audit timestamps

## Graceful Degradation

This feature follows an **optional feature pattern** - the application runs perfectly without it configured:

- If `SLACK_BOT_TOKEN` is not set, the task exits silently without errors
- If no channels are configured, the task completes immediately
- If Slack API calls fail, errors are logged but don't crash the task
- Inactive channels are automatically skipped

## Developer Guide

### Entry Points

**Celery Task**: [slack_analytics/tasks.py:6](slack_analytics/tasks.py#L6)
```python
@shared_task
def fetch_and_save_message_counts(target_date: str = None) -> dict
```

**Schedule Configuration**: [control_center/settings/dev.py:81](control_center/settings/dev.py#L81)
```python
CELERY_BEAT_SCHEDULE = {
    "fetch-slack-message-counts-daily": {
        "task": "slack_analytics.tasks.fetch_and_save_message_counts",
        "schedule": crontab(hour=4, minute=0),  # 4:00 AM UTC
    },
}
```

### Task Flow

1. **Early bailout check**: Returns if `SLACK_BOT_TOKEN` is not configured
2. **Date handling**: Parses `target_date` parameter or defaults to yesterday
3. **Channel query**: Fetches all active channels from `SlackChannelConfig`
4. **Message counting loop**: For each channel:
   - Calls `SlackAnalyticsClient.get_message_count(channel_id, date)`
   - Uses `update_or_create()` to save/update count in `SlackMessageCount`
5. **Returns summary**: Status, date processed, and channel count

### Key Components

**Models** ([slack_analytics/models.py](slack_analytics/models.py)):
- `SlackChannelConfig` - Channel monitoring configuration
- `SlackMessageCount` - Daily message count storage (unique per channel + date)

**Slack Client** ([slack_analytics/slack_client.py](slack_analytics/slack_client.py)):
- `SlackAnalyticsClient.get_message_count()` - Fetches message counts via Slack API
- Handles pagination automatically
- Returns 0 on errors (logged)

**Admin Interface** ([slack_analytics/admin.py](slack_analytics/admin.py)):
- `SlackChannelConfigAdmin` - Manage monitored channels
- `SlackMessageCountAdmin` - View historical data (read-only)

**Tests** ([slack_analytics/tests.py](slack_analytics/tests.py)):
- Comprehensive unit tests with mocked Slack API calls
- Tests graceful degradation scenarios
- Tests pagination, error handling, and update logic

### API Permissions Required

The Slack bot requires the following OAuth scope:
- `channels:history` - View messages in public channels

### Database Schema

**Table**: `slack_channel_configs`
```sql
- id (AutoField, PK)
- channel_id (CharField, unique)
- channel_name (CharField)
- is_active (BooleanField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

**Table**: `slack_message_counts`
```sql
- id (AutoField, PK)
- channel_id (ForeignKey to slack_channel_configs)
- date (DateField)
- message_count (IntegerField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
- UNIQUE(channel_id, date)
```

## Troubleshooting

### Task runs but no data appears

1. Check that `SLACK_BOT_TOKEN` is set correctly
2. Verify channels are configured with `is_active=True`
3. Check Celery logs for errors
4. Ensure the bot is added to the channels you want to monitor
5. Verify the bot has `channels:history` permission

### "Missing required scope" error

The Slack bot needs the `channels:history` scope. Go to your Slack app's OAuth settings and add this scope, then reinstall the app to your workspace.

### Task completes but count is always 0

- The bot must be a member of the channel (invite it using `/invite @YourBotName`)
- Verify the channel ID is correct in the Django Admin
- Check that messages exist for the target date

## Future Enhancements

Potential additions to this feature:
- Support for private channels (`groups:history` scope)
- Message sentiment analysis
- Active user counting per channel
- Webhook support for real-time updates
- Custom date range queries via Admin actions
