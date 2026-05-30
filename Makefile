.PHONY: dev up down seed test lint

dev:
	docker compose up --build

up:
	docker compose up -d --build

down:
	docker compose down -v

seed:
	docker compose exec platform-api python scripts/seed_demo_data.py

test:
	cd services/platform-api && python -m pytest tests/ -v --tb=short

lint:
	cd services/platform-api && python -m ruff check app/ || echo "ruff not installed, skipping"
	cd apps/web && npm run lint || echo "no lint script"

logs-api:
	docker compose logs -f platform-api

logs-web:
	docker compose logs -f web
