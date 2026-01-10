#!/bin/bash

# CI Validation Script
# Runs all CI checks (linters + tests) to ensure code quality before completion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Detect Docker-related changes using git
# This works both when called by hook and when run manually by humans
DOCKER_RELATED=false

# Check for unstaged changes
if git diff --name-only | grep -qE '^(Dockerfile|docker-compose\.ya?ml|requirements\.txt)$'; then
  DOCKER_RELATED=true
fi

# Check for staged changes
if git diff --cached --name-only | grep -qE '^(Dockerfile|docker-compose\.ya?ml|requirements\.txt)$'; then
  DOCKER_RELATED=true
fi

echo "🔍 Running CI validation checks..."

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo -e "${RED}❌ Virtual environment not found at .venv/${NC}"
    exit 1
fi

# Track overall status
ALL_PASSED=true

# Run black
echo -e "\n${YELLOW}Running black...${NC}"
if black --check .; then
    echo -e "${GREEN}✅ black passed${NC}"
else
    echo -e "${RED}❌ black failed${NC}"
    ALL_PASSED=false
fi

# Run isort
echo -e "\n${YELLOW}Running isort...${NC}"
if isort --check-only .; then
    echo -e "${GREEN}✅ isort passed${NC}"
else
    echo -e "${RED}❌ isort failed${NC}"
    ALL_PASSED=false
fi

# Run ruff
echo -e "\n${YELLOW}Running ruff...${NC}"
if ruff check .; then
    echo -e "${GREEN}✅ ruff passed${NC}"
else
    echo -e "${RED}❌ ruff failed${NC}"
    ALL_PASSED=false
fi

# Run pytest
echo -e "\n${YELLOW}Running pytest...${NC}"
if pytest; then
    echo -e "${GREEN}✅ pytest passed${NC}"
else
    echo -e "${RED}❌ pytest failed${NC}"
    ALL_PASSED=false
fi

# Trigger Docker validation asynchronously if needed
if [ "$DOCKER_RELATED" = true ]; then
  echo ""
  echo -e "${BLUE}🐳 Docker-related changes detected${NC}"

  # Start async validation
  "$PROJECT_ROOT/scripts/validate-docker-async.sh" &
  DOCKER_PID=$!

  echo "   Starting Docker validation in background (PID: $DOCKER_PID)"
  echo "   This will take ~60-90 seconds to complete"
  echo "   You will be notified of results in your next interaction"
fi

# Check for previous validation results
if [ -f "$PROJECT_ROOT/.docker-validation-result" ]; then
  echo ""
  echo -e "${BLUE}📋 Previous Docker validation result:${NC}"
  cat "$PROJECT_ROOT/.docker-validation-result"
  echo ""
fi

# Check if validation is still running
if [ -f "$PROJECT_ROOT/.docker-validation-running" ]; then
  RUNNING_PID=$(cat "$PROJECT_ROOT/.docker-validation-running" 2>/dev/null || echo "")
  if [ -n "$RUNNING_PID" ] && ps -p "$RUNNING_PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⏳ Docker validation still running in background (PID: $RUNNING_PID)${NC}"
  fi
fi

# Final status
echo ""
if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✅ All CI checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some CI checks failed. Please fix the issues above.${NC}"
    exit 1
fi
