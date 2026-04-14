# ─────────────────────────────────────────────────────────────────────────────
# QA Hub Hackathon 2026 — <QCoders/>
# Makefile must be run from the project/ directory.
# ─────────────────────────────────────────────────────────────────────────────

.DEFAULT_GOAL := help
.PHONY: help \
        api api-start api-test api-down \
        ui  ui-start  ui-test  ui-down  \
        report

# ── Colours ──────────────────────────────────────────────────────────────────
BOLD  := \033[1m
CYAN  := \033[36m
GREEN := \033[32m
RESET := \033[0m

# ── Paths ─────────────────────────────────────────────────────────────────────
API_DIR := automation/api
UI_DIR  := automation/ui

# ─────────────────────────────────────────────────────────────────────────────
# HELP
# ─────────────────────────────────────────────────────────────────────────────
help:
	@printf "$(BOLD)$(CYAN)<QCoders/>$(RESET) — QA Hub Hackathon 2026\n\n"
	@printf "$(BOLD)API targets (Custom Django API — port 8001):$(RESET)\n"
	@printf "  $(GREEN)make api$(RESET)        Start API server + install deps + run all pytest tests\n"
	@printf "  $(GREEN)make api-start$(RESET)  Start API server only (waits until ready)\n"
	@printf "  $(GREEN)make api-test$(RESET)   Run pytest (server must already be up)\n"
	@printf "  $(GREEN)make api-down$(RESET)   Stop & remove API containers\n\n"
	@printf "$(BOLD)UI targets (Real InvenTree — port 8000):$(RESET)\n"
	@printf "  $(GREEN)make ui$(RESET)         Start InvenTree + install deps + run all Playwright tests\n"
	@printf "  $(GREEN)make ui-start$(RESET)   Start InvenTree only (waits until ready)\n"
	@printf "  $(GREEN)make ui-test$(RESET)    Run Playwright tests (InvenTree must already be up)\n"
	@printf "  $(GREEN)make ui-down$(RESET)    Stop & remove InvenTree containers\n\n"
	@printf "$(BOLD)Misc:$(RESET)\n"
	@printf "  $(GREEN)make report$(RESET)     Open the last Playwright HTML report\n"

# ─────────────────────────────────────────────────────────────────────────────
# API — Custom Django REST API (port 8001)
# ─────────────────────────────────────────────────────────────────────────────

## Start API server, install Python deps, run full pytest suite
api: api-start api-test

## Start API server in the background and wait until it is ready
api-start:
	@printf "$(BOLD)Starting Custom Django API...$(RESET)\n"
	cd $(API_DIR) && docker compose up --build -d
	@printf "Waiting for API to become ready at http://localhost:8001 ...\n"
	@until curl -sf http://localhost:8001/api/part/ > /dev/null 2>&1; do \
		printf "."; sleep 2; \
	done
	@printf "\n$(GREEN)API ready$(RESET) → http://localhost:8001/api/part/\n"
	@printf "Swagger UI → http://localhost:8001/api/schema/swagger-ui/\n"

## Install Python test dependencies and run pytest
api-test:
	@printf "$(BOLD)Installing Python test dependencies...$(RESET)\n"
	cd $(API_DIR) && pip install -q -r requirements-test.txt
	@printf "$(BOLD)Running pytest...$(RESET)\n"
	cd $(API_DIR) && pytest tests/ -v

## Stop and remove API containers
api-down:
	@printf "$(BOLD)Stopping Custom Django API...$(RESET)\n"
	cd $(API_DIR) && docker compose down

# ─────────────────────────────────────────────────────────────────────────────
# UI — Real InvenTree (port 8000) + Playwright
# ─────────────────────────────────────────────────────────────────────────────

## Start InvenTree, install Node deps + Playwright browsers, run full UI suite
ui: ui-start ui-test

## Start InvenTree in the background and wait until it is ready
ui-start:
	@printf "$(BOLD)Starting InvenTree...$(RESET)\n"
	cd $(UI_DIR) && docker compose up -d
	@printf "Waiting for InvenTree to become ready at http://localhost:8000 ...\n"
	@until curl -sf http://localhost:8000/api/ > /dev/null 2>&1; do \
		printf "."; sleep 3; \
	done
	@printf "\n$(GREEN)InvenTree ready$(RESET) → http://localhost:8000/web/\n"

## Install npm dependencies + Playwright browsers, then run all Playwright tests
ui-test:
	@printf "$(BOLD)Installing Node dependencies...$(RESET)\n"
	cd $(UI_DIR) && npm ci --silent
	@printf "$(BOLD)Installing Playwright browsers...$(RESET)\n"
	cd $(UI_DIR) && npx playwright install chromium --with-deps
	@printf "$(BOLD)Running Playwright tests...$(RESET)\n"
	cd $(UI_DIR) && npx playwright test

## Stop and remove InvenTree containers
ui-down:
	@printf "$(BOLD)Stopping InvenTree...$(RESET)\n"
	cd $(UI_DIR) && docker compose down

# ─────────────────────────────────────────────────────────────────────────────
# MISC
# ─────────────────────────────────────────────────────────────────────────────

## Open the Playwright HTML report from the last test run
report:
	cd $(UI_DIR) && npx playwright show-report
