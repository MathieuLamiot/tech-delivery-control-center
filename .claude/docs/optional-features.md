# Optional Features Pattern

## Design Principle

The Tech Delivery Control Center supports multiple features that can be activated independently. Each feature follows the "graceful degradation" pattern where missing configuration causes the feature to skip execution rather than cause errors.

## Implementation Pattern

### Environment-Based Activation

Features are activated through environment variables. Missing or `None` values indicate the feature is not active.

```python
# In settings
FEATURE_TOKEN = os.environ.get("FEATURE_TOKEN")  # Returns None if not set

# In feature code
if not getattr(settings, "FEATURE_TOKEN", None):
    logger.info("Feature not activated. Skipping.")
    return {"success": False, "reason": "Feature not activated"}
```

### Key Characteristics

1. **No Hard Dependencies**: App runs without feature configured
2. **Early Bailout**: Check configuration at task start, exit gracefully
3. **Clear Logging**: Log when features skip due to missing configuration
4. **No Errors**: Never raise exceptions for missing optional configuration

## Current Features

### Slack Analytics

**Activation**: `SLACK_BOT_TOKEN` environment variable
**Components**:
- Models: `SlackChannelConfig`, `SlackMessageCount`
- Task: `fetch_and_save_message_counts`
- Schedule: Daily at 4 AM UTC via Celery Beat

**Bailout Logic**:
```python
if not getattr(settings, "SLACK_BOT_TOKEN", None):
    logger.info("Slack analytics feature not activated. Skipping.")
    return {"success": False, "reason": "Feature not activated"}
```

## Adding New Optional Features

When adding new optional features:

1. **Settings**: Add configuration with `None` default in `base.py`, override from environment in environment-specific settings
2. **Early Check**: Check configuration at entry point (task, view, etc.)
3. **Graceful Exit**: Return informative response, don't raise exceptions
4. **Documentation**: Update README.md Features section
5. **Tests**: Test both activated and deactivated states

## Example Template

```python
# settings/base.py
FEATURE_API_KEY = None  # Override in environment-specific settings

# settings/dev.py
FEATURE_API_KEY = os.environ.get("FEATURE_API_KEY")

# tasks.py
@shared_task
def feature_task():
    if not getattr(settings, "FEATURE_API_KEY", None):
        logger.info("Feature not activated. Skipping.")
        return {"success": False, "reason": "Feature not activated"}

    # Feature logic here
    return {"success": True}
```

## Testing Optional Features

Always test both states:

```python
def test_feature_disabled():
    with patch.object(settings, "FEATURE_API_KEY", None):
        result = feature_task()
    assert result["success"] is False

def test_feature_enabled():
    with patch.object(settings, "FEATURE_API_KEY", "test-key"):
        result = feature_task()
    assert result["success"] is True
```
