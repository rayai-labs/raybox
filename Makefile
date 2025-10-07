.PHONY: help install test lint format check clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync --extra dev

test:  ## Run unit tests
	uv run pytest

test-all:  ## Run all tests (including integration)
	uv run pytest tests/ --ignore=

test-integration:  ## Run integration tests only
	uv run pytest -m integration

format:  ## Format code with black and ruff
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

lint:  ## Run all linters (ruff, mypy)
	uv run ruff check src/ tests/
	uv run mypy

check:  ## Run all checks (format, lint, test)
	uv run black --check src/ tests/
	uv run ruff check src/ tests/
	uv run mypy
	uv run pytest

clean:  ## Clean up cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

serve:  ## Start Raybox API server
	uv run raybox
