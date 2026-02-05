.PHONY: setup setup-backend setup-frontend dev dev-backend dev-frontend stop clean

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
	@echo "🚀 Starting Community Content Hub..."
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
