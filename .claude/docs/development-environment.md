# Development Environment

## Virtual Environment

All Python commands must run within the virtual environment located at `.venv/`.

### For Scripts
Scripts should automatically activate the venv:
```bash
source .venv/bin/activate
```

### Pattern Identified
Scripts handle venv activation automatically so both humans and AI can run them without manual activation.

## Shared Tooling Accessibility

**Principle**: Tooling used by both humans and AI should be in root-level folders, not hidden in `.claude/`.

**Examples**:
- ✅ `scripts/validate-ci.sh` - Accessible to all
- ❌ `.claude/scripts/validate-ci.sh` - Hidden, AI-focused only

## Configuration Philosophy

**Pre-configured, not documented**: Configuration should be set up automatically in `.claude/settings.json`, not left as instructions for manual setup.

Users should get working automation out of the box, not setup instructions.
