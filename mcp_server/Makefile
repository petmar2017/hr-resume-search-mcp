# === HR Resume Search MCP Server Makefile ===
# Python 3.12 MCP Server with HR Tools

# === Variables ===
UV_PYTHON := /opt/homebrew/bin/python3.12
export UV_PYTHON
UV := uv
PYTHON := $(UV) run python
PROJECT := hr-resume-search-mcp
COVERAGE_TARGET := 80

# === Colors ===
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# === Help ===
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)$(PROJECT) - MCP Server Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Python Version: $(UV_PYTHON)$(NC)"
	@echo "$(YELLOW)Coverage Target: $(COVERAGE_TARGET)%$(NC)"

# === Setup Commands ===
.PHONY: setup
setup: ## Complete project setup
	@echo "$(BLUE)Setting up $(PROJECT)...$(NC)"
	@$(MAKE) check-python
	@$(MAKE) create-venv
	@$(MAKE) install
	@$(MAKE) setup-db
	@$(MAKE) setup-directories
	@echo "$(GREEN)Setup complete!$(NC)"

.PHONY: check-python
check-python: ## Check Python version
	@echo "$(BLUE)Checking Python version...$(NC)"
	@if [ ! -f "$(UV_PYTHON)" ]; then \
		echo "$(RED)Error: Python 3.12 not found at $(UV_PYTHON)$(NC)"; \
		exit 1; \
	fi
	@$(UV_PYTHON) --version | grep -q "3.12" || (echo "$(RED)Error: Python 3.12 required$(NC)" && exit 1)
	@echo "$(GREEN)Python 3.12 confirmed$(NC)"

.PHONY: create-venv
create-venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	@$(UV) venv --python $(UV_PYTHON)
	@echo "$(GREEN)Virtual environment created$(NC)"

.PHONY: install
install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@$(UV) pip install -r requirements.txt
	@echo "$(GREEN)Production dependencies installed$(NC)"

.PHONY: install-dev
install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@$(UV) pip install -r requirements-dev.txt
	@echo "$(GREEN)Development dependencies installed$(NC)"

.PHONY: setup-db
setup-db: ## Setup database
	@echo "$(BLUE)Setting up database...$(NC)"
	@mkdir -p hr_database
	@echo '{"resumes": {}, "index": {}, "relationships": {}}' > hr_database/resumes.json
	@echo "$(GREEN)Database initialized$(NC)"

.PHONY: setup-directories
setup-directories: ## Create project directories
	@echo "$(BLUE)Creating project directories...$(NC)"
	@mkdir -p logs tests templates hr_database models parsers database
	@touch logs/.gitkeep tests/.gitkeep
	@echo "$(GREEN)Directories created$(NC)"

# === Development Commands ===
.PHONY: run
run: ## Run MCP server
	@echo "$(BLUE)Starting MCP server...$(NC)"
	@$(PYTHON) -m mcp_server.server

.PHONY: dev
dev: ## Run in development mode with auto-reload
	@echo "$(BLUE)Starting MCP server in development mode...$(NC)"
	@$(UV) run watchdog server.py --command="$(PYTHON) -m mcp_server.server"

.PHONY: mcp-dev
mcp-dev: dev ## Alias for dev mode

.PHONY: mcp-run
mcp-run: run ## Alias for run

# === Testing Commands ===
.PHONY: test
test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(PYTHON) -m pytest tests/ -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(PYTHON) -m pytest tests/ --cov=. --cov-report=html --cov-report=term
	@echo "$(YELLOW)Coverage report generated in htmlcov/$(NC)"

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(PYTHON) -m pytest tests/test_mcp_server.py::TestMCPServerCore -v

.PHONY: test-hr
test-hr: ## Run HR tools tests
	@echo "$(BLUE)Running HR tools tests...$(NC)"
	@$(PYTHON) -m pytest tests/test_mcp_server.py::TestHRTools -v

