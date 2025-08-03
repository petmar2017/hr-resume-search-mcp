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
test: ## Run all tests (Python, curl, MCP integration, enhanced services)
	@echo "$(BOLD)Running comprehensive test suite...$(RESET)"
	$(MAKE) test-python
	$(MAKE) test-curl
	$(MAKE) test-mcp
	$(MAKE) test-enhanced
	@echo "$(GREEN)✓ All tests completed$(RESET)"

.PHONY: test-all
test-all: ## Run all tests including load tests (comprehensive)
	@echo "$(BOLD)Running complete test suite with load tests...$(RESET)"
	$(MAKE) test
	$(MAKE) test-load
	@echo "$(GREEN)✓ Complete test suite finished$(RESET)"

.PHONY: test-python
test-python: ## Run Python pytest suite
	@echo "$(BOLD)Running Python tests...$(RESET)"
	$(PYTHON) -m pytest tests/ -v --ignore=tests/curl_tests.sh --ignore=tests/mcp_curl_tests.sh --ignore=tests/simple_curl_tests.sh --ignore=tests/run_all_tests.sh

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

.PHONY: test-curl
test-curl: ## Run curl-based API tests
	@echo "$(BOLD)Running curl API tests...$(RESET)"
	@if curl -s -f http://localhost:8000/health > /dev/null; then \
		chmod +x tests/simple_curl_tests.sh tests/run_all_tests.sh tests/curl_tests.sh 2>/dev/null || true; \
		tests/simple_curl_tests.sh; \
	else \
		echo "$(RED)Error: FastAPI server not running on localhost:8000$(RESET)"; \
		echo "Start server with: make dev"; \
		exit 1; \
	fi

.PHONY: test-mcp
test-mcp: ## Run MCP server integration tests
	@echo "$(BOLD)Running MCP integration tests...$(RESET)"
	@if curl -s -f http://localhost:8000/health > /dev/null; then \
		chmod +x tests/mcp_curl_tests.sh; \
		echo "y" | tests/mcp_curl_tests.sh; \
	else \
		echo "$(RED)Error: FastAPI server not running on localhost:8000$(RESET)"; \
		echo "Start server with: make dev"; \
		exit 1; \
	fi

.PHONY: test-comprehensive
test-comprehensive: ## Run comprehensive test suite with detailed reporting
	@echo "$(BOLD)Running comprehensive test suite...$(RESET)"
	@if curl -s -f http://localhost:8000/health > /dev/null; then \
		chmod +x tests/run_all_tests.sh; \
		tests/run_all_tests.sh; \
	else \
		echo "$(RED)Error: FastAPI server not running on localhost:8000$(RESET)"; \
		echo "Start server with: make dev"; \
		exit 1; \
	fi

.PHONY: test-enhanced
test-enhanced: ## Run enhanced service capability tests
	@echo "$(BOLD)Running enhanced service tests...$(RESET)"
	$(PYTHON) test_minimal_file_service.py
	$(PYTHON) test_end_to_end_streaming_workflow.py
	@if [ -f tests/integration/test_claude_service_enhanced.py ]; then \
		$(PYTHON) -m pytest tests/integration/test_claude_service_enhanced.py -v; \
	fi
	@if [ -f tests/integration/test_file_service_enhanced.py ]; then \
		$(PYTHON) -m pytest tests/integration/test_file_service_enhanced.py -v; \
	fi
	@echo "$(GREEN)✓ Enhanced service tests completed$(RESET)"

.PHONY: test-jupyter
test-jupyter: ## Run Jupyter notebook API tests
	@echo "$(BOLD)Running Jupyter notebook tests...$(RESET)"
	@if command -v jupyter >/dev/null 2>&1; then \
		echo "Opening API testing notebook..."; \
		jupyter notebook notebooks/api_testing.ipynb; \
	else \
		echo "$(YELLOW)Jupyter not found. Install with: $(UV) pip install jupyter$(RESET)"; \
	fi

.PHONY: coverage-html
coverage-html: ## Open HTML coverage report
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html in your browser"

# === MCP Server Testing ===
.PHONY: mcp-test-comprehensive
mcp-test-comprehensive: ## Run comprehensive MCP tests (curl + Python integration)
	@echo "$(BOLD)Running comprehensive MCP tests...$(RESET)"
	$(MAKE) test-mcp
	@if [ -f tests/test_mcp_integration.py ]; then \
		$(PYTHON) -m pytest tests/test_mcp_integration.py -v; \
	else \
		echo "$(YELLOW)⚠ Python MCP tests not available$(RESET)"; \
	fi

