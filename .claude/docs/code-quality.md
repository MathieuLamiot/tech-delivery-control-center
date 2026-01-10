# Code Quality Standards

## Automated Validation

All code changes must pass automated checks before being considered complete.

### Quality Gates

1. **black** - Code formatting
2. **isort** - Import sorting
3. **ruff** - Linting rules
4. **pytest** - Test suite

### Validation Script

Location: `scripts/validate-ci.sh`

This script:
- Activates venv automatically
- Runs all quality checks in sequence
- Reports pass/fail with clear output
- Returns proper exit codes

### Automation Pattern

**Manual verification is not acceptable** - Quality checks must be automated via hooks, not manually run before completion.

The pre-tool-response hook ensures AI validates code automatically.

## CI/CD Alignment

Local validation matches GitHub Actions CI exactly. No surprises when pushing code.
