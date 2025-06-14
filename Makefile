.PHONY: lint format lint-fix test install dev-install clean

# Linting and formatting
lint:
	flake8 --max-line-length=120 --extend-ignore=F541 .

format:
	black .

lint-fix: format lint

# Testing
test:
	python -m pytest

# Installation
install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Help
help:
	@echo "Available commands:"
	@echo "  make lint      - Run flake8 linter"
	@echo "  make format    - Run black formatter" 
	@echo "  make lint-fix  - Format code then run linter"
	@echo "  make test      - Run pytest tests"
	@echo "  make install   - Install package"
	@echo "  make dev-install - Install with dev dependencies"
	@echo "  make clean     - Clean up Python cache files"