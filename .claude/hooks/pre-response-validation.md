# Post Tool Use Validation Hook

## Purpose

This hook runs automatically after the AI uses tools that modify files (Edit, Write, NotebookEdit), ensuring all CI checks pass.

## Configuration

**Automatically configured** in `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": "scripts/validate-ci.sh"
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

After any tool use that modifies files (Edit, Write, NotebookEdit).

## How File Detection Works

The script automatically detects which files have changed using `git diff`:
- Checks unstaged changes: `git diff --name-only`
- Checks staged changes: `git diff --cached --name-only`

This means:
- ✅ Works when run by the hook (after AI makes changes)
- ✅ Works when run manually by humans
- ✅ No dependency on hook-specific arguments

## Notes

This ensures code quality gates are always satisfied before the AI considers work complete.