.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(PYTHON) -m pytest tests/test_mcp_server.py::TestIntegration -v

.PHONY: mcp-test-comprehensive
mcp-test-comprehensive: ## Run comprehensive MCP tests (23 tests)
	@echo "$(BLUE)Running comprehensive MCP tests...$(NC)"
	@$(PYTHON) -m pytest tests/ -v --tb=short
	@echo "$(GREEN)Comprehensive tests complete$(NC)"

.PHONY: mcp-test-interactive
mcp-test-interactive: ## Manual interactive testing
	@echo "$(BLUE)Starting interactive test session...$(NC)"
	@$(PYTHON) -c "from mcp_server.server import app; print('MCP Server loaded. Use app to test tools.')"

.PHONY: mcp-test-concurrent
mcp-test-concurrent: ## Stress test with concurrent requests
	@echo "$(BLUE)Running concurrent stress tests...$(NC)"
	@$(PYTHON) -m pytest tests/test_mcp_server.py::TestIntegration::test_concurrent_operations -v

.PHONY: mcp-test-performance
mcp-test-performance: ## Test performance requirements
	@echo "$(BLUE)Running performance tests...$(NC)"
	@$(PYTHON) -m pytest tests/test_mcp_server.py::TestIntegration::test_performance -v

.PHONY: mcp-test-report
mcp-test-report: ## Generate test report
	@echo "$(BLUE)Generating test report...$(NC)"
	@$(PYTHON) -m pytest tests/ --html=test_report.html --self-contained-html
	@echo "$(GREEN)Report generated: test_report.html$(NC)"

# === Code Quality Commands ===
.PHONY: lint
lint: ## Run linting
	@echo "$(BLUE)Running linters...$(NC)"
	@$(UV) run ruff check .
	@$(UV) run mypy . --ignore-missing-imports
	@echo "$(GREEN)Linting complete$(NC)"

.PHONY: format
format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(UV) run black .
	@$(UV) run ruff check --fix .
	@echo "$(GREEN)Formatting complete$(NC)"

.PHONY: type-check
type-check: ## Run type checking
	@echo "$(BLUE)Running type checks...$(NC)"
	@$(UV) run mypy . --ignore-missing-imports
	@echo "$(GREEN)Type checking complete$(NC)"

.PHONY: security-check
security-check: ## Check for security vulnerabilities
	@echo "$(BLUE)Checking for security vulnerabilities...$(NC)"
	@$(UV) pip audit
	@echo "$(GREEN)Security check complete$(NC)"

# === Documentation Commands ===
.PHONY: docs
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@$(UV) run mkdocs build
	@echo "$(GREEN)Documentation generated in site/$(NC)"

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@$(UV) run mkdocs serve

.PHONY: api-docs
api-docs: ## Generate API documentation
	@echo "$(BLUE)Generating API documentation...$(NC)"
	@$(PYTHON) -c "from mcp_server.server import app; import json; print(json.dumps({'tools': [t.__name__ for t in app._tools]}, indent=2))"

# === Database Commands ===
.PHONY: db-reset
db-reset: ## Reset database
	@echo "$(YELLOW)Warning: This will delete all data!$(NC)"
	@read -p "Continue? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf hr_database/*.json; \
		$(MAKE) setup-db; \
		echo "$(GREEN)Database reset complete$(NC)"; \
	fi

.PHONY: db-backup
db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	@cp -r hr_database backups/hr_database_$$(date +%Y%m%d_%H%M%S)
	@echo "$(GREEN)Backup complete$(NC)"

