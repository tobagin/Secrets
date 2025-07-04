#!/bin/bash

# Script to run tests for Secrets Password Manager

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running tests for Secrets Password Manager${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip first
echo -e "${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -r tests/requirements.txt

# Install the package in development mode
echo -e "${YELLOW}Installing package in development mode...${NC}"
pip install -e .

# Run tests with coverage
echo -e "${GREEN}Running unit tests...${NC}"
PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH" python -m pytest tests/ -v "$@"

# Run linting if available
if command -v ruff &> /dev/null; then
    echo -e "${GREEN}Running linting...${NC}"
    ruff check src/ tests/
else
    echo -e "${YELLOW}Ruff not available, skipping linting${NC}"
fi

# Run type checking if available
if command -v mypy &> /dev/null; then
    echo -e "${GREEN}Running type checking...${NC}"
    mypy src/secrets --ignore-missing-imports
else
    echo -e "${YELLOW}MyPy not available, skipping type checking${NC}"
fi

# Run black formatting check if available
if command -v black &> /dev/null; then
    echo -e "${GREEN}Checking code formatting...${NC}"
    black --check src/ tests/
else
    echo -e "${YELLOW}Black not available, skipping formatting check${NC}"
fi

echo -e "${GREEN}Test execution completed!${NC}"