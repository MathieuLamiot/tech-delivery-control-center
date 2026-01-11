# Manual Validation Workflow

## Purpose

Validation ensures all CI checks pass before completing a work session. The validation runs **manually at the end of each task completion**, not after every file modification.

## When to Run

**Run validation before handing work back to the user** after completing a task or set of related changes.

## Manual Execution

```bash
./scripts/validate-ci.sh
```

## What It Checks

1. **black** - Code formatting
2. **isort** - Import sorting
3. **ruff** - Linting rules
4. **pytest** - Test suite

## Behavior

- If all checks pass: Task is complete
- If any check fails: Fix issues before completing

## Why Manual Instead of Automatic?

Running validation after every file modification is too aggressive and slows down development. Manual validation at task completion provides better balance between quality and efficiency.

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
