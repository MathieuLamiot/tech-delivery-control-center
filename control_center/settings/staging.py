"""
Staging settings for control_center project.

This configuration inherits from production settings but relaxes some
restrictions to make staging environments easier to work with. It provides
a production-like setup with debugging capabilities.

Use this for:
- Pre-production testing
- QA environments
- Integration testing with external services

Inherits all production security settings but overrides:
- DEBUG: Enabled for troubleshooting
- SSL/Security: Relaxed for easier access
- Logging: More verbose
"""

from .production import *  # noqa: F403, F401

# Enable debug mode in staging for troubleshooting
DEBUG = True

# Less strict security settings for staging access
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# More verbose logging in staging
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
if "django" in LOGGING:  # noqa: F405
    LOGGING["django"]["level"] = "DEBUG"  # noqa: F405
