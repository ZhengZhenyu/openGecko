.PHONY: setup setup-backend setup-frontend dev dev-backend dev-frontend stop clean \
        docker-dev docker-prod docker-prod-down docker-logs docker-status

# ── One-command setup ─────────────────────────────────────────────────
setup: setup-backend setup-frontend
	@echo ""
	@echo "✅ Setup complete! Run 'make dev' to start."

setup-backend:
	@echo "📦 Setting up backend..."
	cd backend && python3 -m venv .venv
	cd backend && .venv/bin/pip install -r requirements.txt -q
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; echo "📝 Created backend/.env — edit it to add your API keys"; fi

setup-frontend:
	@echo "📦 Setting up frontend..."
	cd frontend && npm install --silent

# ── Development server (starts both backend & frontend) ───────────────
dev:
	@echo "🚀 Starting openGecko..."
	@echo "   Backend:  http://localhost:8000  (API docs: http://localhost:8000/docs)"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Press Ctrl+C to stop both services"
	@echo ""
	@trap 'kill 0' EXIT; \
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000 & \
	cd frontend && npx vite --port 3000 & \
	wait

dev-backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npx vite --port 3000

# ── Docker 开发模式（热重载）─────────────────────────────────────────
docker-dev:
	@echo "🐳 Starting openGecko in Docker (dev mode)..."
	docker compose up --build

# ── Docker 生产模式（gunicorn + 资源限制 + 日志驱动）────────────────
docker-prod:
	@echo "🚀 Starting openGecko in production mode..."
	@if [ ! -f backend/.env ]; then echo "❌ backend/.env not found! Copy from backend/.env.prod.example"; exit 1; fi
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo "✅ Production stack started"
	@echo "   Frontend: http://localhost:80"
	@echo "   Backend:  http://localhost:8000"
	@echo "   Run 'make docker-logs' to view logs"

docker-prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

docker-logs:
	docker compose logs -f --tail=100

docker-status:
	docker compose ps

# ── Stop background processes ─────────────────────────────────────────
stop:
	@-pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@-pkill -f "vite --port 3000" 2>/dev/null || true
	@echo "Stopped."

# ── Clean build artifacts ─────────────────────────────────────────────
clean:
	rm -rf backend/.venv backend/__pycache__ backend/*.db
	rm -rf frontend/node_modules frontend/dist
	@echo "Cleaned."
