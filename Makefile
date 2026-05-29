.PHONY: install install-dev run lint format test typecheck docker clean

PYTHON ?= python3

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install || true

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check app tests

format:
	ruff format app tests

test:
	pytest

typecheck:
	$(PYTHON) -m mypy app || true

docker:
	docker build -t pdf-ai-backend .

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +

clean-indexes:
	rm -rf faiss_indexes/*
