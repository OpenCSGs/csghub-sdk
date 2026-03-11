# CSGHub SDK - Makefile
# Usage: make [target]. Run `make help` for targets.

.PHONY: help venv install install-dev build check test lint lint-fix clean

# Default target
help:
	@echo "CSGHub SDK - available targets:"
	@echo "  make venv         - Create .venv (required before install)"
	@echo "  make install      - Install package into .venv (editable)"
	@echo "  make install-dev  - Install with dev deps into .venv"
	@echo "  make build        - Build sdist and wheel"
	@echo "  make check        - Check package metadata"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Lint and format check (ruff)"
	@echo "  make lint-fix     - Auto-fix lint and format"
	@echo "  make clean        - Remove build artifacts and caches"

# All install/build/test/lint use .venv only (no --system). Targets that need .venv depend on venv.
venv:
	@if test -d .venv; then :; else \
		(command -v uv >/dev/null 2>&1 && uv venv .venv || python3 -m venv .venv) && \
		echo "Created .venv. Run: make install-dev"; \
	fi


# uv is a system binary; use VIRTUAL_ENV so it installs into .venv
install: venv
	@if command -v uv >/dev/null 2>&1; then VIRTUAL_ENV="$(CURDIR)/.venv" uv pip install -e .; else .venv/bin/pip install -e .; fi

install-dev: venv
	@if command -v uv >/dev/null 2>&1; then VIRTUAL_ENV="$(CURDIR)/.venv" uv pip install -e ".[dev]"; else .venv/bin/pip install -e ".[dev]"; fi

build: venv install-dev
	.venv/bin/python3 -m build

check: venv install-dev
	.venv/bin/python3 setup.py check

test: venv
	.venv/bin/python3 -m unittest discover -s pycsghub/test -p '*_test.py' -v

lint: venv
	.venv/bin/ruff check . && .venv/bin/ruff format --check .

lint-fix: venv
	.venv/bin/ruff check . --fix && .venv/bin/ruff format .

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .eggs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
