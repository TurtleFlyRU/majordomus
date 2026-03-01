.PHONY: fmt lint typecheck test ci

fmt:
	ruff format .

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest

ci: fmt lint typecheck test
