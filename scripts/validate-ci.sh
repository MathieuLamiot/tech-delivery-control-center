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
if git diff --name-only | grep -qE '^(Dockerfile|docker-compose\.ya?ml|requirements\.txt|control_center/)'; then
  DOCKER_RELATED=true
fi

# Check for staged changes
if git diff --cached --name-only | grep -qE '^(Dockerfile|docker-compose\.ya?ml|requirements\.txt|control_center/)'; then
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

# Docker validation (inline, synchronous)
if [ "$DOCKER_RELATED" = true ]; then
  echo ""
  echo -e "${BLUE}🐳 Docker-related changes detected${NC}"
  echo -e "${BLUE}   Running Docker validation (this may take 30-45 seconds)...${NC}"

  # Check if Docker daemon is running
  if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "   Please start Docker Desktop and try again"
    ALL_PASSED=false
  else
    # Use unique project name to avoid conflicts with dev containers
    DOCKER_PROJECT_NAME="control-center-validation-$$"

    # Cleanup function for Docker resources
    cleanup_docker() {
      echo -e "\n${YELLOW}Cleaning up Docker resources...${NC}"
      docker compose -p "$DOCKER_PROJECT_NAME" down -v --remove-orphans 2>/dev/null || true
    }

    # Register cleanup on exit
    trap cleanup_docker EXIT INT TERM

    # Step 1: Build Docker image (with cache enabled)
    echo -e "\n${YELLOW}Step 1/4: Building Docker image...${NC}"
    if docker compose -p "$DOCKER_PROJECT_NAME" build; then
      echo -e "${GREEN}✅ Docker build passed${NC}"

      # Step 2: Start services
      echo -e "\n${YELLOW}Step 2/4: Starting services...${NC}"
      if docker compose -p "$DOCKER_PROJECT_NAME" up -d; then
        echo -e "${GREEN}✅ Services started${NC}"

        # Step 3: Wait for services to be healthy
        echo -e "\n${YELLOW}Step 3/4: Waiting for services to be healthy...${NC}"
        DOCKER_MAX_WAIT=30
        DOCKER_ELAPSED=0
        DOCKER_HEALTHY=false

        while [ $DOCKER_ELAPSED -lt $DOCKER_MAX_WAIT ]; do
          if docker compose -p "$DOCKER_PROJECT_NAME" ps web | grep -q "Up"; then
            echo -e "${GREEN}✅ Services are healthy${NC}"
            DOCKER_HEALTHY=true
            break
          fi
          echo -n "."
          sleep 2
          DOCKER_ELAPSED=$((DOCKER_ELAPSED + 2))
        done

        if [ "$DOCKER_HEALTHY" = true ]; then
          # Step 4: Test healthcheck endpoint
          echo -e "\n${YELLOW}Step 4/4: Testing healthcheck endpoint...${NC}"

          # Get the port mapping for the web service
          WEB_PORT=$(docker compose -p "$DOCKER_PROJECT_NAME" port web 8000 | cut -d: -f2)

          if [ -n "$WEB_PORT" ]; then
            # Wait a moment for Django to be ready
            sleep 3

            # Test healthcheck with retries
            HEALTHCHECK_PASSED=false
            for i in {1..5}; do
              if curl -f -s "http://localhost:$WEB_PORT/healthcheck/" | grep -q '"status":"ok"'; then
                echo -e "${GREEN}✅ Healthcheck endpoint returned 200 OK with correct response${NC}"
                HEALTHCHECK_PASSED=true
                break
              fi
              echo "Healthcheck attempt $i failed, retrying..."
              sleep 2
            done

            if [ "$HEALTHCHECK_PASSED" = false ]; then
              echo -e "${RED}❌ Healthcheck endpoint failed${NC}"
              echo -e "\n${YELLOW}Web service logs:${NC}"
              docker compose -p "$DOCKER_PROJECT_NAME" logs web
              ALL_PASSED=false
            fi
          else
            echo -e "${RED}❌ Could not determine web service port${NC}"
            ALL_PASSED=false
          fi
        else
          echo -e "\n${RED}❌ Services did not become healthy within ${DOCKER_MAX_WAIT}s${NC}"
          echo -e "\n${YELLOW}Service logs:${NC}"
          docker compose -p "$DOCKER_PROJECT_NAME" logs
          ALL_PASSED=false
        fi
      else
        echo -e "${RED}❌ Failed to start services${NC}"
        ALL_PASSED=false
      fi
    else
      echo -e "${RED}❌ Docker build failed${NC}"
      ALL_PASSED=false
    fi
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
