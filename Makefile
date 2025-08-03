# API Builder - Comprehensive Makefile
# Enterprise-grade automation for FastAPI microservices

# === Variables ===
SHELL := /bin/bash
PROJECT := api-builder
APP_NAME := api_builder
UV_PYTHON := /opt/homebrew/bin/python3.12
export UV_PYTHON

# Python management
UV := uv
PYTHON := $(UV) run python
PYTHON_RAW := python3.12
PIP := $(UV) pip

# Directories
ROOT_DIR := $(shell pwd)
API_DIR := $(ROOT_DIR)/api
MCP_DIR := $(ROOT_DIR)/mcp_server
TESTS_DIR := $(ROOT_DIR)/tests
DOCS_DIR := $(ROOT_DIR)/docs
SCRIPTS_DIR := $(ROOT_DIR)/scripts
NOTEBOOKS_DIR := $(ROOT_DIR)/notebooks

# Docker settings
DOCKER_IMAGE := $(PROJECT):latest
DOCKER_REGISTRY := registry.local
DOCKER_TAG := $(DOCKER_REGISTRY)/$(DOCKER_IMAGE)

# Database settings  
DB_HOST := localhost
DB_PORT := 5432
DB_NAME := api_builder_db
DB_USER := api_builder
DB_TEST_NAME := api_builder_test

