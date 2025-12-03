.PHONY: help install install-dev install-all test lint format type-check clean build

help:
	@echo "Comandos disponíveis:"
	@echo "  make install       - Instala o pacote em modo normal"
	@echo "  make install-dev   - Instala com dependências de desenvolvimento"
	@echo "  make install-all   - Instala todas as dependências (web + dev)"
	@echo "  make test          - Executa os testes"
	@echo "  make lint          - Verifica código com ruff"
	@echo "  make format        - Formata código com black"
	@echo "  make type-check    - Verifica tipos com mypy"
	@echo "  make clean         - Remove arquivos temporários"
	@echo "  make build         - Cria distribuição do pacote"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-all:
	pip install -e ".[all]"

test:
	pytest

test-cov:
	pytest --cov --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/

lint-fix:
	ruff check --fix src/ tests/

format:
	black src/ tests/

format-check:
	black --check src/ tests/

type-check:
	mypy src/pdf_form_filler

check-all: format-check lint type-check test

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

upload-test:
	python -m twine upload --repository testpypi dist/*

upload:
	python -m twine upload dist/*