.PHONY: mcp-test-interactive
mcp-test-interactive: ## Run interactive MCP tests with detailed output
	@echo "$(BOLD)Running interactive MCP tests...$(RESET)"
	@if curl -s -f http://localhost:8000/health > /dev/null; then \
		chmod +x tests/mcp_curl_tests.sh; \
		tests/mcp_curl_tests.sh; \
	else \
		echo "$(RED)Error: FastAPI server not running$(RESET)"; \
		exit 1; \
	fi

.PHONY: mcp-test-concurrent
mcp-test-concurrent: ## Run concurrent MCP stress tests
	@echo "$(BOLD)Running concurrent MCP tests...$(RESET)"
	@for i in {1..5}; do \
		echo "Running concurrent test batch $$i..."; \
		curl -s -X POST http://localhost:8000/mcp \
			-H "Content-Type: application/json" \
			-d '{"id":"concurrent-'$$i'","method":"tools/list","params":{}}' & \
	done; \
	wait; \
	echo "$(GREEN)✓ Concurrent tests completed$(RESET)"

.PHONY: mcp-test-report
mcp-test-report: ## Generate comprehensive MCP test report
	@echo "$(BOLD)Generating MCP test report...$(RESET)"
	@mkdir -p reports
	@echo "# MCP Test Report - $(shell date)" > reports/mcp_test_report.md
	@echo "" >> reports/mcp_test_report.md
	@echo "## Server Status" >> reports/mcp_test_report.md
	@curl -s http://localhost:8000/health | python3 -m json.tool >> reports/mcp_test_report.md 2>/dev/null || echo "Server unavailable" >> reports/mcp_test_report.md
	@echo "" >> reports/mcp_test_report.md
	@echo "## Available Tools" >> reports/mcp_test_report.md
	@curl -s http://localhost:8000/mcp/tools | python3 -m json.tool >> reports/mcp_test_report.md 2>/dev/null || echo "Tools unavailable" >> reports/mcp_test_report.md
	@echo "$(GREEN)✓ Report generated: reports/mcp_test_report.md$(RESET)"

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
	$(UV) run alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(RESET)"

.PHONY: db-rollback
db-rollback: ## Rollback database migration
	@echo "$(BOLD)Rolling back migration...$(RESET)"
	$(UV) run alembic downgrade -1
	@echo "$(GREEN)✓ Rollback complete$(RESET)"

.PHONY: db-seed
db-seed: ## Seed database with test data
	@echo "$(BOLD)Seeding database...$(RESET)"
	python3 scripts/seed_data_sync.py
	@echo "$(GREEN)✓ Database seeded$(RESET)"

.PHONY: db-status
db-status: ## Show database migration status
	@echo "$(BOLD)Database Status:$(RESET)"
	$(UV) run alembic current
	$(UV) run alembic history --verbose

.PHONY: db-create-migration
db-create-migration: ## Create new migration (use MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Usage: make db-create-migration MSG=\"add_new_table\"$(RESET)"; \
	else \
		$(UV) run alembic revision --autogenerate -m "$(MSG)"; \
		echo "$(GREEN)✓ Migration created$(RESET)"; \
	fi

.PHONY: db-reset
db-reset: ## Reset database (CAUTION: destroys all data)
	@echo "$(RED)⚠ This will destroy all data. Continue? [y/N]$(RESET)"
	@read confirmation && [ "$$confirmation" = "y" ] || exit 1
	$(UV) run alembic downgrade base
	$(UV) run alembic upgrade head
	python3 scripts/seed_data_sync.py
	@echo "$(GREEN)✓ Database reset complete$(RESET)"

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

.PHONY: metrics-summary
metrics-summary: ## Show human-readable metrics summary
	@echo "$(BOLD)Metrics Summary:$(RESET)"
	@curl -s http://localhost:8000/metrics/summary | python -m json.tool 2>/dev/null || echo "Metrics summary not available"

.PHONY: health
health: ## Check application health
	@echo "$(BOLD)Health Check:$(RESET)"
	@curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || echo "Health endpoint not available"

.PHONY: monitoring-start
monitoring-start: ## Start monitoring stack (Prometheus + Grafana)
	@echo "$(BOLD)Starting monitoring stack...$(RESET)"
	cd monitoring && docker-compose -f docker-compose.monitoring.yml up -d
	@echo "$(GREEN)✓ Monitoring stack started$(RESET)"
	@echo "$(CYAN)Grafana: http://localhost:3000 (admin/admin_change_me)$(RESET)"
	@echo "$(CYAN)Prometheus: http://localhost:9090$(RESET)"

.PHONY: monitoring-stop
monitoring-stop: ## Stop monitoring stack
	@echo "$(BOLD)Stopping monitoring stack...$(RESET)"
	cd monitoring && docker-compose -f docker-compose.monitoring.yml down
	@echo "$(GREEN)✓ Monitoring stack stopped$(RESET)"

