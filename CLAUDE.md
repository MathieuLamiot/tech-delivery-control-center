# Claude Code Guide

This project uses Claude Code for AI-assisted development.

## Project Context

Tech Delivery Control Center is a Django service that aggregates engineering metrics and analytics to help engineering leaders monitor team delivery and performance.

## Stack

- Django 6.0
- Django REST Framework
- PostgreSQL (containerized)
- Python 3.14+
- No custom UI: Django Admin + Metabase for visualization

## Development Principles

- Small, iterative changes
- Progressive disclosure in documentation
- Container-first development (Docker)
- Test-driven development with pytest
- CI validation required (automated via hooks)

## Critical Requirements

### Development Environment
**Virtual environment required**: All Python commands must run within `.venv/`
- Scripts handle activation automatically
- See [.claude/docs/development-environment.md](.claude/docs/development-environment.md) for details

### Code Quality
**Manual validation required**: All code must pass linters and tests before completion
- Run manually at task completion if any code was changed: `scripts/validate-ci.sh`
- When `scripts/validate-ci.sh` exits with non-zero status, invoke the ci-failure-handler agent according to its description. 
- See [.claude/docs/code-quality.md](.claude/docs/code-quality.md) for standards

## Agentic System

### Configuration
Pre-configured in `.claude/settings.json` - hooks and agents work out of the box.

### Agents
- **dev-feedback**: Captures feedback learnings in themed documentation
- **ci-failure-handler**: Automatically fixes CI validation failures intelligently

### Documentation Structure
- **CLAUDE.md** (this file) - High-level overview and router
- **`.claude/docs/`** - Themed, detailed documentation:
  - `development-environment.md` - Venv, tooling, configuration patterns
  - `code-quality.md` - Quality gates, validation, automation
  - `optional-features.md` - Pattern for environment-activated features with graceful degradation
- **`.claude/agents/`** - Agent definitions (pure behavior, no content)
- **`.claude/skills/`** - Reusable procedures
- **`.claude/hooks/`** - Hook documentation

### Progressive Disclosure
Documentation grows as patterns emerge. Consult themed docs in `.claude/docs/` for detailed context.
