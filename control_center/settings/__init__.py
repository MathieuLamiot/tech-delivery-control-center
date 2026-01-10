"""
Django settings auto-loader.

Automatically selects the appropriate settings module based on DJANGO_ENV.
Defaults to 'dev' for development convenience.

Environment selection:
- DJANGO_ENV=dev → control_center.settings.dev
- DJANGO_ENV=production → control_center.settings.production
- DJANGO_ENV=staging → control_center.settings.staging
- Not set → dev (default)

To override in production:
    export DJANGO_ENV=production
    export DJANGO_SETTINGS_MODULE=control_center.settings.production
"""

import os

# Determine which settings module to use
env = os.environ.get("DJANGO_ENV", "dev")

if env == "production":
    from .production import *  # noqa: F403, F401
elif env == "staging":
    from .staging import *  # noqa: F403, F401
elif env == "dev":
    from .dev import *  # noqa: F403, F401
else:
    raise ValueError(f"Unknown DJANGO_ENV: {env}. Must be 'dev', 'staging', or 'production'")
