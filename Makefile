# FreelanceHub — Developer Makefile
# Usage: make <target>

.PHONY: help \
        up down restart logs \
        db-up db-down \
        backend frontend \
        migrate migrate-create freeze \
        install-backend install-frontend \
        clean

# ── Default ───────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  FreelanceHub — available commands"
	@echo ""
	@echo "  Infrastructure"
	@echo "    make up             Start all Docker services (postgres + redis)"
	@echo "    make down           Stop and remove Docker containers"
	@echo "    make restart        Restart Docker services"
	@echo "    make logs           Tail logs from all Docker services"
	@echo "    make db-up          Start only the database (postgres)"
	@echo "    make db-down        Stop only the database"
	@echo ""
	@echo "  Development servers"
	@echo "    make backend        Run FastAPI dev server (port 8000)"
	@echo "    make frontend       Run Vite dev server (port 5173)"
	@echo ""
	@echo "  Database"
	@echo "    make migrate        Apply all pending Alembic migrations"
	@echo "    make migrate-create msg=\"description\"  Create a new migration"
	@echo ""
	@echo "  Dependencies"
	@echo "    make freeze         Freeze pip packages to requirements.txt"
	@echo "    make install-backend   Install Python dependencies"
	@echo "    make install-frontend  Install Node dependencies"
	@echo ""
	@echo "  Cleanup"
	@echo "    make clean          Remove __pycache__, .pyc files"
	@echo ""

# ── Docker ────────────────────────────────────────────────────────────────────

up:
	docker compose up -d
	@echo "✓ Services started"

down:
	docker compose down
	@echo "✓ Services stopped"

restart:
	docker compose down
	docker compose up -d
	@echo "✓ Services restarted"

logs:
	docker compose logs -f

db-up:
	docker compose up -d postgres
	@echo "✓ Postgres started"

db-down:
	docker compose stop postgres
	@echo "✓ Postgres stopped"

# ── Dev servers ───────────────────────────────────────────────────────────────

backend:
	cd backend && \
	  . venv/bin/activate && \
	  uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

# ── Database migrations ───────────────────────────────────────────────────────

migrate:
	cd backend && \
	  . venv/bin/activate && \
	  alembic upgrade head
	@echo "✓ Migrations applied"

migrate-create:
	@[ -n "$(msg)" ] || (echo "Error: provide a message — make migrate-create msg=\"add users table\"" && exit 1)
	cd backend && \
	  . venv/bin/activate && \
	  alembic revision --autogenerate -m "$(msg)"
	@echo "✓ Migration created"

# ── Dependencies ──────────────────────────────────────────────────────────────

freeze:
	cd backend && \
	  . venv/bin/activate && \
	  pip freeze > requirements.txt
	@echo "✓ requirements.txt updated"

install-backend:
	cd backend && \
	  . venv/bin/activate && \
	  pip install -r requirements.txt
	@echo "✓ Backend dependencies installed"

install-frontend:
	cd frontend && npm install
	@echo "✓ Frontend dependencies installed"

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned up cache files"
