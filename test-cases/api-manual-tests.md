# API Manual Test Cases — InvenTree Parts Module

**Приложение**: InvenTree Parts API (custom Django/DRF)  
**Базовый URL**: `http://localhost:8000`  
**Аутентификация**: HTTP Basic Auth (`admin` / `admin`) для write-операций  
**Формат ошибок**: `{"error_code": "...", "message": "...", "details": {...}}`  

---

## Содержание

1. [PartCategory CRUD](#1-partcategory-crud)
2. [Part CRUD](#2-part-crud)
3. [Part Revisions](#3-part-revisions)
4. [BOM (Bill of Materials)](#4-bom-bill-of-materials)
5. [StockItem](#5-stockitem)
6. [Pagination & Filtering](#6-pagination--filtering)
7. [Field Validation](#7-field-validation)
8. [Error Format](#8-error-format)

---

## 1. PartCategory CRUD

| ID | Title | Method | Endpoint | Preconditions | Input Body | Expected Status | Expected Response | Category |
|----|-------|--------|----------|---------------|------------|-----------------|-------------------|----------|
| CAT-001 | Get list of categories (empty) | GET | `/api/part/category/` | Нет категорий | — | 200 | `{"count": 0, "next": null, "previous": null, "results": []}` | Positive |
| CAT-002 | Get list of categories (populated) | GET | `/api/part/category/` | Существует ≥1 категория | — | 200 | Поле `results` — массив объектов с полями `id`, `name`, `description`, `parent`, `children`, `part_count` | Positive |
| CAT-003 | Create root category | POST | `/api/part/category/` | Auth | `{"name": "Electronics", "description": "Electronic components"}` | 201 | Объект с `id` (int), `name="Electronics"`, `parent=null`, `children=[]`, `part_count=0` | Positive |
| CAT-004 | Create child category | POST | `/api/part/category/` | Существует родительская категория с `id=1`; Auth | `{"name": "Resistors", "description": "Resistors", "parent": 1}` | 201 | Объект с `parent=1` | Positive |
| CAT-005 | Get category by ID | GET | `/api/part/category/{id}/` | Категория существует | — | 200 | Объект категории с корректными полями | Positive |
| CAT-006 | Full update category (PUT) | PUT | `/api/part/category/{id}/` | Категория существует; Auth | `{"name": "Updated Name", "description": "Updated desc", "parent": null}` | 200 | Все поля обновлены | Positive |
| CAT-007 | Partial update category (PATCH) | PATCH | `/api/part/category/{id}/` | Категория существует; Auth | `{"name": "New Name"}` | 200 | Только `name` изменён, остальные поля прежние | Positive |
| CAT-008 | Delete category | DELETE | `/api/part/category/{id}/` | Категория существует без дочерних; Auth | — | 204 | Пустое тело | Positive |
| CAT-009 | Get after delete | GET | `/api/part/category/{id}/` | Категория удалена | — | 404 | `{"error_code": "NOT_FOUND", "message": "..."}` | Positive |
| CAT-010 | Get root categories | GET | `/api/part/category/root/` | Есть корневые и дочерние категории | — | 200 | Все объекты в `results` имеют `parent=null` | Positive |
| CAT-011 | Get category tree | GET | `/api/part/category/tree/` | Есть многоуровневые категории | — | 200 | Массив корневых узлов; каждый имеет поле `children` (массив); поля: `id`, `name`, `parent`, `children` | Positive |
| CAT-012 | Filter by parent | GET | `/api/part/category/?parent={id}` | Есть родитель с дочерними | — | 200 | Только категории с `parent={id}` | Positive |
| CAT-013 | Search by name | GET | `/api/part/category/?search=Elec` | Категория "Electronics" существует | — | 200 | `results` содержит "Electronics" | Positive |
| CAT-014 | Order by name descending | GET | `/api/part/category/?ordering=-name` | ≥2 категории | — | 200 | `results[0].name` >= `results[1].name` (лексикографически) | Positive |
| CAT-015 | part_count annotation | GET | `/api/part/category/{id}/` | 2 детали привязаны к категории `{id}` | — | 200 | `part_count=2` | Positive |
| CAT-016 | Create without name | POST | `/api/part/category/` | Auth | `{"description": "No name"}` | 400 | `error_code=BAD_REQUEST`, `details.name` содержит ошибку | Negative |
| CAT-017 | Create with name > 100 chars | POST | `/api/part/category/` | Auth | `{"name": "A" * 101}` | 400 | `error_code=BAD_REQUEST` | Negative |
| CAT-018 | Set parent to self (circular) | PATCH | `/api/part/category/{id}/` | Категория существует; Auth | `{"parent": {id}}` | 400 | `error_code=BAD_REQUEST`, `details.parent` о цикле | Negative |
| CAT-019 | Set parent to descendant (indirect circular) | PATCH | `/api/part/category/{grandparent_id}/` | Цепочка A→B→C; пытаемся C→A как parent A | `{"parent": {child_id}}` | 400 | `error_code=BAD_REQUEST`, сообщение о циклической зависимости | Negative |
| CAT-020 | Get non-existent category | GET | `/api/part/category/999999/` | — | — | 404 | `error_code=NOT_FOUND` | Negative |
| CAT-021 | Delete without auth | DELETE | `/api/part/category/{id}/` | Категория существует; без аутентификации | — | 403 | `error_code=FORBIDDEN` | Negative |
| CAT-022 | Create with name exactly 100 chars | POST | `/api/part/category/` | Auth | `{"name": "A" * 100, "description": "ok"}` | 201 | Создана успешно | Boundary |
| CAT-023 | Create with name exactly 101 chars | POST | `/api/part/category/` | Auth | `{"name": "A" * 101, "description": "ok"}` | 400 | `error_code=BAD_REQUEST` | Boundary |
| CAT-024 | Root endpoint when no categories | GET | `/api/part/category/root/` | Нет ни одной категории | — | 200 | `count=0`, `results=[]` | Boundary |

---

## 2. Part CRUD

| ID | Title | Method | Endpoint | Preconditions | Input Body | Expected Status | Expected Response | Category |
|----|-------|--------|----------|---------------|------------|-----------------|-------------------|----------|
| PART-001 | Get list of parts (empty) | GET | `/api/part/` | Нет деталей | — | 200 | `{"count": 0, "results": []}` | Positive |
| PART-002 | Create minimal part | POST | `/api/part/` | Auth | `{"name": "Resistor 10k", "description": "10k ohm resistor"}` | 201 | Объект с `id`, `name`, `description`, `active=true`, `virtual=false`, `template=false`, `assembly=false`, `component=true`, `IPN=null`, `parameters=[]`, `stock_count=null`, `bom_count=0` | Positive |
| PART-003 | Create part with IPN | POST | `/api/part/` | Auth | `{"name": "Cap 100uF", "description": "100uF capacitor", "IPN": "CAP-100UF-001"}` | 201 | `IPN="CAP-100UF-001"` в ответе | Positive |
| PART-004 | Create part with category | POST | `/api/part/` | Категория id=1; Auth | `{"name": "LED Red", "description": "Red LED", "category_id": 1}` | 201 | `category.id=1`, `category.name` корректно | Positive |
| PART-005 | Create part with all flags | POST | `/api/part/` | Auth | `{"name": "PCB Assembly", "description": "Main PCB", "active": true, "virtual": false, "template": false, "assembly": true, "component": false}` | 201 | Все флаги отражены в ответе | Positive |
| PART-006 | Get part by ID | GET | `/api/part/{id}/` | Деталь существует | — | 200 | Объект с полями `id`, `name`, `description`, `IPN`, `active`, `virtual`, `template`, `assembly`, `component`, `category`, `revision_of`, `revision`, `creation_date`, `parameters`, `stock_count`, `bom_count` | Positive |
| PART-007 | Full update part (PUT) | PUT | `/api/part/{id}/` | Деталь существует; Auth | `{"name": "New Name", "description": "New desc", "active": true, "virtual": false, "template": false, "assembly": false, "component": true}` | 200 | Все поля обновлены | Positive |
| PART-008 | Partial update (PATCH) active flag | PATCH | `/api/part/{id}/` | Активная деталь без дочерних ревизий; Auth | `{"active": false}` | 200 | `active=false` в ответе | Positive |
| PART-009 | Delete part | DELETE | `/api/part/{id}/` | Деталь без зависимостей; Auth | — | 204 | Пустое тело | Positive |
| PART-010 | Filter by active=true | GET | `/api/part/?active=true` | Есть активные и неактивные | — | 200 | Все `results[].active=true` | Positive |
| PART-011 | Filter by active=false | GET | `/api/part/?active=false` | Есть неактивная деталь | — | 200 | Все `results[].active=false` | Positive |
| PART-012 | Filter by category | GET | `/api/part/?category={id}` | Детали привязаны к категории | — | 200 | Все `results[].category.id={id}` | Positive |
| PART-013 | Filter with include_child_categories | GET | `/api/part/?category={parent_id}&include_child_categories=true` | Детали в дочерних категориях | — | 200 | Детали из родительской и всех дочерних категорий | Positive |
| PART-014 | Search by name | GET | `/api/part/?search=Resistor` | Деталь "Resistor 10k" существует | — | 200 | `results` содержит "Resistor 10k" | Positive |
| PART-015 | Search by IPN | GET | `/api/part/?search=CAP-100` | Деталь с IPN=CAP-100UF-001 | — | 200 | `results` содержит деталь | Positive |
| PART-016 | Order by creation_date | GET | `/api/part/?ordering=-creation_date` | ≥2 детали | — | 200 | Первая деталь создана позже второй | Positive |
| PART-017 | Create without name | POST | `/api/part/` | Auth | `{"description": "No name"}` | 400 | `error_code=BAD_REQUEST`, `details.name` | Negative |
| PART-018 | Create without description | POST | `/api/part/` | Auth | `{"name": "Part without desc"}` | 400 | `error_code=BAD_REQUEST`, `details.description` | Negative |
| PART-019 | Create with whitespace-only name | POST | `/api/part/` | Auth | `{"name": "   ", "description": "ok"}` | 400 | `error_code=BAD_REQUEST`, ошибка в поле `name` | Negative |
| PART-020 | Create with whitespace-only description | POST | `/api/part/` | Auth | `{"name": "Part", "description": "\t\n"}` | 400 | `error_code=BAD_REQUEST`, ошибка в поле `description` | Negative |
| PART-021 | Create with duplicate IPN | POST | `/api/part/` | Деталь с IPN="DUPE-001" существует; Auth | `{"name": "Part2", "description": "desc", "IPN": "DUPE-001"}` | 400 | `error_code=BAD_REQUEST`, сообщение об уникальности IPN | Negative |
| PART-022 | Deactivate part with active revisions | PATCH | `/api/part/{id}/` | Деталь имеет активную дочернюю ревизию; Auth | `{"active": false}` | 400 | `error_code=BAD_REQUEST`, сообщение о дочерних ревизиях | Negative |
| PART-023 | Remove assembly flag with BOM items | PATCH | `/api/part/{id}/` | assembly=True деталь с BOM items; Auth | `{"assembly": false}` | 400 | `error_code=BAD_REQUEST`, сообщение об BOM items | Negative |
| PART-024 | Create with non-existent category_id | POST | `/api/part/` | Auth | `{"name": "Part", "description": "desc", "category_id": 999999}` | 400 | `error_code=BAD_REQUEST` | Negative |
| PART-025 | Get non-existent part | GET | `/api/part/999999/` | — | — | 404 | `error_code=NOT_FOUND` | Negative |
| PART-026 | Post without auth | POST | `/api/part/` | Без аутентификации | `{"name": "Part", "description": "desc"}` | 403 | `error_code=FORBIDDEN` | Negative |
| PART-027 | Create with IPN exactly 50 chars | POST | `/api/part/` | Auth | `{"name": "Part", "description": "desc", "IPN": "A" * 50}` | 201 | Деталь создана, `IPN` = 50 символов | Boundary |
| PART-028 | Create with IPN 51 chars | POST | `/api/part/` | Auth | `{"name": "Part", "description": "desc", "IPN": "A" * 51}` | 400 | `error_code=BAD_REQUEST` | Boundary |
| PART-029 | Create with name exactly 200 chars | POST | `/api/part/` | Auth | `{"name": "A" * 200, "description": "desc"}` | 201 | Деталь создана | Boundary |
| PART-030 | Create with name 201 chars | POST | `/api/part/` | Auth | `{"name": "A" * 201, "description": "desc"}` | 400 | `error_code=BAD_REQUEST` | Boundary |
| PART-031 | Two parts with IPN=null | POST | `/api/part/` ×2 | Auth | Два POST без IPN | 201 (оба) | Оба создаются (null не нарушает unique constraint) | Boundary |
| PART-032 | Update IPN to existing IPN of another part | PATCH | `/api/part/{id}/` | Другая деталь имеет IPN="TAKEN"; Auth | `{"IPN": "TAKEN"}` | 400 | Ошибка уникальности IPN | Boundary |
| PART-033 | Update IPN to same value (idempotent) | PATCH | `/api/part/{id}/` | Деталь имеет IPN="SAME"; Auth | `{"IPN": "SAME"}` | 200 | Деталь обновлена без ошибки | Boundary |

---

## 3. Part Revisions

| ID | Title | Method | Endpoint | Preconditions | Input Body | Expected Status | Expected Response | Category |
|----|-------|--------|----------|---------------|------------|-----------------|-------------------|----------|
| REV-001 | Get revisions for part without revisions | GET | `/api/part/{id}/revisions/` | Деталь без ревизий | — | 200 | `{"count": 0, "results": []}` | Positive |
| REV-002 | Create first revision | POST | `/api/part/{id}/create_revision/` | Auth | `{"revision": "B"}` | 201 | Объект с `revision_of={id}`, `revision="B"`, наследует `name`, `description`, `category` от оригинала | Positive |
| REV-003 | Create revision with name override | POST | `/api/part/{id}/create_revision/` | Auth | `{"revision": "C", "name": "Custom Name"}` | 201 | `name="Custom Name"`, `revision="C"` | Positive |
| REV-004 | List revisions after creation | GET | `/api/part/{id}/revisions/` | Создана ревизия "B" | — | 200 | `count=1`, `results[0].revision="B"` | Positive |
| REV-005 | Create multiple revisions | POST | `/api/part/{id}/create_revision/` x3 | Auth | Ревизии "B", "C", "D" | 201 (все) | GET revisions → `count=3` | Positive |
| REV-006 | Delete all revisions (clear) | DELETE | `/api/part/{id}/revisions/clear/` | Auth; 3 ревизии существуют | — | 200 | `{"detail": "Удалено ревизий: 3."}` | Positive |
| REV-007 | Revisions ordered by creation_date desc | GET | `/api/part/{id}/revisions/` | 3 ревизии созданы последовательно | — | 200 | Первая ревизия в `results` — самая новая | Positive |
| REV-008 | Create revision without revision code | POST | `/api/part/{id}/create_revision/` | Auth | `{}` | 400 | `{"revision": "Код ревизии обязателен..."}` | Negative |
| REV-009 | Create duplicate revision code | POST | `/api/part/{id}/create_revision/` | Ревизия "B" уже существует; Auth | `{"revision": "B"}` | 400 | Сообщение о дубликате | Negative |
| REV-010 | Create revision of revision (meta-revision) | POST | `/api/part/{revision_id}/create_revision/` | `revision_id` — это сама ревизия; Auth | `{"revision": "B2"}` | Документировать фактическое поведение | Нет явной блокировки в views — возможный баг | Edge Case |
| REV-011 | Create revision of inactive part | POST | `/api/part/{id}/create_revision/` | Деталь неактивна; Auth | `{"revision": "B"}` | 400 | Ошибка о неактивной детали (validate_revision_of) | Negative |
| REV-012 | Create revision unauthenticated | POST | `/api/part/{id}/create_revision/` | Без аутентификации | `{"revision": "B"}` | 403 | `error_code=FORBIDDEN` | Negative |
| REV-013 | Clear revisions for non-existent part | DELETE | `/api/part/999999/revisions/clear/` | Auth | — | 404 | `error_code=NOT_FOUND` | Negative |
| REV-014 | Revision code exactly 20 chars | POST | `/api/part/{id}/create_revision/` | Auth | `{"revision": "A" * 20}` | 201 | Создана успешно | Boundary |
| REV-015 | Revision code 21 chars | POST | `/api/part/{id}/create_revision/` | Auth | `{"revision": "A" * 21}` | 400 | `error_code=BAD_REQUEST` | Boundary |
| REV-016 | Same revision code on different parents | POST | 2 разных parent | Auth; 2 разные детали | `{"revision": "B"}` оба | 201 (оба) | Ревизии уникальны per-parent | Boundary |

---

## 4. BOM (Bill of Materials)

| ID | Title | Method | Endpoint | Preconditions | Input Body | Expected Status | Expected Response | Category |
|----|-------|--------|----------|---------------|------------|-----------------|-------------------|----------|
| BOM-001 | Get empty BOM list | GET | `/api/part/bom/` | Нет BOM items | — | 200 | `{"count": 0, "results": []}` | Positive |
| BOM-002 | Create BOM item | POST | `/api/part/bom/` | Assembly-деталь id=1 (assembly=True), Component-деталь id=2 (component=True, active=True); Auth | `{"assembly": 1, "sub_part": 2, "quantity": 2}` | 201 | Объект с `id`, `assembly=1`, `sub_part=2`, `assembly_name`, `sub_part_name`, `quantity="2.00000"`, `optional=false` | Positive |
| BOM-003 | Create optional BOM item | POST | `/api/part/bom/` | Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1, "optional": true}` | 201 | `optional=true` | Positive |
| BOM-004 | Create BOM item with note | POST | `/api/part/bom/` | Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1, "note": "Use premium grade"}` | 201 | `note="Use premium grade"` | Positive |
| BOM-005 | Get BOM item by ID | GET | `/api/part/bom/{id}/` | BOM item существует | — | 200 | Объект с read-only полями `assembly_name`, `sub_part_name` | Positive |
| BOM-006 | Update BOM item quantity (PATCH) | PATCH | `/api/part/bom/{id}/` | Auth | `{"quantity": 5.5}` | 200 | `quantity="5.50000"` | Positive |
| BOM-007 | Delete BOM item | DELETE | `/api/part/bom/{id}/` | Auth | — | 204 | — | Positive |
| BOM-008 | Filter by assembly | GET | `/api/part/bom/?assembly={id}` | BOM items существуют | — | 200 | Все `results[].assembly={id}` | Positive |
| BOM-009 | Filter by optional=true | GET | `/api/part/bom/?optional=true` | Optional BOM item существует | — | 200 | Все `results[].optional=true` | Positive |
| BOM-010 | Create with non-assembly parent | POST | `/api/part/bom/` | Part id=1 имеет `assembly=False`; Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1}` | 400 | `error_code=BAD_REQUEST`, `details.assembly` о флаге assembly | Negative |
| BOM-011 | Create with non-component sub_part | POST | `/api/part/bom/` | Part id=2 имеет `component=False`; Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1}` | 400 | `error_code=BAD_REQUEST`, `details.sub_part` о флаге component | Negative |
| BOM-012 | Create with inactive sub_part | POST | `/api/part/bom/` | Part id=2 неактивна; Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1}` | 400 | `error_code=BAD_REQUEST`, `details.sub_part` о деактивации | Negative |
| BOM-013 | Create self-referential BOM | POST | `/api/part/bom/` | Part id=1 assembly=True, component=True; Auth | `{"assembly": 1, "sub_part": 1, "quantity": 1}` | 400 | `error_code=BAD_REQUEST`, деталь не может быть компонентом самой себя | Negative |
| BOM-014 | Direct cycle: A→B then B→A | POST | `/api/part/bom/` | A→B BOM уже существует; Auth | `{"assembly": B_id, "sub_part": A_id, "quantity": 1}` | 400 | `error_code=BAD_REQUEST`, сообщение об обнаружении цикла | Negative |
| BOM-015 | Transitive cycle: A→B, B→C, then C→A | POST | `/api/part/bom/` | A→B, B→C уже существуют; Auth | `{"assembly": C_id, "sub_part": A_id, "quantity": 1}` | 400 | `error_code=BAD_REQUEST`, циклическая зависимость | Negative |
| BOM-016 | Duplicate (assembly, sub_part) pair | POST | `/api/part/bom/` | BOM item A→B уже существует; Auth | `{"assembly": A_id, "sub_part": B_id, "quantity": 3}` | 400 | `error_code=INTEGRITY_ERROR` (unique_together) | Negative |
| BOM-017 | Create with quantity=0 | POST | `/api/part/bom/` | Auth | `{"assembly": 1, "sub_part": 2, "quantity": 0}` | 400 | Ошибка: количество должно быть > 0 | Negative |
| BOM-018 | Create with quantity=-1 | POST | `/api/part/bom/` | Auth | `{"assembly": 1, "sub_part": 2, "quantity": -1}` | 400 | Ошибка: количество должно быть > 0 | Negative |
| BOM-019 | Create unauthenticated | POST | `/api/part/bom/` | Без Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1}` | 403 | `error_code=FORBIDDEN` | Negative |
| BOM-020 | Quantity with 5 decimal places | POST | `/api/part/bom/` | Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1.12345}` | 201 | `quantity="1.12345"` | Boundary |
| BOM-021 | Minimum positive quantity (0.00001) | POST | `/api/part/bom/` | Auth | `{"assembly": 1, "sub_part": 2, "quantity": 0.00001}` | 201 | Создан успешно | Boundary |
| BOM-022 | Quantity with 6 decimal places | POST | `/api/part/bom/` | Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1.123456}` | 400 | Ошибка decimal_places | Boundary |
| BOM-023 | Deep valid chain (A→B→C→D, no cycle) | POST | `/api/part/bom/` x3 | Auth | A→B, B→C, C→D последовательно | 201 (все) | Все BOM items созданы без ошибок | Boundary |

---

## 5. StockItem

| ID | Title | Method | Endpoint | Preconditions | Input Body | Expected Status | Expected Response | Category |
|----|-------|--------|----------|---------------|------------|-----------------|-------------------|----------|
| STK-001 | Get empty stock list | GET | `/api/part/stock/` | — | — | 200 | `{"count": 0, "results": []}` | Positive |
| STK-002 | Create stock item | POST | `/api/part/stock/` | Non-template деталь id=1; Auth | `{"part": 1, "quantity": 100}` | 201 | Объект с `id`, `part=1`, `part_name`, `quantity="100.00000"`, `created` (timestamp) | Positive |
| STK-003 | Create stock with location and batch | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": 50, "location": "Shelf A-1", "batch": "LOT-2026-001"}` | 201 | `location="Shelf A-1"`, `batch="LOT-2026-001"` | Positive |
| STK-004 | Create stock with quantity=0 | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": 0}` | 201 | `quantity="0.00000"` (ноль допустим) | Positive |
| STK-005 | Get stock item by ID | GET | `/api/part/stock/{id}/` | StockItem существует | — | 200 | Объект с read-only полями `part_name`, `created` | Positive |
| STK-006 | Update stock quantity (PATCH) | PATCH | `/api/part/stock/{id}/` | Auth | `{"quantity": 200}` | 200 | `quantity="200.00000"` | Positive |
| STK-007 | Full update stock item (PUT) | PUT | `/api/part/stock/{id}/` | Auth | `{"part": 1, "quantity": 75, "location": "B-2", "batch": null}` | 200 | Все поля обновлены | Positive |
| STK-008 | Delete stock item | DELETE | `/api/part/stock/{id}/` | Auth | — | 204 | — | Positive |
| STK-009 | Filter by part | GET | `/api/part/stock/?part={id}` | StockItem существует | — | 200 | Все `results[].part={id}` | Positive |
| STK-010 | Filter by location | GET | `/api/part/stock/?location=Shelf A-1` | StockItem с location существует | — | 200 | Только items с этой локацией | Positive |
| STK-011 | Filter by batch | GET | `/api/part/stock/?batch=LOT-2026-001` | StockItem с batch существует | — | 200 | Только items с этим batch | Positive |
| STK-012 | Order by quantity descending | GET | `/api/part/stock/?ordering=-quantity` | ≥2 stock items | — | 200 | Первый item имеет наибольший quantity | Positive |
| STK-013 | Create stock for template part | POST | `/api/part/stock/` | Template-деталь (template=True) id=1; Auth | `{"part": 1, "quantity": 10}` | 400 | `error_code=BAD_REQUEST`, ошибка в `details.part` о template | Negative |
| STK-014 | Create with negative quantity | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": -1}` | 400 | `error_code=BAD_REQUEST`, ошибка в `details.quantity` | Negative |
| STK-015 | Create without part field | POST | `/api/part/stock/` | Auth | `{"quantity": 10}` | 400 | `error_code=BAD_REQUEST`, `details.part` — обязательное поле | Negative |
| STK-016 | Create with non-existent part id | POST | `/api/part/stock/` | Auth | `{"part": 999999, "quantity": 10}` | 400 | `error_code=BAD_REQUEST` | Negative |
| STK-017 | Get non-existent stock item | GET | `/api/part/stock/999999/` | — | — | 404 | `error_code=NOT_FOUND` | Negative |
| STK-018 | Create unauthenticated | POST | `/api/part/stock/` | Без Auth | `{"part": 1, "quantity": 10}` | 403 | `error_code=FORBIDDEN` | Negative |
| STK-019 | Minimum positive quantity (0.00001) | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": 0.00001}` | 201 | Создан успешно | Boundary |
| STK-020 | Quantity with 6 decimal places | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": 1.123456}` | 400 | Ошибка decimal_places | Boundary |
| STK-021 | Location exactly 200 chars | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": 1, "location": "A" * 200}` | 201 | Создан успешно | Boundary |
| STK-022 | Location 201 chars | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": 1, "location": "A" * 201}` | 400 | `error_code=BAD_REQUEST` | Boundary |
| STK-023 | Batch exactly 100 chars | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": 1, "batch": "B" * 100}` | 201 | Создан успешно | Boundary |
| STK-024 | Batch 101 chars | POST | `/api/part/stock/` | Auth | `{"part": 1, "quantity": 1, "batch": "B" * 101}` | 400 | `error_code=BAD_REQUEST` | Boundary |

---

## 6. Pagination & Filtering

| ID | Title | Method | Endpoint | Preconditions | Query Params | Expected Status | Expected Response | Category |
|----|-------|--------|----------|---------------|--------------|-----------------|-------------------|----------|
| PAG-001 | Default page size is 25 | GET | `/api/part/` | 26 деталей в БД | — | 200 | `count=26`, `results` содержит 25 items, `next` не null | Positive |
| PAG-002 | Custom page_size=5 | GET | `/api/part/` | ≥5 деталей | `?page_size=5` | 200 | `results` содержит 5 items | Positive |
| PAG-003 | Get second page | GET | `/api/part/` | 10 деталей | `?page_size=5&page=2` | 200 | Вторые 5 деталей (смещение корректное) | Positive |
| PAG-004 | Max page_size=100 | GET | `/api/part/` | 110 деталей | `?page_size=100` | 200 | `results` содержит 100 items (не более) | Positive |
| PAG-005 | Filter parts by assembly=true | GET | `/api/part/` | Есть assembly и non-assembly детали | `?assembly=true` | 200 | Все `results[].assembly=true` | Positive |
| PAG-006 | Filter parts by template=true | GET | `/api/part/` | Есть template детали | `?template=true` | 200 | Все `results[].template=true` | Positive |
| PAG-007 | include_child_categories with non-existent category | GET | `/api/part/` | — | `?category=999999&include_child_categories=true` | 200 | `count=0`, `results=[]` | Positive |
| PAG-008 | Search with no matches | GET | `/api/part/` | — | `?search=nonexistent_xyz_99999` | 200 | `count=0`, `results=[]` | Positive |
| PAG-009 | Ordering by name ascending | GET | `/api/part/` | ≥2 детали | `?ordering=name` | 200 | `results[0].name` <= `results[1].name` | Positive |
| PAG-010 | Ordering by IPN | GET | `/api/part/` | ≥2 детали с IPN | `?ordering=IPN` | 200 | Отсортированы по IPN ASC | Positive |
| PAG-011 | Category filter — direct children only | GET | `/api/part/category/` | Есть родитель с дочерними | `?parent={id}` | 200 | Только прямые потомки (не рекурсивно) | Positive |
| PAG-012 | include_child_categories — deep hierarchy | GET | `/api/part/` | Дерево: Root→Child→Grandchild; деталь в Grandchild | `?category={root_id}&include_child_categories=true` | 200 | Деталь из Grandchild включена в results | Positive |

---

## 7. Field Validation

| ID | Title | Method | Endpoint | Preconditions | Input Body | Expected Status | Expected Response | Category |
|----|-------|--------|----------|---------------|------------|-----------------|-------------------|----------|
| FV-001 | Read-only field id is ignored on create | POST | `/api/part/` | Auth | `{"id": 9999, "name": "Part", "description": "desc"}` | 201 | `id` присвоен автоматически (не 9999) | Positive |
| FV-002 | Read-only field creation_date ignored | POST | `/api/part/` | Auth | `{"name": "Part", "description": "desc", "creation_date": "2000-01-01T00:00:00Z"}` | 201 | `creation_date` — текущее время (не 2000-01-01) | Positive |
| FV-003 | Read-only field part_name in StockItem | POST | `/api/part/stock/` | Auth; деталь id=1 | `{"part": 1, "quantity": 1, "part_name": "Override"}` | 201 | `part_name` в ответе = реальное имя детали | Positive |
| FV-004 | category_id write-only, category read-only | POST | `/api/part/` | Auth; категория id=1 | `{"name": "P", "description": "d", "category_id": 1}` | 201 | В ответе поле `category` как объект, поля `category_id` нет | Positive |
| FV-005 | Part IPN nullable | POST | `/api/part/` | Auth | `{"name": "Part", "description": "desc", "IPN": null}` | 201 | `IPN=null` | Positive |
| FV-006 | Category description nullable | POST | `/api/part/category/` | Auth | `{"name": "Cat"}` | 201 | `description=null` | Positive |
| FV-007 | StockItem location nullable | POST | `/api/part/stock/` | Auth; деталь id=1 | `{"part": 1, "quantity": 1}` | 201 | `location=null`, `batch=null` | Positive |
| FV-008 | BOM note nullable | POST | `/api/part/bom/` | Auth | `{"assembly": 1, "sub_part": 2, "quantity": 1}` | 201 | `note=null` | Positive |
| FV-009 | Revision max_length=20 on Part | POST | `/api/part/` | Auth; `revision_of` существует | `{"name": "P", "description": "d", "revision_of": 1, "revision": "A" * 21}` | 400 | `error_code=BAD_REQUEST`, ошибка поля `revision` | Boundary |
| FV-010 | Invalid JSON body | POST | `/api/part/` | Auth | Невалидный JSON | 400 | Ошибка парсинга | Negative |
| FV-011 | Wrong content type (text/plain) | POST | `/api/part/` | Auth; header `Content-Type: text/plain` | `name=Part` | 400 или 415 | Ошибка типа контента | Negative |

---

## 8. Error Format

| ID | Title | Method | Endpoint | Preconditions | Input | Expected Status | Expected Response Structure | Category |
|----|-------|--------|----------|---------------|-------|-----------------|----------------------------|----------|
| ERR-001 | Validation error format | POST | `/api/part/` | Auth | `{"description": "no name"}` | 400 | `{"error_code": "BAD_REQUEST", "message": "Ошибка валидации данных.", "details": {"name": [...]}}` | Positive |
| ERR-002 | Not found error format | GET | `/api/part/999999/` | — | — | 404 | `{"error_code": "NOT_FOUND", "message": "..."}` | Positive |
| ERR-003 | Unauthenticated write error | POST | `/api/part/` | Без Auth | `{"name": "P", "description": "d"}` | 403 | `{"error_code": "FORBIDDEN", "message": "..."}` | Positive |
| ERR-004 | Method not allowed | DELETE | `/api/part/category/root/` | — | — | 405 | `{"error_code": "METHOD_NOT_ALLOWED", "message": "..."}` | Positive |
| ERR-005 | IntegrityError format (duplicate BOM) | POST | `/api/part/bom/` | BOM item A→B уже существует; Auth | `{"assembly": A_id, "sub_part": B_id, "quantity": 1}` | 400 | `{"error_code": "INTEGRITY_ERROR", "message": "Нарушение ограничения...", "details": "..."}` | Positive |
| ERR-006 | All errors have Content-Type JSON | ANY | любой endpoint | — | Некорректный запрос | 4xx | Заголовок `Content-Type: application/json` | Positive |
| ERR-007 | details field present on field validation error | POST | `/api/part/` | Auth | `{"name": "   ", "description": "ok"}` | 400 | `details` — объект с ключами-полями | Positive |
| ERR-008 | message is a non-empty string | GET | `/api/part/999/` | — | — | 404 | `message` — непустая строка | Positive |

---

**Итого тест-кейсов**: 131  
**Распределение**: Positive — 72 | Negative — 44 | Boundary — 15
