# === Variables ===
UV_PYTHON := /opt/homebrew/bin/python3.12
export UV_PYTHON
UV := uv
PYTHON := $(UV) run python
PROJECT := hr-resume-search-mcp

# === Colors ===
RESET := \033[0m
BOLD := \033[1m
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
CYAN := \033[36m

# === Help ===
.PHONY: help
help: ## Show this help message
	@echo "$(BOLD)$(PROJECT) - Available commands:$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)Quick Start:$(RESET)"
	@echo "  1. make setup        # Complete project setup"
	@echo "  2. make dev          # Run in development mode"
	@echo "  3. make test         # Run all tests"

# === Setup ===
.PHONY: setup
setup: ## Complete project setup
	@echo "$(BOLD)Setting up $(PROJECT)...$(RESET)"
	$(MAKE) check-python
	$(MAKE) install
	$(MAKE) setup-db
	$(MAKE) setup-git-hooks
	@echo "$(GREEN)✓ Setup complete!$(RESET)"

.PHONY: check-python
check-python: ## Check Python version
	@echo "Checking Python version..."
	@if ! command -v $(UV_PYTHON) &> /dev/null; then \
		echo "$(RED)Error: Python 3.12 not found at $(UV_PYTHON)$(RESET)"; \
		echo "Please install Python 3.12 and try again"; \
		exit 1; \
	fi
	@$(UV_PYTHON) --version | grep -q "3.12" || (echo "$(RED)Error: Python 3.12 required$(RESET)" && exit 1)
	@echo "$(GREEN)✓ Python 3.12 found$(RESET)"

.PHONY: install
install: ## Install dependencies
	@echo "Installing dependencies..."
	$(UV) venv --python $(UV_PYTHON)
	$(UV) pip install -r requirements.txt
	$(UV) pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencies installed$(RESET)"

.PHONY: setup-db
setup-db: ## Setup database
	@echo "Setting up database..."
	# TODO: Add database setup commands
	@echo "$(YELLOW)⚠ Database setup pending implementation$(RESET)"

.PHONY: setup-git-hooks
setup-git-hooks: ## Setup git hooks
	@echo "Setting up git hooks..."
	# TODO: Add pre-commit hooks
	@echo "$(YELLOW)⚠ Git hooks pending implementation$(RESET)"

# === Development ===
.PHONY: run
run: ## Run the application
	$(PYTHON) -m api.main

.PHONY: dev
dev: ## Run in development mode with auto-reload
	$(UV) run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: shell
shell: ## Start interactive Python shell
	$(PYTHON)

# === Testing ===
.PHONY: test
test: ## Run all tests
	@echo "$(BOLD)Running tests...$(RESET)"
	$(PYTHON) -m pytest tests/ -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BOLD)Running tests with coverage...$(RESET)"
	$(PYTHON) -m pytest tests/ --cov=api --cov-report=html --cov-report=term --cov-fail-under=80

.PHONY: test-e2e
test-e2e: ## Run E2E tests only
	@echo "$(BOLD)Running E2E tests...$(RESET)"
	$(PYTHON) -m pytest tests/e2e/ -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BOLD)Running unit tests...$(RESET)"
	$(PYTHON) -m pytest tests/unit/ -v

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(BOLD)Running integration tests...$(RESET)"
	$(PYTHON) -m pytest tests/integration/ -v

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	$(PYTHON) -m pytest tests/ -v --watch

.PHONY: test-parallel
test-parallel: ## Run tests in parallel
	$(PYTHON) -m pytest tests/ -n auto -v

.PHONY: test-failed
test-failed: ## Re-run failed tests
	$(PYTHON) -m pytest tests/ --lf -v

.PHONY: test-debug
test-debug: ## Run tests with debugger on failure
	$(PYTHON) -m pytest tests/ --pdb -v

.PHONY: coverage-html
coverage-html: ## Open HTML coverage report
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html in your browser"

# === MCP Server Testing ===
.PHONY: mcp-test-comprehensive
mcp-test-comprehensive: ## Run comprehensive MCP tests (23 automated tests)
	@echo "$(BOLD)Running comprehensive MCP tests...$(RESET)"
	# TODO: Implement MCP test suite
	@echo "$(YELLOW)⚠ MCP tests pending implementation$(RESET)"

.PHONY: mcp-test-interactive
mcp-test-interactive: ## Run interactive MCP tests
	@echo "$(BOLD)Running interactive MCP tests...$(RESET)"
	# TODO: Implement interactive MCP tests
	@echo "$(YELLOW)⚠ MCP interactive tests pending implementation$(RESET)"

.PHONY: mcp-test-concurrent
mcp-test-concurrent: ## Run concurrent MCP stress tests
	@echo "$(BOLD)Running concurrent MCP tests...$(RESET)"
	# TODO: Implement concurrent MCP tests
	@echo "$(YELLOW)⚠ MCP concurrent tests pending implementation$(RESET)"

.PHONY: mcp-test-report
mcp-test-report: ## Generate MCP test report
	@echo "$(BOLD)Generating MCP test report...$(RESET)"
	# TODO: Implement MCP test reporting
	@echo "$(YELLOW)⚠ MCP test report pending implementation$(RESET)"

# === Quality ===
.PHONY: lint
lint: ## Run linting
	@echo "$(BOLD)Running linters...$(RESET)"
	$(UV) run ruff check .
	$(UV) run mypy api/

.PHONY: format
format: ## Format code
	@echo "$(BOLD)Formatting code...$(RESET)"
	$(UV) run black .
	$(UV) run ruff check --fix .
	$(UV) run isort .

.PHONY: security
security: ## Run security checks
	@echo "$(BOLD)Running security checks...$(RESET)"
	$(UV) run bandit -r api/
	$(UV) run safety check

.PHONY: type-check
type-check: ## Run type checking
	@echo "$(BOLD)Running type checks...$(RESET)"
	$(UV) run mypy api/ --strict

# === Database ===
.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "$(BOLD)Running migrations...$(RESET)"
	# TODO: Add alembic migrations
	@echo "$(YELLOW)⚠ Migrations pending implementation$(RESET)"

.PHONY: db-rollback
db-rollback: ## Rollback database migration
	@echo "$(BOLD)Rolling back migration...$(RESET)"
	# TODO: Add rollback command
	@echo "$(YELLOW)⚠ Rollback pending implementation$(RESET)"

.PHONY: db-seed
db-seed: ## Seed database with test data
	@echo "$(BOLD)Seeding database...$(RESET)"
	# TODO: Add seed script
	@echo "$(YELLOW)⚠ Database seeding pending implementation$(RESET)"

# === Docker ===
.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BOLD)Building Docker image...$(RESET)"
	docker build -t $(PROJECT):latest .

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "$(BOLD)Running Docker container...$(RESET)"
	docker run -p 8000:8000 --env-file .env $(PROJECT):latest

