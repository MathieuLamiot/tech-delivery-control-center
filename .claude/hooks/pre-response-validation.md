# Pre-Response Validation Hook

## Purpose

This hook runs automatically before the AI completes a response where Python code was written, ensuring all CI checks pass.

## Configuration

**Automatically configured** in `.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-response": "scripts/validate-ci.sh"
  }
}
```

## Manual Execution

You can also run the validation script manually:
```bash
./scripts/validate-ci.sh
```

## What It Checks

1. **black** - Code formatting
2. **isort** - Import sorting
3. **ruff** - Linting rules
4. **pytest** - Test suite

## Behavior

- If all checks pass: Response proceeds
- If any check fails: AI is prompted to fix issues before completing

## When It Runs

After any tool use that modifies Python files (Edit, Write, NotebookEdit).

## Notes

This ensures code quality gates are always satisfied before the AI considers work complete.
