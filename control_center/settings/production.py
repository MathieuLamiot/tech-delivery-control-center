"""
Production settings for control_center project.

This configuration enforces security best practices and requires
explicit environment variable configuration. All critical settings
must be provided - the application will fail to start if they are missing.

Required environment variables:
- SECRET_KEY: Django secret key for cryptographic signing
- ALLOWED_HOSTS: Comma-separated list of allowed hostnames
- DATABASE_URL: PostgreSQL connection URL

Optional environment variables:
- DEBUG: Set to 'True' to enable debug mode (default: False)
- SECURE_SSL_REDIRECT: Set to 'False' to disable SSL redirect (default: True)
- LOG_LEVEL: Logging level (default: INFO)
"""

import os
import re

from .base import *  # noqa: F403, F401

# Security: DEBUG defaults to False in production
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# Security: SECRET_KEY must be provided
try:
    SECRET_KEY = os.environ["SECRET_KEY"]
except KeyError:
    raise ValueError(
        "SECRET_KEY environment variable must be set in production. "
        "Generate one with: openssl rand -hex 32"
    ) from None

# Security: ALLOWED_HOSTS must be configured
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    raise ValueError(
        "ALLOWED_HOSTS environment variable must be set in production. "
        "Example: ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com"
    )

# Remove any empty strings or whitespace
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]


# Database: Require DATABASE_URL
try:
    DATABASE_URL = os.environ["DATABASE_URL"]
except KeyError:
    raise ValueError(
        "DATABASE_URL environment variable must be set in production. "
        "Format: postgresql://user:password@host:port/database"
    ) from None

# Parse DATABASE_URL for PostgreSQL
match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DATABASE_URL)
if not match:
    raise ValueError(
        "DATABASE_URL must be a valid PostgreSQL URL. "
        "Format: postgresql://user:password@host:port/database"
    )

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": match.group(5),
        "USER": match.group(1),
        "PASSWORD": match.group(2),
        "HOST": match.group(3),
        "PORT": match.group(4),
        "CONN_MAX_AGE": 600,  # Connection pooling for better performance
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}


# Security settings
# https://docs.djangoproject.com/en/6.0/ref/settings/#security

SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() in ("true", "1", "yes")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"


# Logging configuration for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
