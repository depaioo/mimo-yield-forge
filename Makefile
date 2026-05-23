.PHONY: help install test coverage lint format clean docker

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

test:  ## Run tests
	python -m pytest tests/ -v

coverage:  ## Run tests with coverage
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:  ## Run linters
	python -m ruff check src/ tests/
	python -m mypy src/ --ignore-missing-imports

format:  ## Format code
	python -m black src/ tests/
	python -m ruff check --fix src/ tests/

clean:  ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

docker:  ## Build Docker image
	docker build -t mimo-yield-forge .

docker-run:  ## Run with Docker Compose
	docker-compose up -d

docker-stop:  ## Stop Docker Compose
	docker-compose down
