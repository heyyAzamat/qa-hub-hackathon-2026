<div align="center">

# `<QCoders/>`

### QA Hub Hackathon 2026 — InvenTree Parts Module

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![pytest](https://img.shields.io/badge/pytest-181%20passed-brightgreen?logo=pytest&logoColor=white)](https://pytest.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.44-E2571C?logo=playwright&logoColor=white)](https://playwright.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![AI](https://img.shields.io/badge/AI-Claude%20Code-7C3AED?logo=anthropic&logoColor=white)](https://claude.ai/code)

*AI-driven QA automation: from requirements analysis to executable test suites*

</div>

---

## Overview

This project demonstrates a **modern AI-assisted QA workflow** for the **InvenTree Parts Module** — an open-source inventory management system built with Python/Django.

An AI agent (Claude Code) drove every phase: reading requirements, generating test cases, writing automation scripts, fixing bugs, and validating the final suite.

**All three phases complete:**

| Phase | Deliverable | Status |
|-------|------------|--------|
| 1 — UI Analysis | 101 manual test cases | ✅ Done |
| 2 — API Automation | 131 manual cases + **181 automated pytest tests** | ✅ Done |
| 3 — UI Automation | 41 Playwright tests across 7 spec files | ✅ Done |

---

## Architecture

Two independent servers — run them separately (no shared state, no shared port):

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│   Custom Django REST API        │     │   Real InvenTree (official image) │
│   automation/api/               │     │   automation/ui/docker-compose.yml│
│                                 │     │                                   │
│   localhost:8001                │     │   localhost:8000                  │
│   admin / admin                 │     │   admin / inventree               │
│                                 │     │                                   │
│   ← pytest + requests           │     │   ← Playwright + TypeScript       │
└─────────────────────────────────┘     └──────────────────────────────────┘
```

| System | Port | Purpose | Credentials |
|--------|------|---------|-------------|
| Custom Django API (`automation/api/`) | **:8001** | Target of pytest API tests | `admin` / `admin` |
| Real InvenTree (official Docker image) | **:8000** | Target of Playwright UI tests | `admin` / `inventree` |

---

## Quick Start

```bash
# Clone and enter the project directory
cd project/

# Run API tests (Docker + pytest)
make api

# Run UI tests (Docker + Playwright)
make ui
```

That's it. Each `make` target handles everything end-to-end.

---

## Prerequisites

| Tool | Version | Used for |
|------|---------|---------|
| Docker + Docker Compose | 24+ | Running both test servers |
| Python | 3.13+ | pytest API test suite |
| Node.js + npm | 20+ | Playwright UI test suite |
| make | any | Convenience targets |

---

## All Commands

### API System (Custom Django — port 8001)

```bash
make api          # start server + install deps + run full pytest suite
make api-start    # start server only (waits until healthy)
make api-test     # run pytest (server must be up)
make api-down     # stop containers

# Run from automation/api/ for granular control:
pytest tests/ -v
pytest tests/ -m smoke                   # critical path only
pytest tests/ -m "negative or boundary"  # edge cases
pytest tests/test_bom.py -v              # single file
pytest tests/ -n auto                    # parallel (pytest-xdist)
```

**Test markers:**

| Marker | Description |
|--------|-------------|
| `smoke` | Critical path (~10 tests) |
| `positive` | Happy-path cases |
| `negative` | Expected failure cases |
| `boundary` | Edge and limit cases |
| `auth` | Authentication / authorization |
| `schema` | Response schema validation |
| `business` | Domain business rule enforcement |

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8001` | API server URL |
| `TEST_USER` | `admin` | Superuser username |
| `TEST_PASSWORD` | `admin` | Superuser password |

---

### UI System (Real InvenTree — port 8000)

```bash
make ui           # start InvenTree + install deps + run full Playwright suite
make ui-start     # start InvenTree only (waits until healthy)
make ui-test      # run Playwright (InvenTree must be up)
make ui-down      # stop containers
make report       # open HTML report from last run

# Run from automation/ui/ for granular control:
npm test                    # full suite
npm run test:headed         # visible browser window
npm run test:debug          # Playwright Inspector
npm run test:create         # Part Creation (PC-001–005, E2E-001)
npm run test:tabs           # Part Detail Tabs (DV-001–011)
npm run test:types          # Part Types (PT-001–007)
npm run test:status         # Part Status (ST-001–004)
npm run test:categories     # Categories (CAT-001–005 + hierarchy)
npm run test:revisions      # Revisions (REV-001–004)
npm run report              # open HTML report
```

**Key Playwright config:**
- `baseURL`: `http://localhost:8000`
- `workers`: 1 (sequential — tests share live InvenTree state)
- `retries`: 1 (trace + screenshot + video on failure)
- Auth: session stored in `playwright/.auth/user.json`

---

## Project Structure

```
project/
├── Makefile                              ← make api / make ui / make help
├── README.md
├── agents/
│   ├── prompts.md                        ← All prompts used with the AI agent
│   └── system-instructions.md           ← Agent context and behavioural rules
├── test-cases/
│   ├── api-manual-tests.md              ← 131 API manual test cases
│   └── ui-manual-tests.md              ← 101 UI manual test cases
└── automation/
    ├── api/                             ← Custom Django REST API + pytest suite
    │   ├── docker-compose.yml           ← Exposes API on host port 8001
    │   ├── Dockerfile
    │   ├── entrypoint.sh
    │   ├── requirements.txt
    │   ├── requirements-test.txt
    │   ├── pytest.ini
    │   ├── manage.py
    │   ├── config/                      ← Django settings, URLs, WSGI
    │   ├── backend/                     ← Django app (models, views, serializers)
    │   └── tests/
    │       ├── conftest.py              ← Fixtures, factories, health check
    │       ├── helpers/
    │       │   ├── api_client.py        ← Thin requests.Session wrapper
    │       │   ├── schemas.py           ← jsonschema definitions
    │       │   └── assertions.py        ← Reusable assertion helpers
    │       ├── test_category.py         ← 24 tests
    │       ├── test_part.py             ← 33 tests
    │       ├── test_revisions.py        ← 16 tests
    │       ├── test_bom.py              ← 23 tests
    │       ├── test_stock.py            ← 24 tests
    │       ├── test_auth.py             ← 3 parametrized tests
    │       ├── test_filtering_pagination.py  ← 14 tests
    │       └── test_error_format.py     ← 14 tests
    └── ui/                              ← Playwright UI automation (Phase 3)
        ├── docker-compose.yml           ← Real InvenTree on host port 8000
        ├── package.json
        ├── tsconfig.json
        ├── playwright.config.ts
        ├── helpers/
        │   ├── auth.setup.ts            ← Session auth via React login form
        │   ├── navigation.ts            ← URL constants + navigate helpers
        │   └── part.helpers.ts          ← API factories for setup/teardown
        ├── page-objects/
        │   ├── PartsPage.ts
        │   ├── CreatePartModal.ts
        │   ├── PartDetailPage.ts
        │   └── CategoryPage.ts
        └── tests/
            ├── parts/
            │   ├── create-part.spec.ts        ← PC-001–005 + E2E-001 (6 tests)
            │   ├── part-detail-tabs.spec.ts   ← DV-001–011 (11 tests)
            │   ├── part-types.spec.ts         ← PT-001–007 (7 tests)
            │   └── part-status.spec.ts        ← ST-001–004 (4 tests)
            ├── categories/
            │   ├── category-crud.spec.ts      ← CAT-001–005 (5 tests)
            │   └── category-hierarchy.spec.ts ← CAT-002h/b, CAT-003h (3 tests)
            └── revisions/
                └── part-revisions.spec.ts     ← REV-001–004 (4 tests)
```

---

## Test Coverage

| Area | Manual cases | Automated |
|------|:-----------:|:---------:|
| PartCategory CRUD | 24 | 24 pytest |
| Part CRUD | 33 | 33 pytest |
| Part Revisions | 16 | 16 pytest + 4 Playwright |
| BOM | 23 | 23 pytest |
| StockItem | 24 | 24 pytest |
| Auth / Authz | 4 | 3 pytest (parametrized) |
| Pagination & Filtering | 12 | 14 pytest |
| Error Format | 8 | 14 pytest |
| Part Creation (UI) | 6 | 6 Playwright |
| Part Detail Tabs (UI) | 11 | 11 Playwright |
| Part Types (UI) | 7 | 7 Playwright |
| Part Status (UI) | 4 | 4 Playwright |
| Categories (UI) | 8 | 8 Playwright |
| **Total** | **131 API + 101 UI** | **181 pytest + 41 Playwright** |

---

## Tool Selection

| Tool | Purpose | Why |
|------|---------|-----|
| **Claude Code** (claude-sonnet-4-6) | Primary AI agent | Agentic CLI with full file-system access — reads source code, infers business rules, generates grounded tests, executes multi-step plans |
| **pytest + requests** | API test runner + HTTP client | Full programmatic control: parametrized tests, data factories, BFS cycle detection. Pure external black-box — zero ORM access |
| **Faker** | Realistic unique test data | Prevents name collisions across parallel test runs |
| **jsonschema** | Response schema validation | Detects unexpected field additions or type changes |
| **Playwright + TypeScript** | UI automation | First-class TypeScript, auto-wait, trace/screenshot/video on failure, Page Object Model |
| **Docker Compose** | Server isolation | Both systems are reproducible, stateless, and port-isolated |
| **Makefile** | Developer experience | Single command to bootstrap + run either system |

---

## Agent Workflow

### Phase 1 — Analysis & Planning
Claude Code read `CLAUDE.md` and the full codebase, then produced a detailed multi-phase implementation plan covering all deliverables.

### Phase 2 — Bug Detection & Fix
Auto-detected a critical naming mismatch: the Django app directory was named `src/` but `apps.py` declared `name = 'backend'`. Fixed by renaming `src/ → backend/`, unblocking the Docker build.

### Phase 3 — Test Case Generation
Generated API and UI manual test cases by:
- Reading all serializer validation logic to identify business rules
- Reading the custom exception handler for error format requirements
- Mapping model field constraints (`max_length`, `decimal_places`, `null`) to boundary tests

### Phase 4 — Automation Code Generation
Generated the complete pytest + Playwright suites by:
- Designing the `conftest.py` fixture hierarchy (session → function scope with automatic cleanup)
- Implementing BOM cycle detection (direct A→B→A and transitive A→B→C→A)
- Parametrizing boolean flags, quantity values, and ordering fields
- Integrating Page Object Model with API-backed setup/teardown for test isolation

---

## Notes on Agent Output

| Item | What happened |
|------|--------------|
| App naming mismatch | Auto-detected and fixed. `src/` → `backend/` rename was the prerequisite for Docker to start |
| PostgreSQL binding conflict | Port 5432 was already in use locally — removed host port binding, kept internal Docker network access |
| Python 3.9 compatibility | Generated `str \| None` union syntax; fixed by adding `from __future__ import annotations` + `Optional[T]` |
| Context processor typo | `auth.context_processors.request` → `auth.context_processors.auth` in `settings.py` |
| Category filter conflict | `DjangoFilterBackend` and manual `get_queryset` conflicted on `?category=` — removed from `filterset_fields`, handled manually |
| InvenTree URL prefix | Tests written for `/ui/` prefix; stable image uses `/web/` — updated all URLs in `navigation.ts` and `auth.setup.ts` |
| Port conflict (api vs ui) | Both wanted `:8000` — custom API moved to host port `:8001`; `BASE_URL` default updated in `conftest.py` |
| InvenTree startup command | `invoke server` not available in stable image — removed `command:` override, used `INVENTREE_AUTO_UPDATE: "true"` |
