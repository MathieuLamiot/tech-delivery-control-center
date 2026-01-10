# Claude Code Setup

## Configuration

This project is pre-configured with Claude Code settings in `.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-response": "scripts/validate-ci.sh"
  },
  "agents": {
    "dev-feedback": {
      "path": ".claude/agents/dev-feedback.md",
      "description": "Analyzes feedback on AI-generated code and captures learnings"
    }
  }
}
```

## Automatic Validation

The pre-tool-response hook automatically runs CI checks after code modifications and prompts the AI to fix issues before completing.

## Manual Validation

You can also run validation manually at any time:
```bash
./scripts/validate-ci.sh
```

## Current Setup

- **Virtual Environment**: `.venv/` (automatically activated by scripts)
- **CI Validation Script**: `scripts/validate-ci.sh` (accessible to both humans and AI)
- **Validation Runs**: black, isort, ruff, pytest
- **Agents**: dev-feedback (for capturing feedback learnings)

## Principle

**Progressive Disclosure**: Documentation grows as needed, not prematurely. Start minimal, expand based on actual usage patterns.
