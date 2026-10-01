.PHONY: install test lint format bench docker

install:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

bench:
	uv run python -m bench.run

docker:
	docker compose up --build
