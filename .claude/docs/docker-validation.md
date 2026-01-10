# Docker Validation

## Purpose

Automatically validates Docker configuration changes to ensure:
- Docker images build successfully
- Services start correctly
- Application responds to healthcheck endpoint

This validation complements Python CI checks by catching container-level issues before deployment.

## How It Works

### Automatic Trigger

When Docker-related files change, the PostToolUse hook triggers async validation:

**Trigger Files:**
- `Dockerfile` - Container image definition
- `docker-compose.yml` or `docker-compose.yaml` - Service orchestration
- `requirements.txt` - Python dependencies (affects Docker build)

### Async Execution

Docker validation runs in the background (~60-90 seconds) to avoid blocking:
1. Agent makes Docker-related changes
2. Hook detects changes and starts validation in background
3. Agent continues working immediately
4. Next interaction: Agent sees validation results automatically

This approach ensures fast feedback for Python CI checks while thorough Docker validation completes asynchronously.

### File Detection

The validation script uses `git diff` to detect Docker-related changes:
- Checks unstaged changes: `git diff --name-only`
- Checks staged changes: `git diff --cached --name-only`
- Matches: Dockerfile, docker-compose.yml, docker-compose.yaml, requirements.txt

This means the script works identically whether called by the hook or run manually by humans.

## Validation Process

The validation script performs four critical steps:

### 1. Build Image (No Cache)
```bash
docker compose build --no-cache
```
- Clean build from scratch
- Validates Dockerfile syntax and instructions
- Ensures dependencies resolve correctly
- Catches layer-specific issues

### 2. Start Services
```bash
docker compose up -d
```
- Starts PostgreSQL database
- Starts Django web application
- Validates service dependencies
- Uses unique project name to avoid conflicts with dev containers

### 3. Health Check (60s Timeout)
- Waits for services to become healthy
- Checks every 2 seconds
- Ensures database is ready
- Ensures web service is running

### 4. Endpoint Test (5 Retries)
```bash
curl -f -s http://localhost:$PORT/healthcheck/
```
- Tests `/healthcheck/` endpoint
- Validates response contains `{"status":"ok"}`
- Retries up to 5 times with 2s delays
- Accounts for Django startup time and migrations

### 5. Cleanup
- Always runs (even on failure or interrupt)
- Removes validation containers
- Removes volumes
- Prevents resource leakage

## Notification Files

Validation communicates via files in project root:

### `.docker-validation-running`
- Created when validation starts
- Contains PID of validation process
- Used to detect concurrent validations
- Displayed in hook output if validation still in progress

### `.docker-validation-result`
- Created when validation completes
- Contains:
  - Timestamp
  - Exit code (0 = passed, non-zero = failed)
  - Log file path
  - Status message (PASSED/FAILED)
  - Last 50 lines of log (if failed)
- Automatically displayed in next hook execution
- Provides actionable feedback to agent

### `.docker-validation-TIMESTAMP.log`
- Full validation output
- Timestamped for debugging
- Includes all Docker command output
- Available for detailed investigation if validation fails

### `.docker-validation.lock`
- Prevents concurrent validations
- Contains PID of running validation
- Automatically cleaned up on completion
- Detects and removes stale locks

**Note:** All notification files are git-ignored.

## Concurrent Validation Handling

The lock file mechanism prevents resource conflicts:

1. **First validation starts:**
   - Creates lock file with PID
   - Runs validation

2. **Second validation attempt:**
   - Detects existing lock file
   - Checks if PID is running
   - Skips if already running
   - Proceeds if lock is stale

This ensures:
- Only one validation runs at a time
- No Docker resource conflicts
- No redundant validations
- Efficient resource usage

## Manual Execution

### Run Full Validation
```bash
./scripts/validate-docker.sh
```
Runs complete validation synchronously (blocks until complete).

### Run Async Validation
```bash
./scripts/validate-docker-async.sh &
```
Runs validation in background with notification files.

### Check Validation Status
```bash
# Check if validation is running
if [ -f .docker-validation-running ]; then
  echo "Validation running (PID: $(cat .docker-validation-running))"
fi

# Check previous result
if [ -f .docker-validation-result ]; then
  cat .docker-validation-result
fi
```

### View Full Logs
```bash
# List all validation logs
ls -lt .docker-validation-*.log

# View most recent log
cat $(ls -t .docker-validation-*.log | head -1)
```

## Integration with CI Validation

Docker validation works alongside Python CI checks:

### Python CI (Synchronous)
- Always runs on every hook execution
- Quick (~10-30 seconds)
- Validates: black, isort, ruff, pytest
- Blocks agent response if fails

### Docker Validation (Async)
- Runs only when Docker-related files change
- Slow (~60-90 seconds)
- Validates: build, start, health, endpoint
- Does not block agent response
- Results shown in next interaction

This dual approach ensures:
- Fast feedback loop for Python changes
- Thorough validation for Docker changes
- No unnecessary waiting
- No skipped validations

## Troubleshooting

### Validation Fails to Start
**Symptom:** No validation running, no lock file created

**Possible causes:**
- Script not executable: `chmod +x scripts/validate-docker-async.sh`
- Permission issues: Check file permissions
- Path issues: Run from project root

### Validation Never Completes
**Symptom:** `.docker-validation-running` file persists indefinitely

**Possible causes:**
- Process killed externally
- System shutdown during validation
- Docker daemon issues

**Solution:**
```bash
# Check if process is actually running
ps -p $(cat .docker-validation-running)

# If not running, remove stale files
rm -f .docker-validation-running .docker-validation.lock

# Restart validation
./scripts/validate-docker-async.sh &
```

### Healthcheck Fails
**Symptom:** Validation fails at step 4 (endpoint test)

**Possible causes:**
- Database migrations failing
- Port conflicts
- Application startup errors
- Healthcheck endpoint misconfigured

**Solution:**
```bash
# View full logs
cat $(ls -t .docker-validation-*.log | head -1)

# Check web service logs specifically
docker compose -p control-center-validation-* logs web

# Test endpoint manually
curl http://localhost:8000/healthcheck/
```

### Port Conflicts
**Symptom:** Services fail to start, port already in use

**Possible causes:**
- Development containers still running
- Previous validation didn't cleanup
- Other services using ports 8000 or 5432

**Solution:**
```bash
# Check running containers
docker ps

# Stop dev containers if needed
docker compose down

# Force cleanup of validation containers
docker compose -p control-center-validation down -v --remove-orphans

# Retry validation
./scripts/validate-docker.sh
```

## Best Practices

1. **Don't manually edit notification files** - They're managed by validation scripts

2. **Let async validation complete** - Don't interrupt or kill validation processes manually

3. **Review failed validation logs** - Full logs provide detailed error context

4. **Clean up old logs periodically** - Validation logs accumulate over time
   ```bash
   # Remove logs older than 7 days
   find . -name ".docker-validation-*.log" -mtime +7 -delete
   ```

5. **Test Docker changes locally first** - Run `docker compose up` manually before committing

6. **Monitor validation in CI** - GitHub Actions should also validate Docker builds

## Future Enhancements

Potential improvements for Docker validation:

- **Smoke tests in container** - Run a subset of tests within the container
- **Multi-stage validation** - Quick validation first, thorough validation later
- **Caching strategies** - Reuse builds when only code changes (not dependencies)
- **Parallel container testing** - Test multiple configurations simultaneously
- **Performance metrics** - Track validation duration trends
- **Notification improvements** - Slack/email alerts for failures in CI

These enhancements would be added based on team needs and feedback.
