.PHONY: setup
setup:
	poetry config virtualenvs.in-project true

.PHONY: install-main
install-main:
	poetry install --only main

.PHONY: install-dev
install-dev:
	poetry install --with dev

.PHONY: lint
lint:
	poetry run ruff check . --fix
	poetry run pre-commit run --all-files

.PHONY: test
test:
	poetry run pytest

.PHONY: build
build:
	poetry build

.PHONY: publish
publish:
	poetry publish -u __token__ -p "$$PYPI_TOKEN"
