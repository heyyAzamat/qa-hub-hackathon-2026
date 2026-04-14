# Agent Prompts — QA Hub Hackathon 2026

## Prompt 1 — Project Analysis & Planning

**User instruction**:
> Проанализируй CLAUDE.md и проанализируй проект и составь план по следующим действиям, за исключением фронтенда в UI (его добавлю в последнюю очередь а затем подключу).

**Agent approach**:
1. Read `CLAUDE.md` (full technical specification in Russian)
2. Launched Explore subagent to scan the entire project structure
3. Read critical backend files: `settings.py`, `models.py`, `serializers.py`, `views.py`, `exception_handlers.py`, `apps.py`
4. Launched Plan subagent to design the API test suite structure
5. Wrote final plan to `/Users/pavel/.claude/plans/misty-imagining-pumpkin.md`

**Key findings from exploration**:
- Django app naming mismatch: directory `src/` but `apps.py` declares `name = 'backend'` and `settings.py` installs `'backend'`
- 4 models: Part, PartCategory, BomItem, StockItem
- Custom serializer validation: IPN uniqueness, revision constraints, BOM cycle detection (BFS), template stock restriction
- Custom exception handler: unified `{"error_code", "message", "details"}` format
- Empty placeholders: `prompts.md`, `system-instructions.md`, `ui-manual-tests.md`, `api-manual-tests.md`, `README.md`

---

## Prompt 2 — Fix Backend Structure

**User instruction**: Approved the plan; implementation began.

**Agent action**:
```bash
mv project/automation/api/src project/automation/api/backend
```

**Why**: `apps.py` declares `name = 'backend'`, `settings.py` references `backend.*` in `INSTALLED_APPS`, `MIDDLEWARE`, `REST_FRAMEWORK` exception handler. Without renaming, Django cannot start.

---

## Prompt 3 — API Manual Test Cases

**Agent prompt to itself** (internal planning):
> Generate comprehensive API manual test cases for all 4 ViewSets (PartCategory, Part, BomItem, StockItem) plus revision endpoints. Cover CRUD, filtering, pagination, search, field validation, business rules, and error format. Use Markdown tables with columns: ID | Title | Method | Endpoint | Preconditions | Input Body | Expected Status | Expected Response | Category.

**Generated file**: `project/test-cases/api-manual-tests.md`  
**Output**: 131 test cases across 8 sections

**Key decisions**:
- Test IDs prefixed by resource: CAT-xxx, PART-xxx, REV-xxx, BOM-xxx, STK-xxx, PAG-xxx, FV-xxx, ERR-xxx
- BOM cycle detection tested as both direct (A→B, B→A) and transitive (A→B→C, C→A)
- Documented REV-010 (revision of revision) as Edge Case — no explicit block in views
- `INTEGRITY_ERROR` vs `BAD_REQUEST` for duplicate BOM pair noted (depends on which layer catches it first)

---

## Prompt 4 — UI Manual Test Cases

**Agent prompt to itself**:
> Generate 100 UI manual test cases for the InvenTree Parts module based on CLAUDE.md requirements. Cover: Part Creation (manual + import), Part Detail View (all tabs), Categories, Attributes, Types, Units, Revisions. Include cross-functional test. Based on docs.inventree.org/en/stable/part/ (documentation returned 403 — used CLAUDE.md spec and domain knowledge instead).

**Generated file**: `project/test-cases/ui-manual-tests.md`  
**Output**: 101 test cases across 17 sections

**Note on documentation access**: InvenTree docs returned HTTP 403 during generation. Test cases were written based on:
1. Requirements listed in `CLAUDE.md` (comprehensive spec in Russian)
2. Domain knowledge of InvenTree's Parts module architecture
3. Backend code analysis (model flags, serializer validations)

---

## Prompt 5 — API Test Infrastructure

**Agent prompt to itself**:
> Create the test infrastructure for pytest + requests API test suite:
> - `requirements-test.txt` with pytest, requests, Faker, jsonschema, python-dotenv
> - `pytest.ini` with markers (smoke, positive, negative, boundary, auth, schema, business)  
> - `tests/conftest.py` with session-scoped auth_client, anon_client, base_url; function-scoped factories (category_factory, part_factory, bom_item_factory, stock_item_factory); convenience fixtures (assembly_part, component_part, template_part, inactive_part); autouse health check
> - `tests/helpers/api_client.py` — thin requests.Session wrapper
> - `tests/helpers/schemas.py` — JSON Schema dicts for all resources
> - `tests/helpers/assertions.py` — reusable assertion functions

**Generated files**: 6 infrastructure files  
**Key design decisions**:
- `check_server_health` is `autouse=True, scope="session"` → entire run is skipped with a clear message if server is down
- Factories use `fake.unique.*` for collision-free test data
- Cleanup in reverse insertion order (children before parents for categories)
- `APIClient` returns raw `Response` — keeps assertions explicit in test files

---

## Prompt 6 — API Automation Test Files

**Agent prompt to itself**:
> Generate 8 test files covering all API test cases from api-manual-tests.md. Use conftest.py fixtures, helpers/assertions.py, helpers/schemas.py. Apply pytest markers. Cover: CRUD, filtering, pagination, business rules, auth, error format.

**Generated files**:

| File | Cases | Key patterns |
|------|-------|--------------|
| `test_category.py` | 24 tests | Tree structure, circular parent validation |
| `test_part.py` | 33 tests | Flag parametrize, IPN uniqueness, cascade rules |
| `test_revisions.py` | 16 tests | Revision inheritance, code uniqueness per-parent |
| `test_bom.py` | 23 tests | Direct + transitive cycle detection, quantity parametrize |
| `test_stock.py` | 24 tests | Template restriction, decimal quantity parametrize |
| `test_auth.py` | 3 tests | Parametrized write endpoints, anonymous read |
| `test_filtering_pagination.py` | 14 tests | Page size, ordering correctness, child categories |
| `test_error_format.py` | 14 tests | error_code/message/details format, Content-Type |

**Total**: ~151 automated test cases

---

## Prompt 7 — Agent Artifacts & README

**Agent action**: Generated `system-instructions.md`, `prompts.md` (this file), `README.md`.

---

## Observations & Corrections Made

| Issue | Discovered | Action |
|-------|-----------|--------|
| App naming mismatch (`src/` vs `backend`) | Code exploration | Renamed `src/` → `backend/` |
| InvenTree docs return 403 | WebFetch call | UI tests written from CLAUDE.md spec + domain knowledge |
| REV-010: no explicit block for revision-of-revision | Reading views.py | Documented as edge case, test documents actual behavior |
| BOM-016: duplicate pair may be INTEGRITY_ERROR or BAD_REQUEST | Reading middleware/serializer | Test accepts both error codes |
| `description` required despite `blank=True, null=True` on model | Reading serializer validate() | All part_factory calls include description; dedicated negative tests cover this |
