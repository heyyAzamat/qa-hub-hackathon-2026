# InvenTree UI Automation — Playwright / TypeScript

End-to-end UI tests for the **InvenTree Parts module**, written with
[Playwright](https://playwright.dev/) and TypeScript.

---

## Overview

These tests exercise the InvenTree Platform UI (React SPA served under `/ui/`)
against a live, locally-running InvenTree instance. They cover the full
lifecycle of parts and categories:

- Creating, searching, and viewing parts
- Part type flags (Assembly, Template, Trackable, etc.) and their effect on the
  detail page layout
- Part status transitions (Active ↔ Inactive) and downstream enforcement
  (inactive parts blocked from BOM selection)
- Part revisions — creating, listing, and constraint enforcement
- Category CRUD and hierarchy (breadcrumbs, parent/child relationships, filter
  by category)

**Why UI tests here?**  
The InvenTree REST API is covered by server-side tests. These tests exist to
catch regressions in the React frontend — routing, tab visibility rules,
form validation, dialog flows — that API tests cannot detect.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Node.js | ≥ 20 |
| npm | ≥ 10 (bundled with Node 20) |
| Docker Desktop | Latest stable |
| InvenTree | Running locally on `http://localhost:8000` |

### Start InvenTree

From the repo root:

```bash
cd InvenTree/.devcontainer
docker compose up -d
```

Wait until the `inventree` container is healthy before running tests.
The default admin credentials expected by the test suite are:

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `inventree` |

If your instance uses different credentials, update `helpers/auth.setup.ts`.

---

## Installation

```bash
# 1. Install Node dependencies
cd automation/ui
npm install

# 2. Install the Chromium browser binary Playwright will drive
npm run install:browsers
```

The second command is equivalent to `npx playwright install chromium --with-deps`
and only needs to be run once (or when the Playwright version changes).

---

## Configuration

All Playwright settings live in [`playwright.config.ts`](playwright.config.ts).

### `baseURL`

```ts
use: {
  baseURL: 'http://localhost:8000',
}
```

To run against a different host without editing the file, add an environment
variable override to the config:

```ts
// playwright.config.ts
baseURL: process.env.BASE_URL ?? 'http://localhost:8000',
```

Then pass it at runtime:

```bash
BASE_URL=http://staging.example.com npx playwright test
```

### Authentication — `storageState`

Authentication uses a **two-project pipeline**:

1. The `setup` project runs `helpers/auth.setup.ts` **once** before any spec.
   It navigates to Django's `/accounts/login/` form, fills in the admin
   credentials, and persists the resulting session cookie to
   `playwright/.auth/user.json`.

2. The `chromium` project declares `dependencies: ['setup']` and loads that
   file via `storageState: 'playwright/.auth/user.json'`.

Every test therefore starts already authenticated — no spec needs to handle
login itself. The auth file is gitignored; Playwright regenerates it on each
run.

### Other notable options

| Option | Value | Effect |
|---|---|---|
| `fullyParallel` | `false` | Tests run sequentially (shared live DB) |
| `workers` | `1` | Enforces sequential execution |
| `retries` | `1` | One automatic retry on CI |
| `trace` | `on-first-retry` | Trace captured on retry for debugging |
| `screenshot` | `only-on-failure` | Screenshot saved when a test fails |
| `video` | `retain-on-failure` | Video kept when a test fails |
| `actionTimeout` | `15 000 ms` | Per-action timeout (generous for Docker) |
| `navigationTimeout` | `30 000 ms` | Per-navigation timeout |

---

## Running Tests

All commands must be run from the `automation/ui/` directory.

```bash
# Run the full suite
npm test
# or
npx playwright test

# Run a single spec file
npx playwright test tests/parts/create-part.spec.ts

# Run all tests in a folder
npx playwright test tests/categories

# Run in headed mode (browser window visible)
npm run test:headed
# or
npx playwright test --headed

# Open the interactive Playwright UI (step-through, time-travel)
npm run test:ui

# Step through a test with the Inspector
npm run test:debug

# Open the HTML report from the last run
npm run report
# or
npx playwright show-report
```

### Convenience scripts (from `package.json`)

| Script | Runs |
|---|---|
| `npm run test:create` | `tests/parts/create-part.spec.ts` |
| `npm run test:tabs` | `tests/parts/part-detail-tabs.spec.ts` |
| `npm run test:types` | `tests/parts/part-types.spec.ts` |
| `npm run test:status` | `tests/parts/part-status.spec.ts` |
| `npm run test:categories` | `tests/categories/` (both files) |
| `npm run test:revisions` | `tests/revisions/` |

---

## Project Structure

```
automation/ui/
│
├── helpers/
│   ├── auth.setup.ts       # One-time login; writes playwright/.auth/user.json.
│   │                       # Runs as the "setup" Playwright project before specs.
│   ├── navigation.ts       # URL constants + goto helpers.
│   │                       # Replaces waitForLoadState('networkidle') with
│   │                       # Promise.all([waitForResponse(...), goto(...)]) so
│   │                       # navigation implicitly asserts HTTP 200 from the API.
│   └── part.helpers.ts     # Typed REST API wrappers (createPartApi,
│                           # deletePartApi, etc.) used for fast setup/teardown.
│                           # Also exports uniqueName() to prevent name collisions.
│
├── page-objects/
│   ├── CategoryPage.ts     # Category detail page: breadcrumb assertions,
│   │                       # parts/sub-category list, New/Edit/Delete dialogs.
│   ├── CreatePartModal.ts  # Create Part modal: field setters, flag checkboxes,
│   │                       # submit, and validation error assertions.
│   ├── PartDetailPage.ts   # Part detail page: tab navigation, status badges,
│   │                       # type badges, setActive/setInactive via Edit dialog,
│   │                       # revision helpers, parameter helpers, BOM helpers.
│   └── PartsPage.ts        # Parts list: navigate, open New Part modal,
│                           # search with waitForResponse, list assertions.
│
├── tests/
│   ├── categories/
│   │   ├── category-crud.spec.ts       # CAT-001 – CAT-005
│   │   └── category-hierarchy.spec.ts  # CAT-002h, CAT-002b, CAT-003h
│   ├── parts/
│   │   ├── create-part.spec.ts         # PC-001 – PC-005, E2E-001
│   │   ├── part-detail-tabs.spec.ts    # DV-001 – DV-011
│   │   ├── part-status.spec.ts         # ST-001 – ST-004
│   │   └── part-types.spec.ts          # PT-001 – PT-007
│   └── revisions/
│       └── part-revisions.spec.ts      # REV-001 – REV-004
│
├── playwright/.auth/
│   └── user.json           # Generated at runtime; gitignored.
│
├── playwright-report/      # HTML report output; gitignored.
├── test-results/           # Traces, screenshots, videos; gitignored.
├── playwright.config.ts
└── package.json
```

---

## Test Coverage Summary

| Spec file | IDs | What is covered |
|---|---|---|
| `parts/create-part.spec.ts` | PC-001 – PC-005, E2E-001 | Create part (required fields only; all optional fields); part appears in list; empty-name validation error; duplicate IPN server error; full E2E flow (create → add parameter → verify in category view) |
| `parts/part-detail-tabs.spec.ts` | DV-001 – DV-011 | Every tab on the part detail page renders; BOM tab absent for non-Assembly parts; Variants tab absent for non-Template parts; Test Templates tab absent for non-Trackable parts |
| `parts/part-status.spec.ts` | ST-001 – ST-004 | Active → Inactive transition; Inactive badge persists after reload; Inactive part excluded from BOM item picker; Inactive → Active reactivation |
| `parts/part-types.spec.ts` | PT-001 – PT-007 | Each part type flag (Virtual, Template, Assembly, Component, Trackable, Purchaseable, Saleable) produces the correct badge on the detail page; Assembly and Template flags surface their respective extra tabs |
| `categories/category-crud.spec.ts` | CAT-001 – CAT-005 | Create root category via UI; edit category name; assign part to a different category; delete empty category (verified via API 404); deleting a non-empty category is blocked or warned |
| `categories/category-hierarchy.spec.ts` | CAT-002h, CAT-002b, CAT-003h | Create child under parent via UI; breadcrumb shows parent → child path; parts list filtered to child category |
| `revisions/part-revisions.spec.ts` | REV-001 – REV-004 | Create revision via Revisions tab; revision appears in tab list; duplicate revision code rejected; creating a revision-of-a-revision is blocked |

---

## Known Limitations

**Selector fragility — Mantine Breadcrumbs**  
`CategoryPage.expectBreadcrumbContains()` targets `[aria-label="breadcrumb"]`.
If InvenTree's layout omits that ARIA attribute, the assertion will fail silently
or time out. Fix: add `data-testid="breadcrumb"` to the breadcrumb component
and update the locator accordingly.

**Selector fragility — form validation errors**  
`CreatePartModal.expectValidationErrors()` relies on `[aria-invalid="true"]` and
`[data-error]`. Mantine's class-based error indicator (`[class*="error"]`) was
intentionally excluded because class names are minified in production builds.
If both attributes are absent in your InvenTree build, add `data-testid="field-error"`
to the error text element.

**Mantine Select portal**  
InvenTree renders Mantine `<Select>` option lists in a React portal **outside**
the dialog DOM subtree. Locators for dropdown options therefore use `page`
(the full document) rather than `dialog`. If Mantine changes this rendering
strategy, all category and template autocomplete interactions will break.

**Sequential execution only**  
`workers: 1` is intentional — all tests share one live InvenTree instance with
a real database, so parallel runs would cause data collisions. If you add a
separate test database per worker, you can raise `workers` and enable
`fullyParallel: true`.

**Revision tab behaviour is version-dependent**  
`REV-004` asserts that the "Add Revision" button is absent or disabled on a
revision part. The exact enforcement mechanism (button hidden vs. disabled)
may differ across InvenTree releases. The page object handles both cases, but
verify against your deployed version if this test is flaky.

**`networkidle` removed — response filter must match**  
Navigation helpers wait for the first `/api/part/…` response with status 200
instead of `waitForLoadState('networkidle')`. If InvenTree makes an API call to
a different path before the parts endpoint responds, the `Promise.all` will
resolve on that earlier response and the page may not be fully rendered.
Tighten the URL filter in `navigation.ts` if you observe premature resolution.

**Credentials are hardcoded**  
`auth.setup.ts` and `part.helpers.ts` use `admin` / `inventree`. These match
the defaults for InvenTree's Docker dev image. Override them with environment
variables if your instance differs (no env-var support is wired in yet — a
future improvement).
