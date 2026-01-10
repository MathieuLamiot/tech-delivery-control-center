#!/bin/bash

# Docker Validation Script
# Validates Docker build, service startup, and healthcheck

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🐳 Docker Validation Starting...${NC}"

# Use unique project name to avoid conflicts with development containers
PROJECT_NAME="control-center-validation-$$"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Cleanup function
cleanup() {
  echo -e "\n${YELLOW}Cleaning up Docker resources...${NC}"
  docker compose -p "$PROJECT_NAME" down -v --remove-orphans 2>/dev/null || true
}

# Register cleanup on exit
trap cleanup EXIT INT TERM

# Track overall status
ALL_PASSED=true

# Step 1: Build Docker image
echo -e "\n${YELLOW}Step 1/4: Building Docker image...${NC}"
if docker compose -p "$PROJECT_NAME" build --no-cache; then
  echo -e "${GREEN}✅ Docker build passed${NC}"
else
  echo -e "${RED}❌ Docker build failed${NC}"
  ALL_PASSED=false
  exit 1
fi

# Step 2: Start services
echo -e "\n${YELLOW}Step 2/4: Starting services...${NC}"
if docker compose -p "$PROJECT_NAME" up -d; then
  echo -e "${GREEN}✅ Services started${NC}"
else
  echo -e "${RED}❌ Failed to start services${NC}"
  ALL_PASSED=false
  exit 1
fi

# Step 3: Wait for services to be healthy
echo -e "\n${YELLOW}Step 3/4: Waiting for services to be healthy...${NC}"
MAX_WAIT=60
ELAPSED=0
HEALTHY=false

while [ $ELAPSED -lt $MAX_WAIT ]; do
  # Check if web service is running
  if docker compose -p "$PROJECT_NAME" ps web | grep -q "Up"; then
    echo -e "${GREEN}✅ Services are healthy${NC}"
    HEALTHY=true
    break
  fi

  echo -n "."
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done

if [ "$HEALTHY" = false ]; then
  echo -e "\n${RED}❌ Services did not become healthy within ${MAX_WAIT}s${NC}"
  echo -e "\n${YELLOW}Service logs:${NC}"
  docker compose -p "$PROJECT_NAME" logs
  ALL_PASSED=false
  exit 1
fi

# Step 4: Test healthcheck endpoint
echo -e "\n${YELLOW}Step 4/4: Testing healthcheck endpoint...${NC}"

# Get the port mapping for the web service
WEB_PORT=$(docker compose -p "$PROJECT_NAME" port web 8000 | cut -d: -f2)

if [ -z "$WEB_PORT" ]; then
  echo -e "${RED}❌ Could not determine web service port${NC}"
  ALL_PASSED=false
  exit 1
fi

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
  docker compose -p "$PROJECT_NAME" logs web
  ALL_PASSED=false
  exit 1
fi

# Final status
echo ""
if [ "$ALL_PASSED" = true ]; then
  echo -e "${GREEN}✅ All Docker validation checks passed!${NC}"
  exit 0
else
  echo -e "${RED}❌ Docker validation failed. See errors above.${NC}"
  exit 1
fi
