.PHONY: setup db-up db-import-sqlite db-down db-logs dev logs

DATABASE_URL := postgresql://paper_radar:paper_radar@localhost:5432/paper_radar

setup:
	env -u VIRTUAL_ENV uv sync --directory backend
	npm --prefix frontend install

db-up:
	docker compose up -d --wait db

db-import-sqlite: db-up
	cd backend && env -u VIRTUAL_ENV RADAR_DATABASE_URL="$(DATABASE_URL)" uv run python -m migrations.import_sqlite

db-down:
	docker compose down

db-logs:
	docker compose logs -f db

dev:
	@$(MAKE) db-up
	@set -e; \
	(cd backend && exec env -u VIRTUAL_ENV RADAR_DATABASE_URL="$(DATABASE_URL)" .venv/bin/uvicorn app.main:app --reload --no-access-log) & backend_pid=$$!; \
	(cd frontend && exec ./node_modules/.bin/vite) & frontend_pid=$$!; \
	trap 'kill "$$backend_pid" "$$frontend_pid" 2>/dev/null || true; wait' INT TERM EXIT; \
	wait

logs:
	tail -f backend/logs/paper-radar.log