.PHONY: monitoring-logs
monitoring-logs: ## Show monitoring stack logs
	@echo "$(BOLD)Monitoring Stack Logs:$(RESET)"
	cd monitoring && docker-compose -f docker-compose.monitoring.yml logs -f

.PHONY: monitoring-status
monitoring-status: ## Check monitoring stack status
	@echo "$(BOLD)Monitoring Stack Status:$(RESET)"
	cd monitoring && docker-compose -f docker-compose.monitoring.yml ps

.PHONY: performance-test
performance-test: ## Run performance validation tests
	@echo "$(BOLD)Running performance tests...$(RESET)"
	@echo "$(YELLOW)Testing API response times...$(RESET)"
	@for i in {1..10}; do \
		echo "Request $$i:"; \
		curl -w "Response time: %{time_total}s\n" -s -o /dev/null http://localhost:8000/health; \
	done
	@echo "$(GREEN)✓ Performance test completed$(RESET)"
	@echo "$(CYAN)Check Grafana dashboard for detailed metrics$(RESET)"

# === Load Testing ===
.PHONY: test-load
test-load: ## Run all load tests (upload, search, MCP streaming)
	@echo "$(BOLD)Running comprehensive load tests...$(RESET)"
	$(MAKE) test-load-upload
	$(MAKE) test-load-search
	$(MAKE) test-load-mcp
	@echo "$(GREEN)✓ All load tests completed$(RESET)"

.PHONY: test-load-upload
test-load-upload: ## Run concurrent resume upload load tests
	@echo "$(BOLD)Running concurrent upload load tests...$(RESET)"
	$(PYTHON) tests/load/test_concurrent_resume_upload.py
	@echo "$(GREEN)✓ Upload load tests completed$(RESET)"

.PHONY: test-load-search
test-load-search: ## Run high-volume search query load tests
	@echo "$(BOLD)Running high-volume search load tests...$(RESET)"
	$(PYTHON) tests/load/test_high_volume_search.py
	@echo "$(GREEN)✓ Search load tests completed$(RESET)"

.PHONY: test-load-mcp
test-load-mcp: ## Run MCP streaming response load tests
	@echo "$(BOLD)Running MCP streaming load tests...$(RESET)"
	@if [ -f tests/load/test_mcp_streaming.py ]; then \
		$(PYTHON) tests/load/test_mcp_streaming.py; \
	else \
		echo "$(YELLOW)⚠ MCP streaming tests pending implementation$(RESET)"; \
	fi
	@echo "$(GREEN)✓ MCP load tests completed$(RESET)"

.PHONY: test-load-report
test-load-report: ## Generate comprehensive load test report
	@echo "$(BOLD)Generating load test report...$(RESET)"
	@mkdir -p reports
	@echo "# Load Test Report - $(shell date)" > reports/load_test_report.md
	@echo "" >> reports/load_test_report.md
	@echo "## Test Results Summary" >> reports/load_test_report.md
	@if [ -f concurrent_upload_load_test_results.json ]; then \
		echo "### Concurrent Upload Tests" >> reports/load_test_report.md; \
		echo "\`\`\`json" >> reports/load_test_report.md; \
		cat concurrent_upload_load_test_results.json >> reports/load_test_report.md; \
		echo "\`\`\`" >> reports/load_test_report.md; \
	fi
	@if [ -f high_volume_search_load_test_results.json ]; then \
		echo "### High-Volume Search Tests" >> reports/load_test_report.md; \
		echo "\`\`\`json" >> reports/load_test_report.md; \
		cat high_volume_search_load_test_results.json >> reports/load_test_report.md; \
		echo "\`\`\`" >> reports/load_test_report.md; \
	fi
	@echo "$(GREEN)✓ Load test report generated: reports/load_test_report.md$(RESET)"

.PHONY: test-stress
test-stress: ## Run stress tests with high concurrency
	@echo "$(BOLD)Running stress tests...$(RESET)"
	@echo "$(YELLOW)⚠ High resource usage expected$(RESET)"
	$(PYTHON) tests/load/test_concurrent_resume_upload.py
	@echo "$(GREEN)✓ Stress tests completed$(RESET)"

.PHONY: test-performance-baseline
test-performance-baseline: ## Establish performance baselines
	@echo "$(BOLD)Establishing performance baselines...$(RESET)"
	@mkdir -p reports/baselines
	@echo "Recording baseline metrics..."
	$(MAKE) test-load > reports/baselines/baseline_$(shell date +%Y%m%d_%H%M%S).log 2>&1
	@echo "$(GREEN)✓ Performance baseline recorded$(RESET)"

# === Default ===
.DEFAULT_GOAL := help