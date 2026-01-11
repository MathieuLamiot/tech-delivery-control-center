"""
Development settings for control_center project.

This configuration is optimized for local development with:
- Permissive ALLOWED_HOSTS (fixes Docker 0.0.0.0 access)
- Auto-detection of DATABASE_URL for Docker PostgreSQL
- SQLite fallback for non-Docker development
- Hardcoded SECRET_KEY for convenience
- Debug mode enabled
"""

import os
import re

from .base import *  # noqa: F403, F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow Docker container access and localhost
# This fixes the DisallowedHost error when accessing via 0.0.0.0:8000
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "[::1]",  # IPv6 localhost
]

# SECURITY WARNING: keep the secret key used in production secret!
# This is the same dev key from the original settings - safe for development
SECRET_KEY = "django-insecure-gdo%oqng)*+^l!(5j@=khlfpq9c@jz%8$)nwts07h9d8(z8c+i"


# Database
# Auto-detect DATABASE_URL (from Docker) or default to SQLite

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Parse DATABASE_URL manually for PostgreSQL
    # Format: postgresql://user:password@host:port/database
    match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DATABASE_URL)
    if match:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": match.group(5),
                "USER": match.group(1),
                "PASSWORD": match.group(2),
                "HOST": match.group(3),
                "PORT": match.group(4),
            }
        }
    else:
        raise ValueError(
            f"Invalid DATABASE_URL format: {DATABASE_URL}. "
            "Expected: postgresql://user:password@host:port/database"
        )
else:
    # SQLite for local development without Docker
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }


# Development-friendly email backend (prints to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Celery Configuration for Development
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Celery Beat Schedule - Daily Slack Analytics at 4AM UTC
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "fetch-slack-message-counts-daily": {
        "task": "slack_analytics.tasks.fetch_and_save_message_counts",
        "schedule": crontab(hour=4, minute=0),  # Run daily at 4:00 AM UTC
    },
}


# Slack Configuration (Optional Feature)
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
