# Tech Delivery Control Center

A Django-based control center for engineering leaders to monitor team delivery and performance metrics.

## Stack

- **Backend**: Django 6.0 + Django REST Framework
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis
- **UI**: Django Admin panel + Metabase
- **Testing**: pytest
- **Linting**: black, isort, ruff
- **Containerization**: Docker + Docker Compose

## Features

The Control Center supports multiple optional features that can be activated independently through environment variables. Each feature is designed to fail gracefully if not configured, allowing the application to run with only the features you need.

### Slack Analytics

Tracks daily message counts for configured Slack channels. Runs automatically at 4 AM UTC via Celery Beat.

**Activation**: Set `SLACK_BOT_TOKEN` environment variable
**Status**: If not activated, the scheduled task will bail out early without errors

To use:
1. Create a Slack Bot token with `channels:history` scope
2. Set `SLACK_BOT_TOKEN` in your environment (`.env` file or environment variables)
3. Configure channels to monitor via Django Admin (`/admin/slack_analytics/slackchannelconfig/`)
4. The task will run automatically daily at 4 AM UTC

## Development Setup

### Prerequisites

- Python 3.14+
- Docker & Docker Compose

### Local Development

1. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Run development server:
```bash
python manage.py runserver
```

### Docker Development

```bash
docker-compose up
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
ruff check .
```

### CI Validation (All Checks)

Run all CI checks (formatters + linters + tests) at once:
```bash
./scripts/validate-ci.sh
```

This is the same validation that runs in GitHub Actions CI and automatically in the AI system.

## Project Structure

- `control_center/` - Django project settings
- `healthcheck/` - Health check endpoint
- `tests/` - Test suite
- `docs/` - Documentation
- `.claude/` - Claude Code AI development configuration

## AI-Assisted Development

This project uses Claude Code with an agentic system for development.

### Key Files

- [CLAUDE.md](CLAUDE.md) - Main guide for AI behavior and context
- `.claude/settings.json` - Pre-configured hooks and agents
- `.claude/agents/` - Specialized agents (e.g., dev-feedback)
- `.claude/hooks/` - Automation hooks documentation
- `scripts/` - Utility scripts (CI validation, accessible to all)

### Agents

**dev-feedback**: When providing feedback on AI-generated code that requires systemic changes, this agent analyzes the feedback and updates relevant documentation and automation.

### Developer Workflow

1. Make changes (or have AI make them)
2. Run `./scripts/validate-ci.sh` to verify all checks pass (optional - AI runs this automatically)
3. Commit and push
4. CI runs automatically on PR

The AI system is pre-configured in `.claude/settings.json` to run CI validation automatically before completing responses.
