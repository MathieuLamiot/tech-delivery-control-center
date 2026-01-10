#!/bin/bash

# CI Validation Script
# Runs all CI checks (linters + tests) to ensure code quality before completion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

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

# Final status
echo ""
if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✅ All CI checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some CI checks failed. Please fix the issues above.${NC}"
    exit 1
fi