.PHONY: docker-compose-up
docker-compose-up: ## Start services with docker-compose
	docker-compose up -d

.PHONY: docker-compose-down
docker-compose-down: ## Stop services with docker-compose
	docker-compose down

.PHONY: docker-compose-logs
docker-compose-logs: ## Show docker-compose logs
	docker-compose logs -f

# === Deployment ===
.PHONY: deploy
deploy: ## Deploy to Kubernetes
	@echo "$(BOLD)Deploying to Kubernetes...$(RESET)"
	kubectl apply -f k8s/

.PHONY: deploy-rollback
deploy-rollback: ## Rollback Kubernetes deployment
	@echo "$(BOLD)Rolling back deployment...$(RESET)"
	kubectl rollout undo deployment/$(PROJECT)

# === Documentation ===
.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "$(BOLD)Serving documentation...$(RESET)"
	$(UV) run mkdocs serve

.PHONY: docs-build
docs-build: ## Build documentation
	@echo "$(BOLD)Building documentation...$(RESET)"
	$(UV) run mkdocs build

# === Utilities ===
.PHONY: clean
clean: ## Clean up generated files
	@echo "$(BOLD)Cleaning up...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf build/ dist/ *.egg-info/
	@echo "$(GREEN)✓ Cleanup complete$(RESET)"

.PHONY: logs
logs: ## Show application logs
	tail -f logs/*.log 2>/dev/null || echo "No logs found"

.PHONY: env-check
env-check: ## Check environment variables
	@echo "$(BOLD)Environment Configuration:$(RESET)"
	@echo "Python: $(UV_PYTHON)"
	@echo "Project: $(PROJECT)"
	@test -f .env && echo "$(GREEN)✓ .env file exists$(RESET)" || echo "$(RED)✗ .env file missing$(RESET)"
	@test -f .env.example && echo "$(GREEN)✓ .env.example file exists$(RESET)" || echo "$(YELLOW)⚠ .env.example file missing$(RESET)"

.PHONY: requirements-update
requirements-update: ## Update requirements files
	@echo "$(BOLD)Updating requirements...$(RESET)"
	$(UV) pip freeze > requirements.txt
	@echo "$(GREEN)✓ Requirements updated$(RESET)"

.PHONY: git-status
git-status: ## Show git status
	@git status

.PHONY: git-commit
git-commit: ## Commit with conventional commit message
	@echo "$(BOLD)Creating commit...$(RESET)"
	@git add -A
	@echo "Enter commit type (feat/fix/docs/test/chore):"
	@read TYPE && echo "Enter commit message:" && read MSG && git commit -m "$$TYPE: $$MSG"

# === Monitoring ===
.PHONY: metrics
metrics: ## Show application metrics
	@echo "$(BOLD)Application Metrics:$(RESET)"
	@curl -s http://localhost:8000/metrics 2>/dev/null || echo "Metrics endpoint not available"

.PHONY: health
health: ## Check application health
	@echo "$(BOLD)Health Check:$(RESET)"
	@curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || echo "Health endpoint not available"

# === Default ===
.DEFAULT_GOAL := help