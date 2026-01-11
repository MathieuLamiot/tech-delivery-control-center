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

The PostToolUse hook ensures AI validates code automatically after modifying files.

### File Detection

The validation script uses `git diff` to detect changes:
- Works when called by the hook (after AI changes)
- Works when run manually by humans
- No dependency on hook-specific arguments

## CI/CD Alignment

Local validation matches GitHub Actions CI exactly. No surprises when pushing code.

## Docker Validation

Docker configuration changes trigger comprehensive validation (integrated into validate-ci.sh).

### When It Runs

Automatically triggers when these files change:
- `Dockerfile` - Container image definition
- `docker-compose.yml` / `docker-compose.yaml` - Service orchestration
- `requirements.txt` - Python dependencies (affects Docker build)
- `control_center/` - Django settings, WSGI/ASGI config

### What It Validates

Four-step validation process (synchronous, ~30-45 seconds):

1. **Build** - Docker image builds successfully (with cache enabled)
2. **Start** - All services (web, db, redis, celery) start correctly
3. **Health** - Services become healthy within 30 seconds
4. **Endpoint** - `/healthcheck/` returns `{"status":"ok"}`

### Key Characteristics

- **Synchronous execution** - Script waits for completion, immediate feedback
- **Docker cache enabled** - Fast rebuilds (~30-45s) unless dependencies change
- **Automatic cleanup** - Containers and volumes removed after validation
- **Unique project names** - No conflicts with development containers

### Troubleshooting

**Validation fails:**
- Check logs in validation output (includes service logs on failure)
- Verify Docker daemon is running
- Ensure no port conflicts with dev containers

**Slow validation:**
- First build without cache: 60-90 seconds (expected)
- Subsequent builds with cache: 30-45 seconds (expected)
- Clear cache if needed: `docker builder prune -a`

**Skip Docker validation:**
- Only runs when Docker-related or control_center/ files change
- Python-only changes skip Docker validation entirely
