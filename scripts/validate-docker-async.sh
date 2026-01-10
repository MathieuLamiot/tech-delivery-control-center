#!/bin/bash

# Async Docker Validation Wrapper
# Runs docker validation and creates notification file

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_ROOT/.docker-validation-$TIMESTAMP.log"
NOTIFICATION_FILE="$PROJECT_ROOT/.docker-validation-result"
LOCK_FILE="$PROJECT_ROOT/.docker-validation.lock"

# Cleanup function
cleanup() {
  rm -f "$LOCK_FILE"
  rm -f "$PROJECT_ROOT/.docker-validation-running"
}

# Register cleanup on exit
trap cleanup EXIT INT TERM

# Check for existing validation
if [ -f "$LOCK_FILE" ]; then
  EXISTING_PID=$(cat "$LOCK_FILE")
  if ps -p "$EXISTING_PID" > /dev/null 2>&1; then
    echo "Docker validation already running (PID: $EXISTING_PID)"
    echo "Skipping duplicate validation."
    exit 0
  else
    # Stale lock file, remove it
    rm -f "$LOCK_FILE"
  fi
fi

# Create lock file with current PID
echo $$ > "$LOCK_FILE"

# Create running indicator with PID
echo $$ > "$PROJECT_ROOT/.docker-validation-running"

# Remove old notification files
rm -f "$NOTIFICATION_FILE"

# Run validation and capture result
"$PROJECT_ROOT/scripts/validate-docker.sh" > "$LOG_FILE" 2>&1
EXIT_CODE=$?

# Create notification file
cat > "$NOTIFICATION_FILE" << EOF
timestamp: $TIMESTAMP
exit_code: $EXIT_CODE
log_file: $LOG_FILE
EOF

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Docker validation PASSED" >> "$NOTIFICATION_FILE"
else
  echo "❌ Docker validation FAILED" >> "$NOTIFICATION_FILE"
  echo "" >> "$NOTIFICATION_FILE"
  echo "=== Last 50 lines of log ===" >> "$NOTIFICATION_FILE"
  tail -50 "$LOG_FILE" >> "$NOTIFICATION_FILE"
fi

exit $EXIT_CODE
