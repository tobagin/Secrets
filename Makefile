# Makefile for Secrets Password Manager

.PHONY: help setup test lint format type-check security-check clean run install build dev-install

# Default target
help:
	@echo "Available targets:"
	@echo "  setup          - Set up development environment"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with black and isort"
	@echo "  format-check   - Check code formatting"
	@echo "  type-check     - Run type checking with mypy"
	@echo "  security-check - Run security analysis with bandit"
	@echo "  quality-check  - Run all quality checks (lint, type, security)"
	@echo "  clean          - Clean up build artifacts"
	@echo "  run            - Run the application in development mode"
	@echo "  install        - Install the package"
	@echo "  build          - Build the application with meson"
	@echo "  dev-install    - Install in development mode"
	@echo "  pre-commit     - Set up pre-commit hooks"

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
SRC_DIR := src/secrets
TEST_DIR := tests

# Setup development environment
setup:
	@echo "Setting up development environment..."
	$(PYTHON) -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r tests/requirements.txt
	./venv/bin/pip install -e .
	@echo "Development environment ready!"

# Testing
test:
	@echo "Running all tests..."
	./scripts/run-tests.sh

test-unit:
	@echo "Running unit tests..."
	PYTHONPATH="$(PWD)/src:$$PYTHONPATH" $(PYTHON) -m pytest $(TEST_DIR)/ -v

test-coverage:
	@echo "Running tests with coverage..."
	PYTHONPATH="$(PWD)/src:$$PYTHONPATH" $(PYTHON) -m pytest $(TEST_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

# Code quality
lint:
	@echo "Running linting checks..."
	ruff check $(SRC_DIR)/ $(TEST_DIR)/

format:
	@echo "Formatting code..."
	black $(SRC_DIR)/ $(TEST_DIR)/
	isort $(SRC_DIR)/ $(TEST_DIR)/

format-check:
	@echo "Checking code formatting..."
	black --check $(SRC_DIR)/ $(TEST_DIR)/
	isort --check-only $(SRC_DIR)/ $(TEST_DIR)/

type-check:
	@echo "Running type checks..."
	mypy $(SRC_DIR) --ignore-missing-imports

security-check:
	@echo "Running security analysis..."
	bandit -r $(SRC_DIR)/ -f json -o bandit-report.json || true
	@echo "Security report saved to bandit-report.json"

quality-check: lint format-check type-check security-check
	@echo "All quality checks completed!"

# Pre-commit hooks
pre-commit:
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "Pre-commit hooks installed!"

# Application
run:
	@echo "Running application in development mode..."
	./scripts/run-dev.sh

run-direct:
	@echo "Running application directly..."
	PYTHONPATH="$(PWD)/src:$$PYTHONPATH" $(PYTHON) -m secrets.main

# Build and install
build:
	@echo "Building with meson..."
	meson setup build
	meson compile -C build

install:
	@echo "Installing the package..."
	$(PIP) install .

dev-install:
	@echo "Installing in development mode..."
	$(PIP) install -e .

# Flatpak
flatpak-build:
	@echo "Building Flatpak..."
	flatpak-builder --user --install --force-clean build io.github.tobagin.secrets.yml

flatpak-run:
	@echo "Running Flatpak version..."
	flatpak run io.github.tobagin.secrets

# Release
prepare-release:
	@echo "Preparing release..."
	./scripts/prepare-release.sh

# Cleanup
clean:
	@echo "Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf bandit-report.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Documentation
docs:
	@echo "Generating documentation..."
	# Add documentation generation here if needed

# Development utilities
fix:
	@echo "Auto-fixing code issues..."
	ruff check --fix $(SRC_DIR)/ $(TEST_DIR)/
	$(MAKE) format

check: quality-check test
	@echo "All checks passed!"

# Continuous integration helpers
ci-setup:
	$(PIP) install --upgrade pip
	$(PIP) install -r tests/requirements.txt

ci-test: ci-setup test-coverage quality-check

# Show project statistics
stats:
	@echo "Project statistics:"
	@echo -n "Lines of code: "
	@find $(SRC_DIR) -name "*.py" -exec cat {} \; | wc -l
	@echo -n "Test files: "
	@find $(TEST_DIR) -name "test_*.py" | wc -l
	@echo -n "Python files: "
	@find $(SRC_DIR) $(TEST_DIR) -name "*.py" | wc -l