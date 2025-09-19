SHELL := /usr/bin/env bash
VENV_DIR ?= venv
PYTHON ?= python3

.PHONY: all deps venv install-dev brew-tools test lint format clean

all: test

venv:
	# Create a virtual environment if it doesn't exist
	if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "Virtualenv created at $(VENV_DIR)"; \
	fi

deps: venv
	# Activate venv and upgrade pip
	set -euo pipefail; \
	. $(VENV_DIR)/bin/activate; \
	python -m pip install --upgrade pip setuptools wheel; \
	if [ -f requirements-dev.txt ]; then \
		pip install -r requirements-dev.txt; \
	fi

install-dev: deps
	@echo "Developer dependencies installed in $(VENV_DIR). Activate with: source $(VENV_DIR)/bin/activate"

brew-tools:
	@echo "Installing shell tools via Homebrew (requires brew)..."
	if ! command -v brew >/dev/null 2>&1; then \
		echo "Homebrew not found. Install Homebrew first: https://brew.sh"; exit 1; \
	fi
	brew install shellcheck shfmt bats-core || true

test: deps
	@echo "Running pytest..."
	. $(VENV_DIR)/bin/activate; pytest -q || exit 1
	@echo "Running bats tests (requires bats in PATH)..."
	bats tests || true

lint:
	@echo "Running shellcheck on mkvnmp4 (install with 'make brew-tools')"
	shellcheck mkvnmp4 || true

format:
	@echo "Formatting mkvnmp4 with shfmt"
	shfmt -w mkvnmp4 || true

clean:
	rm -rf $(VENV_DIR) .pytest_cache