.PHONY: db-restore
db-restore: ## Restore database from latest backup
	@echo "$(BLUE)Restoring database...$(NC)"
	@if [ -d "backups" ]; then \
		latest=$$(ls -t backups | head -1); \
		if [ -n "$$latest" ]; then \
			cp -r backups/$$latest/* hr_database/; \
			echo "$(GREEN)Restored from $$latest$(NC)"; \
		else \
			echo "$(RED)No backups found$(NC)"; \
		fi; \
	else \
		echo "$(RED)No backup directory found$(NC)"; \
	fi

.PHONY: test-db-connection
test-db-connection: ## Test database connection
	@echo "$(BLUE)Testing database connection...$(NC)"
	@$(PYTHON) -c "import json; p=open('hr_database/resumes.json','r'); d=json.load(p); print('Database OK')"

# === Docker Commands ===
.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t $(PROJECT):latest .
	@echo "$(GREEN)Docker image built$(NC)"

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	@docker run -p 8080:8080 --env-file .env $(PROJECT):latest

.PHONY: docker-push
docker-push: ## Push Docker image
	@echo "$(BLUE)Pushing Docker image...$(NC)"
	@docker push $(PROJECT):latest

# === Deployment Commands ===
.PHONY: deploy
deploy: ## Deploy to Kubernetes
	@echo "$(BLUE)Deploying to Kubernetes...$(NC)"
	@kubectl apply -f k8s/
	@echo "$(GREEN)Deployment complete$(NC)"

.PHONY: deploy-status
deploy-status: ## Check deployment status
	@echo "$(BLUE)Checking deployment status...$(NC)"
	@kubectl get pods -l app=$(PROJECT)
	@kubectl get services -l app=$(PROJECT)

# === Monitoring Commands ===
.PHONY: logs
logs: ## Show server logs
	@tail -f logs/mcp.log

.PHONY: monitor
monitor: ## Monitor server performance
	@echo "$(BLUE)Monitoring server performance...$(NC)"
	@$(PYTHON) -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"

.PHONY: monitor-performance
monitor-performance: monitor ## Alias for monitor

# === Utility Commands ===
.PHONY: clean
clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	@rm -f test_report.html
	@echo "$(GREEN)Cleanup complete$(NC)"

.PHONY: validate
validate: ## Validate project setup
	@echo "$(BLUE)Validating project setup...$(NC)"
	@$(MAKE) check-python
	@test -f requirements.txt || (echo "$(RED)Missing requirements.txt$(NC)" && exit 1)
	@test -f server.py || (echo "$(RED)Missing server.py$(NC)" && exit 1)
	@test -d hr_database || (echo "$(RED)Missing hr_database directory$(NC)" && exit 1)
	@echo "$(GREEN)Validation passed$(NC)"

.PHONY: version
version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "  Project: $(PROJECT)"
	@echo "  Python: $$($(UV_PYTHON) --version)"
	@echo "  MCP: $$($(PYTHON) -c 'import mcp; print(mcp.__version__)' 2>/dev/null || echo 'Not installed')"

.PHONY: install-claude-desktop
install-claude-desktop: ## Install Claude Desktop configuration
	@echo "$(BLUE)Installing Claude Desktop configuration...$(NC)"
	@echo "$(YELLOW)Add the following to your Claude Desktop config:$(NC)"
	@cat claude_desktop_config.json
	@echo ""
	@echo "$(YELLOW)Config location: ~/Library/Application Support/Claude/claude_desktop_config.json$(NC)"

# === Git Commands ===
.PHONY: git-commit
git-commit: ## Commit changes
	@echo "$(BLUE)Committing changes...$(NC)"
	@git add -A
	@git commit -m "Progress: MCP server updates - $$(date +%Y-%m-%d_%H:%M:%S)"
	@echo "$(GREEN)Changes committed$(NC)"

.PHONY: git-status
git-status: ## Show git status
	@git status

# === All-in-one Commands ===
.PHONY: all
all: setup install-dev test-coverage lint ## Complete setup and test

.PHONY: ci
ci: lint type-check test-coverage ## Run CI pipeline

.PHONY: release
release: clean lint test-coverage docker-build ## Prepare for release

# Default target
.DEFAULT_GOAL := help