.PHONY: dev test lint migrate docker-up docker-down clean install

# ── Development ───────────────────────────────────────────────────────────────

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# ── Linting ───────────────────────────────────────────────────────────────────

lint:
	ruff check app/ tests/

lint-fix:
	ruff check app/ tests/ --fix

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	alembic upgrade head

migrate-new:
	@read -p "Migration message: " msg; alembic revision --autogenerate -m "$$msg"

migrate-down:
	alembic downgrade -1

# ── Docker ────────────────────────────────────────────────────────────────────

docker-build:
	docker build -t emotion-detection:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov .pytest_cache .ruff_cache
	rm -f *.db test.db
