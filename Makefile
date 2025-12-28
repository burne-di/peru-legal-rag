.PHONY: install dev test lint format clean docker-build docker-up docker-down ingest query help

# Variables
PYTHON := python
PIP := pip
DOCKER_COMPOSE := docker compose

# Colores
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
NC := \033[0m

help: ## Muestra esta ayuda
	@echo "$(BLUE)RAG Estado Peru - Comandos disponibles:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

# ============================================
# Desarrollo local
# ============================================

install: ## Instala dependencias
	$(PIP) install -e .

dev: ## Instala dependencias de desarrollo
	$(PIP) install -e ".[dev]"

test: ## Ejecuta tests
	pytest tests/ -v

lint: ## Ejecuta linter (ruff)
	ruff check packages/ services/ scripts/

format: ## Formatea código
	ruff format packages/ services/ scripts/

clean: ## Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache htmlcov .coverage

# ============================================
# RAG Pipeline
# ============================================

ingest: ## Ingesta documentos de data/raw
	$(PYTHON) scripts/ingest.py --directory ./data/raw

ingest-clear: ## Limpia vector store e ingesta
	$(PYTHON) scripts/ingest.py --directory ./data/raw --clear

query: ## Modo interactivo de consultas
	$(PYTHON) scripts/query.py --interactive

test-pipeline: ## Prueba el pipeline completo
	$(PYTHON) scripts/test_pipeline.py

# ============================================
# API
# ============================================

run-api: ## Inicia API en modo desarrollo
	uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000

# ============================================
# Docker
# ============================================

docker-build: ## Construye imagen Docker
	$(DOCKER_COMPOSE) build

docker-up: ## Inicia servicios con Docker
	$(DOCKER_COMPOSE) up -d

docker-down: ## Detiene servicios Docker
	$(DOCKER_COMPOSE) down

docker-logs: ## Muestra logs de Docker
	$(DOCKER_COMPOSE) logs -f

docker-ingest: ## Ejecuta ingesta en Docker
	$(DOCKER_COMPOSE) --profile ingest up ingest

# ============================================
# Evaluación
# ============================================

eval: ## Ejecuta evaluación offline
	$(PYTHON) scripts/eval_run.py

eval-report: ## Genera reporte de evaluación
	$(PYTHON) scripts/eval_run.py --report
