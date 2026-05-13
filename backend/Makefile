.PHONY: lint format typecheck test ci

lint:
	uv run ruff check .

format:
	uv run ruff format --check .

typecheck:
	uv run mypy app/

test:
	uv run pytest -x -q

ci: lint format typecheck test