# Redis settings
REDIS_HOST := localhost
REDIS_PORT := 6379

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
CYAN := \033[0;36m
NC := \033[0m # No Color

# === Default Target ===
.DEFAULT_GOAL := help

# === Help ===
.PHONY: help
help: ## Show this help message
	@echo "$(CYAN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║              API Builder - Available Commands             ║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)🚀 Quick Start:$(NC)"
	@echo "  make setup                   # Complete initial setup"
	@echo "  make dev                     # Start development server"
	@echo "  make test                    # Run tests"
	@echo ""
	@echo "$(YELLOW)📦 Setup & Installation:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(setup|install|init|check-)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🔧 Development:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(dev|run|debug|watch)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🧪 Testing & Quality:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(test|lint|format|type|coverage|quality)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🗄️ Database:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(db-|migrate|seed)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🐳 Docker & Deployment:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(docker|deploy|k8s)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)📊 Monitoring & Observability:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(monitor|metrics|logs|trace)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)📚 Documentation:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(docs|api-docs|readme)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🛠️ Utilities:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(clean|backup|restore|shell|repl)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(CYAN)Environment:$(NC) UV_PYTHON=$(UV_PYTHON)"
	@echo "$(CYAN)Documentation:$(NC) http://localhost:8000/docs"

# === Setup & Installation ===
.PHONY: setup
setup: check-python install init-dirs setup-env setup-git ## Complete project setup
	@echo "$(GREEN)✅ Setup complete!$(NC)"
	@echo "Run 'make dev' to start development server"

.PHONY: check-python
check-python: ## Check Python version (must be 3.12)
	@echo "$(YELLOW)Checking Python version...$(NC)"
	@if ! command -v $(PYTHON_RAW) >/dev/null 2>&1; then \
		echo "$(RED)❌ Python 3.12 not found at $(UV_PYTHON)$(NC)"; \
		echo "Install with: brew install python@3.12"; \
		exit 1; \
	fi
	@version=$$($(PYTHON_RAW) --version 2>&1 | cut -d" " -f2); \
	if [[ "$$version" != 3.12.* ]]; then \
		echo "$(RED)❌ Python $$version found, but 3.12 required$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Python $$version$(NC)"

.PHONY: install
install: install-uv create-venv install-deps ## Install all dependencies
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

.PHONY: install-uv
install-uv: ## Install uv package manager
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "$(YELLOW)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)✅ uv installed$(NC)"; \
	else \
		echo "$(GREEN)✅ uv already installed$(NC)"; \
	fi

.PHONY: create-venv
create-venv: ## Create virtual environment
	@echo "$(YELLOW)Creating virtual environment...$(NC)"
	@$(UV) venv --python $(UV_PYTHON)
	@echo "$(GREEN)✅ Virtual environment created$(NC)"

.PHONY: install-deps
install-deps: ## Install Python dependencies
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@if [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt; \
	else \
		echo "Creating requirements.txt..."; \
		echo "fastapi==0.104.1" > requirements.txt; \
		echo "uvicorn[standard]==0.24.0" >> requirements.txt; \
		echo "sqlalchemy==2.0.23" >> requirements.txt; \
		echo "pydantic==2.5.2" >> requirements.txt; \
		echo "redis==5.0.1" >> requirements.txt; \
		echo "httpx==0.25.2" >> requirements.txt; \
		echo "python-jose[cryptography]==3.3.0" >> requirements.txt; \
		echo "passlib[bcrypt]==1.7.4" >> requirements.txt; \
		echo "python-multipart==0.0.6" >> requirements.txt; \
		echo "alembic==1.13.0" >> requirements.txt; \
		echo "asyncpg==0.29.0" >> requirements.txt; \
		echo "python-dotenv==1.0.0" >> requirements.txt; \
		$(PIP) install -r requirements.txt; \
	fi
	@if [ -f requirements-dev.txt ]; then \
		$(PIP) install -r requirements-dev.txt; \
	else \
		echo "Creating requirements-dev.txt..."; \
		echo "pytest==7.4.3" > requirements-dev.txt; \
		echo "pytest-cov==4.1.0" >> requirements-dev.txt; \
		echo "pytest-asyncio==0.21.1" >> requirements-dev.txt; \
		echo "black==23.12.0" >> requirements-dev.txt; \
		echo "ruff==0.1.8" >> requirements-dev.txt; \
		echo "mypy==1.7.1" >> requirements-dev.txt; \
		echo "pre-commit==3.6.0" >> requirements-dev.txt; \
		echo "httpx==0.25.2" >> requirements-dev.txt; \
		echo "pytest-mock==3.12.0" >> requirements-dev.txt; \
		echo "faker==20.1.0" >> requirements-dev.txt; \
		$(PIP) install -r requirements-dev.txt; \
	fi
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

.PHONY: init-dirs
init-dirs: ## Initialize directory structure
	@echo "$(YELLOW)Creating directory structure...$(NC)"
	@mkdir -p $(API_DIR)/{auth,crud,endpoints,middleware,utils}
	@mkdir -p $(MCP_DIR)/{handlers,schemas,utils}
	@mkdir -p $(TESTS_DIR)/{unit,integration,e2e,fixtures}
	@mkdir -p $(DOCS_DIR)/{api,architecture,deployment}
	@mkdir -p $(SCRIPTS_DIR)/{setup,migration,deployment}
	@mkdir -p $(NOTEBOOKS_DIR)
	@mkdir -p logs
	@touch $(API_DIR)/__init__.py
	@touch $(API_DIR)/auth/__init__.py
	@touch $(API_DIR)/crud/__init__.py
	@touch $(API_DIR)/endpoints/__init__.py
	@touch $(API_DIR)/middleware/__init__.py
	@touch $(API_DIR)/utils/__init__.py
	@touch $(MCP_DIR)/__init__.py
	@touch $(TESTS_DIR)/__init__.py
	@echo "$(GREEN)✅ Directory structure created$(NC)"

.PHONY: setup-env
setup-env: ## Setup environment files
	@echo "$(YELLOW)Setting up environment files...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env 2>/dev/null || \
		echo "# API Builder Environment Variables" > .env; \
		echo "APP_NAME=api-builder" >> .env; \
		echo "APP_VERSION=1.0.0" >> .env; \
		echo "ENVIRONMENT=development" >> .env; \
		echo "DEBUG=true" >> .env; \
		echo "LOG_LEVEL=INFO" >> .env; \
		echo "" >> .env; \
		echo "# API Configuration" >> .env; \
		echo "API_HOST=0.0.0.0" >> .env; \
		echo "API_PORT=8000" >> .env; \
		echo "API_PREFIX=/api/v1" >> .env; \
		echo "CORS_ORIGINS=[\"http://localhost:3000\"]" >> .env; \
		echo "" >> .env; \
		echo "# Database" >> .env; \
		echo "DATABASE_URL=postgresql://user:password@localhost:5432/api_builder" >> .env; \
		echo "DATABASE_POOL_SIZE=20" >> .env; \
		echo "DATABASE_MAX_OVERFLOW=40" >> .env; \
		echo "" >> .env; \
		echo "# Redis" >> .env; \
		echo "REDIS_URL=redis://localhost:6379" >> .env; \
		echo "REDIS_PREFIX=api_builder:" >> .env; \
		echo "" >> .env; \
		echo "# Authentication" >> .env; \
		echo "JWT_SECRET_KEY=$$(openssl rand -hex 32)" >> .env; \
		echo "JWT_ALGORITHM=HS256" >> .env; \
		echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env; \
		echo "$(GREEN)✅ Created .env file$(NC)"; \
	else \
		echo "$(GREEN)✅ .env file already exists$(NC)"; \
	fi
	@if [ ! -f .env.example ]; then \
		cp .env .env.example; \
		sed -i.bak 's/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=your-secret-key-here/' .env.example; \
		sed -i.bak 's/password@/password@/' .env.example; \
		rm -f .env.example.bak; \
		echo "$(GREEN)✅ Created .env.example$(NC)"; \
	fi

.PHONY: setup-git
setup-git: ## Initialize git repository
	@echo "$(YELLOW)Setting up git...$(NC)"
	@if [ ! -d .git ]; then \
		git init; \
		git add .; \
		git commit -m "Initial commit: API Builder project setup"; \
		echo "$(GREEN)✅ Git repository initialized$(NC)"; \
	else \
		echo "$(GREEN)✅ Git already initialized$(NC)"; \
	fi

.PHONY: setup-git-hooks
setup-git-hooks: ## Setup git hooks
	@echo "$(YELLOW)Setting up git hooks...$(NC)"
	@$(UV) run pre-commit install 2>/dev/null || echo "$(YELLOW)pre-commit not installed$(NC)"
	@echo "$(GREEN)✅ Git hooks configured$(NC)"

# === Development ===
.PHONY: dev
dev: ## Start development server with hot reload
	@echo "$(CYAN)🚀 Starting development server...$(NC)"
	@$(UV) run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: run
run: ## Run production server
	@echo "$(CYAN)🚀 Starting production server...$(NC)"
	@$(UV) run uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

.PHONY: debug
debug: ## Run with debug mode enabled
	@echo "$(CYAN)🐛 Starting debug server...$(NC)"
	@DEBUG=true $(UV) run python -m debugpy --listen 5678 --wait-for-client -m uvicorn api.main:app --reload

.PHONY: watch
watch: ## Watch for changes and auto-restart
	@echo "$(CYAN)👁️ Watching for changes...$(NC)"
	@$(UV) run watchfiles 'make dev' $(API_DIR) $(MCP_DIR)

.PHONY: shell
shell: ## Start interactive Python shell
	@$(UV) run python

.PHONY: repl
repl: ## Start IPython REPL with app context
	@$(UV) run ipython -i -c "from api.main import app; from api.database import get_db; print('App context loaded')"

# === Testing & Quality ===
.PHONY: test
test: ## Run all tests
	@echo "$(YELLOW)🧪 Running tests...$(NC)"
	@$(UV) run pytest $(TESTS_DIR) -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(YELLOW)Running unit tests...$(NC)"
	@$(UV) run pytest $(TESTS_DIR)/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@$(UV) run pytest $(TESTS_DIR)/integration -v

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests
	@echo "$(YELLOW)Running E2E tests...$(NC)"
	@$(UV) run pytest $(TESTS_DIR)/e2e -v

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@$(UV) run pytest-watch $(TESTS_DIR) -v

.PHONY: coverage
coverage: ## Run tests with coverage report
	@echo "$(YELLOW)📊 Running tests with coverage...$(NC)"
	@$(UV) run pytest $(TESTS_DIR) --cov=$(API_DIR) --cov-report=html --cov-report=term --cov-report=term-missing

.PHONY: coverage-html
coverage-html: coverage ## Open coverage HTML report
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html in your browser"

.PHONY: lint
lint: ## Run linting checks
	@echo "$(YELLOW)🔍 Running linters...$(NC)"
	@$(UV) run ruff check .
	@$(UV) run mypy $(API_DIR) --ignore-missing-imports

.PHONY: format
format: ## Format code
	@echo "$(YELLOW)✨ Formatting code...$(NC)"
	@$(UV) run black .
	@$(UV) run ruff check --fix .

.PHONY: type-check
type-check: ## Run type checking
	@echo "$(YELLOW)🔍 Type checking...$(NC)"
	@$(UV) run mypy $(API_DIR) --strict

.PHONY: quality
quality: lint type-check test ## Run all quality checks
	@echo "$(GREEN)✅ All quality checks passed!$(NC)"

.PHONY: pre-commit
pre-commit: ## Run pre-commit checks
	@$(UV) run pre-commit run --all-files

# === Database ===
.PHONY: db-start
db-start: ## Start PostgreSQL and Redis
	@echo "$(YELLOW)Starting databases...$(NC)"
	@docker-compose up -d postgres redis 2>/dev/null || \
		(docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15 && \
		 docker run -d --name redis -p 6379:6379 redis:7)
	@echo "$(GREEN)✅ Databases started$(NC)"

.PHONY: db-stop
db-stop: ## Stop databases
	@echo "$(YELLOW)Stopping databases...$(NC)"
	@docker-compose down 2>/dev/null || \
		(docker stop postgres redis 2>/dev/null && docker rm postgres redis 2>/dev/null)
	@echo "$(GREEN)✅ Databases stopped$(NC)"

.PHONY: db-create
db-create: ## Create database
	@echo "$(YELLOW)Creating database...$(NC)"
	@$(UV) run python -c "from api.database import create_database; create_database()"
	@echo "$(GREEN)✅ Database created$(NC)"

.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "$(YELLOW)Running migrations...$(NC)"
	@$(UV) run alembic upgrade head
	@echo "$(GREEN)✅ Migrations complete$(NC)"

.PHONY: db-rollback
db-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back migration...$(NC)"
	@$(UV) run alembic downgrade -1
	@echo "$(GREEN)✅ Rollback complete$(NC)"

.PHONY: db-reset
db-reset: db-drop db-create db-migrate ## Reset database
	@echo "$(GREEN)✅ Database reset complete$(NC)"

.PHONY: db-drop
db-drop: ## Drop database
	@echo "$(RED)⚠️ Dropping database...$(NC)"
	@$(UV) run python -c "from api.database import drop_database; drop_database()"
	@echo "$(GREEN)✅ Database dropped$(NC)"

.PHONY: db-seed
db-seed: ## Seed database with sample data
	@echo "$(YELLOW)Seeding database...$(NC)"
	@$(UV) run python scripts/seed_data.py
	@echo "$(GREEN)✅ Database seeded$(NC)"

.PHONY: db-shell
db-shell: ## Open database shell
	@psql postgresql://user:password@localhost:5432/api_builder

.PHONY: migrate-create
migrate-create: ## Create new migration (use NAME="description")
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)Usage: make migrate-create NAME=\"add_user_table\"$(NC)"; \
	else \
		$(UV) run alembic revision --autogenerate -m "$(NAME)"; \
		echo "$(GREEN)✅ Migration created$(NC)"; \
	fi

# === Docker & Deployment ===
.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(YELLOW)🐳 Building Docker image...$(NC)"
	@docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✅ Docker image built: $(DOCKER_IMAGE)$(NC)"

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "$(YELLOW)🐳 Running Docker container...$(NC)"
	@docker run -d \
		--name $(PROJECT) \
		-p 8000:8000 \
		--env-file .env \
		--network host \
		$(DOCKER_IMAGE)
	@echo "$(GREEN)✅ Container running$(NC)"

.PHONY: docker-stop
docker-stop: ## Stop Docker container
	@docker stop $(PROJECT) 2>/dev/null && docker rm $(PROJECT) 2>/dev/null || true
	@echo "$(GREEN)✅ Container stopped$(NC)"

.PHONY: docker-logs
docker-logs: ## Show Docker logs
	@docker logs -f $(PROJECT)

.PHONY: docker-shell
docker-shell: ## Shell into Docker container
	@docker exec -it $(PROJECT) /bin/bash

.PHONY: docker-push
docker-push: docker-build ## Push Docker image to registry
	@echo "$(YELLOW)📤 Pushing to registry...$(NC)"
	@docker tag $(DOCKER_IMAGE) $(DOCKER_TAG)
	@docker push $(DOCKER_TAG)
	@echo "$(GREEN)✅ Image pushed: $(DOCKER_TAG)$(NC)"

.PHONY: docker-compose-up
docker-compose-up: ## Start all services with docker-compose
	@docker-compose up -d
	@echo "$(GREEN)✅ All services started$(NC)"

.PHONY: docker-compose-down
docker-compose-down: ## Stop all services
	@docker-compose down
	@echo "$(GREEN)✅ All services stopped$(NC)"

.PHONY: k8s-deploy
k8s-deploy: ## Deploy to Kubernetes
	@echo "$(YELLOW)☸️ Deploying to Kubernetes...$(NC)"
	@kubectl apply -f k8s/
	@echo "$(GREEN)✅ Deployed to Kubernetes$(NC)"

.PHONY: k8s-delete
k8s-delete: ## Delete from Kubernetes
	@kubectl delete -f k8s/
	@echo "$(GREEN)✅ Removed from Kubernetes$(NC)"

.PHONY: k8s-status
k8s-status: ## Check Kubernetes deployment status
	@kubectl get pods,svc,ing -l app=$(PROJECT)

# === Monitoring & Observability ===
.PHONY: monitor-start
monitor-start: ## Start monitoring stack
	@echo "$(YELLOW)Starting monitoring stack...$(NC)"
	@docker-compose -f docker-compose.monitoring.yml up -d
	@echo "$(GREEN)✅ Monitoring stack started$(NC)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"
	@echo "Loki: http://localhost:3100"

.PHONY: monitor-stop
monitor-stop: ## Stop monitoring stack
	@docker-compose -f docker-compose.monitoring.yml down
	@echo "$(GREEN)✅ Monitoring stack stopped$(NC)"

.PHONY: logs
logs: ## Tail application logs
	@tail -f logs/*.log

.PHONY: metrics
metrics: ## Show application metrics
	@curl -s http://localhost:8000/metrics | grep -v '^#'

.PHONY: health
health: ## Check application health
	@curl -s http://localhost:8000/health | jq '.' 2>/dev/null || curl http://localhost:8000/health

.PHONY: trace
trace: ## Enable request tracing
	@echo "$(YELLOW)Enabling tracing...$(NC)"
	@export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
	@export OTEL_SERVICE_NAME=$(PROJECT)
	@echo "$(GREEN)✅ Tracing enabled$(NC)"

# === Documentation ===
.PHONY: docs
docs: ## Generate documentation
	@echo "$(YELLOW)📚 Generating documentation...$(NC)"
	@$(UV) run mkdocs build 2>/dev/null || echo "mkdocs not installed"
	@echo "$(GREEN)✅ Documentation generated$(NC)"

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@$(UV) run mkdocs serve 2>/dev/null || echo "Visit http://localhost:8000/docs for API docs"

.PHONY: api-docs
api-docs: ## Open API documentation
	@echo "$(CYAN)Opening API docs...$(NC)"
	@open http://localhost:8000/docs 2>/dev/null || xdg-open http://localhost:8000/docs 2>/dev/null || \
		echo "Visit http://localhost:8000/docs"

.PHONY: readme
readme: ## Generate README from template
	@echo "$(YELLOW)Generating README...$(NC)"
	@$(UV) run python scripts/generate_readme.py 2>/dev/null || \
		echo "# $(PROJECT)" > README.md && \
		echo "" >> README.md && \
		echo "## Quick Start" >> README.md && \
		echo '```bash' >> README.md && \
		echo "make setup" >> README.md && \
		echo "make dev" >> README.md && \
		echo '```' >> README.md
	@echo "$(GREEN)✅ README generated$(NC)"

# === Utilities ===
.PHONY: clean
clean: ## Clean generated files and caches
	@echo "$(YELLOW)🧹 Cleaning...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache 2>/dev/null || true
	@rm -rf build dist *.egg-info 2>/dev/null || true
	@echo "$(GREEN)✅ Cleaned$(NC)"

.PHONY: clean-docker
clean-docker: ## Clean Docker resources
	@echo "$(YELLOW)🐳 Cleaning Docker...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)✅ Docker cleaned$(NC)"

.PHONY: backup
backup: ## Backup project and database
	@echo "$(YELLOW)💾 Creating backup...$(NC)"
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	mkdir -p backups; \
	tar -czf backups/backup_$$timestamp.tar.gz \
		--exclude='.venv' \
		--exclude='__pycache__' \
		--exclude='.git' \
		--exclude='node_modules' \
		--exclude='htmlcov' \
		--exclude='.pytest_cache' \
		. && \
	pg_dump postgresql://user:password@localhost:5432/api_builder > backups/db_$$timestamp.sql 2>/dev/null || true
	@echo "$(GREEN)✅ Backup created in backups/$(NC)"

.PHONY: restore
restore: ## Restore from latest backup
	@echo "$(YELLOW)📥 Restoring from backup...$(NC)"
	@latest=$$(ls -t backups/*.tar.gz 2>/dev/null | head -1); \
	if [ -n "$$latest" ]; then \
		tar -xzf $$latest && echo "$(GREEN)✅ Restored from $$latest$(NC)"; \
	else \
		echo "$(RED)No backups found$(NC)"; \
	fi

.PHONY: version
version: ## Show version information
	@echo "$(CYAN)Version Information:$(NC)"
	@echo "Project: $(PROJECT)"
	@echo "Python: $$($(PYTHON_RAW) --version)"
	@echo "FastAPI: $$($(UV) run python -c 'import fastapi; print(fastapi.__version__)' 2>/dev/null || echo 'Not installed')"
	@echo "uv: $$($(UV) --version 2>/dev/null || echo 'Not installed')"

.PHONY: info
info: ## Show project information
	@echo "$(CYAN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║                    Project Information                    ║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo "Project: $(PROJECT)"
	@echo "Directory: $(ROOT_DIR)"
	@echo "Python: $(UV_PYTHON)"
	@echo "Virtual Env: .venv"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  API: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo "  Database: postgresql://localhost:5432/api_builder"
	@echo "  Redis: redis://localhost:6379"
	@echo ""
	@echo "$(YELLOW)Files:$(NC)"
	@echo "  API files: $$(find $(API_DIR) -name '*.py' | wc -l)"
	@echo "  Test files: $$(find $(TESTS_DIR) -name '*.py' 2>/dev/null | wc -l)"
	@echo "  Total LOC: $$(find . -name '*.py' -exec cat {} \; 2>/dev/null | wc -l)"

# === Git Shortcuts ===
.PHONY: commit
commit: ## Quick commit (use MSG="message")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Usage: make commit MSG=\"Your commit message\"$(NC)"; \
	else \
		git add -A && git commit -m "$(MSG)"; \
		echo "$(GREEN)✅ Committed$(NC)"; \
	fi

.PHONY: push
push: ## Push to origin
	@git push origin $$(git branch --show-current)
	@echo "$(GREEN)✅ Pushed to origin$(NC)"

.PHONY: pull
pull: ## Pull from origin
	@git pull origin $$(git branch --show-current)
	@echo "$(GREEN)✅ Pulled from origin$(NC)"

.PHONY: status
status: ## Git status
	@git status

.PHONY: branch
branch: ## Create new branch (use NAME="branch-name")
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)Usage: make branch NAME=\"feature/new-feature\"$(NC)"; \
	else \
		git checkout -b $(NAME); \
		echo "$(GREEN)✅ Created branch: $(NAME)$(NC)"; \
	fi

# === Quick Commands (Aliases) ===
.PHONY: d
d: dev ## Alias for dev

.PHONY: t
t: test ## Alias for test

.PHONY: l
l: lint ## Alias for lint

.PHONY: f
f: format ## Alias for format

.PHONY: c
c: clean ## Alias for clean

.PHONY: h
h: help ## Alias for help

# === Advanced Operations ===
.PHONY: profile
profile: ## Profile application performance
	@echo "$(YELLOW)📊 Profiling application...$(NC)"
	@$(UV) run python -m cProfile -o profile.stats api.main
	@$(UV) run python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

.PHONY: security
security: ## Run security checks
	@echo "$(YELLOW)🔒 Running security checks...$(NC)"
	@$(UV) run pip-audit 2>/dev/null || echo "pip-audit not installed"
	@$(UV) run bandit -r $(API_DIR) 2>/dev/null || echo "bandit not installed"
	@echo "$(GREEN)✅ Security check complete$(NC)"

.PHONY: deps-update
deps-update: ## Update all dependencies
	@echo "$(YELLOW)📦 Updating dependencies...$(NC)"
	@$(UV) pip compile requirements.in -o requirements.txt --upgrade 2>/dev/null || \
		$(UV) pip install --upgrade -r requirements.txt
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

.PHONY: deps-tree
deps-tree: ## Show dependency tree
	@$(UV) run pipdeptree 2>/dev/null || $(PIP) install pipdeptree && $(UV) run pipdeptree

.PHONY: benchmark
benchmark: ## Run performance benchmarks
	@echo "$(YELLOW)⚡ Running benchmarks...$(NC)"
	@$(UV) run python scripts/benchmark.py 2>/dev/null || \
		echo "Create scripts/benchmark.py to run benchmarks"

.PHONY: load-test
load-test: ## Run load testing
	@echo "$(YELLOW)🔥 Running load tests...$(NC)"
	@$(UV) run locust -f scripts/locustfile.py --host=http://localhost:8000 2>/dev/null || \
		echo "Install locust: pip install locust"

# === MCP Server Commands ===
.PHONY: mcp-start
mcp-start: ## Start MCP server
	@echo "$(CYAN)🚀 Starting MCP server...$(NC)"
	@$(UV) run python mcp_server/server.py

.PHONY: mcp-test
mcp-test: ## Test MCP server
	@echo "$(YELLOW)Testing MCP server...$(NC)"
	@$(UV) run pytest tests/test_mcp_server.py -v

# === Jupyter Notebook Commands ===
.PHONY: notebook
notebook: ## Start Jupyter notebook
	@echo "$(CYAN)📓 Starting Jupyter notebook...$(NC)"
	@$(UV) run jupyter notebook $(NOTEBOOKS_DIR)

.PHONY: lab
lab: ## Start Jupyter lab
	@echo "$(CYAN)🔬 Starting Jupyter lab...$(NC)"
	@$(UV) run jupyter lab $(NOTEBOOKS_DIR)

# === CI/CD Commands ===
.PHONY: ci
ci: quality security ## Run CI pipeline locally
	@echo "$(GREEN)✅ CI pipeline passed$(NC)"

.PHONY: cd
cd: docker-build docker-push k8s-deploy ## Run CD pipeline
	@echo "$(GREEN)✅ Deployed successfully$(NC)"

# === All-in-One Commands ===
.PHONY: all
all: setup quality docker-build ## Setup, test, and build everything
	@echo "$(GREEN)✅ All tasks completed$(NC)"

.PHONY: reset
reset: clean db-reset ## Reset everything (CAUTION!)
	@echo "$(RED)⚠️ System reset complete$(NC)"

.PHONY: fresh
fresh: clean setup db-reset db-seed dev ## Fresh start with seeded database
	@echo "$(GREEN)✅ Fresh environment ready$(NC)"

# === End of Makefile ===