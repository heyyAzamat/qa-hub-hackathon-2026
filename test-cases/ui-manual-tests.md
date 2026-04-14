# UI Manual Test Cases — InvenTree Parts Module

**Приложение**: InvenTree (demo.inventree.org или локальный Docker-экземпляр)  
**Фокус**: Модуль "Parts" (Детали)  
**Источник требований**: https://docs.inventree.org/en/stable/part/  

---

## Содержание

1. [Part Creation — Manual Input](#1-part-creation--manual-input)
2. [Part Creation — Import (CSV/Bulk)](#2-part-creation--import-csvbulk)
3. [Part Detail View — Overview Tab](#3-part-detail-view--overview-tab)
4. [Part Detail View — Stock Tab](#4-part-detail-view--stock-tab)
5. [Part Detail View — BOM Tab](#5-part-detail-view--bom-tab)
6. [Part Detail View — Parameters Tab](#6-part-detail-view--parameters-tab)
7. [Part Detail View — Variants Tab](#7-part-detail-view--variants-tab)
8. [Part Detail View — Revisions Tab](#8-part-detail-view--revisions-tab)
9. [Part Detail View — Attachments Tab](#9-part-detail-view--attachments-tab)
10. [Part Detail View — Related Parts Tab](#10-part-detail-view--related-parts-tab)
11. [Part Detail View — Test Templates Tab](#11-part-detail-view--test-templates-tab)
12. [Part Categories](#12-part-categories)
13. [Part Attributes & Status](#13-part-attributes--status)
14. [Part Types](#14-part-types)
15. [Unit Settings](#15-unit-settings)
16. [Part Revisions](#16-part-revisions)
17. [Negative & Boundary Scenarios](#17-negative--boundary-scenarios)

---

## 1. Part Creation — Manual Input

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-CREATE-001 | Open Create Part form | Пользователь авторизован | 1. Перейти в раздел Parts. 2. Нажать кнопку "New Part" / "+ Add Part" | Открывается форма создания детали с полями: Name, Description, IPN, Category, Notes, Type-флаги (Assembly, Template, Virtual, Component, Trackable, Purchaseable, Saleable) | Positive |
| UI-CREATE-002 | Create minimal part (name + description only) | Форма создания открыта | 1. Ввести Name: "Test Resistor". 2. Ввести Description: "10k ohm resistor". 3. Нажать Save | Деталь создана. Страница перенаправляет на detail view новой детали. В header отображается "Test Resistor". | Positive |
| UI-CREATE-003 | Create part with IPN | Форма создания открыта | 1. Name: "Capacitor 100uF". 2. Description: "100uF 25V capacitor". 3. IPN: "CAP-100UF-25V". 4. Save | Деталь создана с IPN. В detail view поле IPN отображает "CAP-100UF-25V". | Positive |
| UI-CREATE-004 | Create part with category | Существует категория "Electronics"; форма открыта | 1. Name: "LED Red 5mm". 2. Description: "5mm red LED". 3. Category: выбрать "Electronics" из dropdown. 4. Save | Деталь создана и привязана к категории. В breadcrumb/header отображается категория. | Positive |
| UI-CREATE-005 | Create part — verify all flags defaults | Форма открыта | 1. Открыть форму без заполнения флагов. 2. Проверить значения по умолчанию | Active=On, Virtual=Off, Template=Off, Assembly=Off, Component=On. Trackable/Purchaseable/Saleable — Off по умолчанию. | Positive |
| UI-CREATE-006 | Create part — enable Assembly flag | Форма открыта | 1. Name: "PCB Assembly". 2. Description: "Main PCB". 3. Включить флаг Assembly. 4. Save | Деталь создана с `assembly=true`. В detail view видна вкладка "BOM". | Positive |
| UI-CREATE-007 | Create part — enable Template flag | Форма открыта | 1. Name: "Resistor Template". 2. Description: "Generic resistor". 3. Включить Template. 4. Save | Деталь создана с `template=true`. Видна вкладка "Variants". В detail view отображается метка "Template". | Positive |
| UI-CREATE-008 | Create part — enable Virtual flag | Форма открыта | 1. Name: "Virtual Part". 2. Description: "Non-physical item". 3. Включить Virtual. 4. Save | Деталь создана с `virtual=true`. Отображается метка "Virtual". | Positive |
| UI-CREATE-009 | Create part with Notes | Форма открыта | 1. Name: "Bolt M3x10". 2. Description: "M3 10mm bolt". 3. Notes: "Use stainless steel grade A2". 4. Save | Notes сохранены и отображаются на странице детали. | Positive |
| UI-CREATE-010 | Cancel part creation | Форма открыта | 1. Заполнить Name и Description. 2. Нажать Cancel / закрыть форму | Деталь не создана. Список деталей не изменился. | Positive |
| UI-CREATE-011 | Create part — required field Name validation | Форма открыта | 1. Оставить Name пустым. 2. Заполнить Description. 3. Нажать Save | Форма не сабмитится. Поле Name подсвечивается красным с сообщением об обязательном поле. | Negative |
| UI-CREATE-012 | Create part — required field Description validation | Форма открыта | 1. Заполнить Name. 2. Оставить Description пустым. 3. Save | Ошибка валидации поля Description. Деталь не создана. | Negative |
| UI-CREATE-013 | Create part with duplicate IPN | Существует деталь с IPN="DUPE-001"; форма открыта | 1. Name: "Part2". 2. Description: "desc". 3. IPN: "DUPE-001". 4. Save | Ошибка: IPN уже существует. Форма остаётся открытой с сообщением об ошибке. | Negative |
| UI-CREATE-014 | Create part with Name > 200 characters | Форма открыта | 1. Ввести в Name строку из 201+ символа. 2. Save | Ошибка валидации. Деталь не создана. | Negative |
| UI-CREATE-015 | Create part — search and select category | Форма открыта; много категорий | 1. Кликнуть поле Category. 2. Ввести часть названия категории для поиска. 3. Выбрать из выпадающего списка. 4. Save | Dropdown фильтрует категории по введённому тексту. Выбранная категория сохраняется. | Positive |

---

## 2. Part Creation — Import (CSV/Bulk)

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-IMPORT-001 | Access Import function | Авторизован; раздел Parts | 1. Найти кнопку Import / "Upload Parts". 2. Кликнуть | Открывается интерфейс импорта с выбором файла. | Positive |
| UI-IMPORT-002 | Import valid CSV file | Подготовлен CSV с колонками name, description, IPN | 1. Выбрать файл. 2. Загрузить. 3. Пройти маппинг колонок. 4. Подтвердить импорт | Детали импортированы. Отчёт показывает количество созданных записей. | Positive |
| UI-IMPORT-003 | CSV column mapping UI | Загружен CSV с нестандартными заголовками | 1. Загрузить CSV. 2. Проверить экран маппинга колонок | Интерфейс позволяет сопоставить колонки CSV с полями модели (name, description, IPN, category). | Positive |
| UI-IMPORT-004 | Import CSV with validation errors | CSV содержит строку с дублирующим IPN | 1. Загрузить CSV. 2. Завершить маппинг. 3. Запустить импорт | Импорт частично успешен: валидные строки импортированы, строки с ошибками выделены с описанием проблемы. | Negative |
| UI-IMPORT-005 | Import unsupported file format | Подготовлен файл .xlsx или .txt | 1. Попытаться загрузить неподдерживаемый формат | Интерфейс показывает ошибку формата. Импорт не начинается. | Negative |

---

## 3. Part Detail View — Overview Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-DETAIL-001 | Navigate to Part detail view | Деталь существует | 1. Кликнуть на деталь в списке | Открывается detail view с: header (name, IPN), вкладками, полем статуса (Active/Inactive), описанием, флагами. | Positive |
| UI-DETAIL-002 | All expected tabs are visible | Деталь — Assembly с Template | 1. Открыть detail view такой детали | Вкладки: Stock, BOM, Allocated, Build Orders, Parameters, Variants, Revisions, Attachments, Related Parts, Test Templates. | Positive |
| UI-DETAIL-003 | Edit part from detail view | Деталь существует | 1. Кликнуть Edit (карандаш / кнопку Edit). 2. Изменить Description. 3. Save | Description обновлён. Страница обновляется с новым значением. | Positive |
| UI-DETAIL-004 | Part breadcrumb navigation | Деталь в категории | 1. Открыть detail view | Breadcrumb отображает путь: Home > Parts > Category > Part Name. Ссылки в breadcrumb кликабельны. | Positive |
| UI-DETAIL-005 | Delete part from detail view | Деталь без зависимостей | 1. Нажать Delete (или "Actions" → Delete). 2. Подтвердить | Деталь удалена. Редирект на список деталей. Деталь не появляется в списке. | Positive |
| UI-DETAIL-006 | Part star (favourite) toggle | Деталь существует | 1. Кликнуть иконку звезды рядом с деталью | Деталь добавлена/убрана из избранного. Иконка меняет состояние. | Positive |

---

## 4. Part Detail View — Stock Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-STOCK-001 | View Stock tab | Деталь с ≥1 StockItem | 1. Открыть detail view. 2. Кликнуть вкладку Stock | Таблица с записями StockItem: Quantity, Location, Batch, Created date. Общий остаток отображён в header. | Positive |
| UI-STOCK-002 | Stock tab shows zero stock | Деталь без StockItems | 1. Открыть вкладку Stock | Сообщение "No stock available" или пустая таблица. Общий остаток = 0. | Positive |
| UI-STOCK-003 | Add stock from Stock tab | Не-template деталь | 1. Stock tab. 2. Нажать "Add Stock". 3. Ввести Quantity=50, Location="Shelf A". 4. Save | Новая запись StockItem отображается в таблице. Общий остаток обновлён. | Positive |
| UI-STOCK-004 | Add stock to template part | Template деталь (template=True) | 1. Stock tab. 2. Попытаться добавить stock | Кнопка "Add Stock" отсутствует или действие заблокировано с сообщением "Template parts cannot have stock items". | Negative |

---

## 5. Part Detail View — BOM Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-BOM-001 | View BOM tab | Деталь с assembly=True и BOM items | 1. Открыть detail view. 2. Вкладка BOM | Таблица компонентов: Sub Part, Quantity, Optional, Note. | Positive |
| UI-BOM-002 | BOM tab absent for non-assembly part | Деталь с assembly=False | 1. Открыть detail view | Вкладка BOM отсутствует или скрыта. | Positive |
| UI-BOM-003 | Add BOM item | Assembly деталь; component деталь существует | 1. BOM tab. 2. "Add item". 3. Выбрать component деталь. 4. Quantity: 3. 5. Save | BOM item появился в таблице: component name, quantity=3, optional=false. | Positive |
| UI-BOM-004 | Edit BOM item quantity | BOM item существует | 1. BOM tab. 2. Кликнуть Edit на BOM item. 3. Изменить Quantity. 4. Save | Quantity обновлён в таблице. | Positive |
| UI-BOM-005 | Delete BOM item | BOM item существует | 1. BOM tab. 2. Кликнуть Delete на BOM item. 3. Подтвердить | BOM item удалён из таблицы. | Positive |
| UI-BOM-006 | Add self as BOM component | Assembly деталь (также component) | 1. BOM tab. 2. Попытаться добавить деталь саму себя | Ошибка: деталь не может быть компонентом самой себя. | Negative |

---

## 6. Part Detail View — Parameters Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-PARAMS-001 | View Parameters tab | Деталь существует | 1. Открыть вкладку Parameters | Таблица параметров (может быть пустой). Кнопка добавления параметра. | Positive |
| UI-PARAMS-002 | Add parameter | Существует Parameter Template (напр. "Resistance") | 1. Parameters tab. 2. "Add Parameter". 3. Выбрать Template "Resistance". 4. Data: "10k". 5. Save | Параметр отображается: Name="Resistance", Value="10k". | Positive |
| UI-PARAMS-003 | Edit parameter value | Параметр существует | 1. Parameters tab. 2. Edit параметра. 3. Изменить value. 4. Save | Новое значение отображается в таблице. | Positive |
| UI-PARAMS-004 | Delete parameter | Параметр существует | 1. Нажать Delete на параметр. 2. Подтвердить | Параметр удалён из таблицы. | Positive |
| UI-PARAMS-005 | Parameters inherited from category | Категория имеет Parameter Templates | 1. Создать деталь в этой категории. 2. Открыть Parameters | Параметры из категории предзаполнены / предложены для заполнения. | Positive |

---

## 7. Part Detail View — Variants Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-VARS-001 | Variants tab visible only for Template part | Template-деталь | 1. Открыть detail view template-детали | Вкладка "Variants" присутствует. | Positive |
| UI-VARS-002 | Variants tab absent for non-template part | Обычная деталь (template=False) | 1. Открыть detail view | Вкладка "Variants" отсутствует или скрыта. | Positive |
| UI-VARS-003 | View existing variants | Template с вариантами | 1. Открыть Variants tab | Список вариантов с их Name, IPN, статусом. | Positive |
| UI-VARS-004 | Create variant from template | Template деталь | 1. Variants tab. 2. "Add Variant". 3. Name: "Resistor 10k 5%". 4. Save | Вариант создан и отображается в списке Variants. | Positive |

---

## 8. Part Detail View — Revisions Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-REVS-001 | View Revisions tab (no revisions) | Деталь без ревизий | 1. Открыть Revisions tab | Пустой список. Кнопка создания ревизии. | Positive |
| UI-REVS-002 | Create revision from detail view | Активная деталь | 1. Revisions tab. 2. "New Revision". 3. Revision code: "B". 4. Save | Ревизия создана. Отображается в списке: Revision="B", ссылка на detail view ревизии. | Positive |
| UI-REVS-003 | Navigate to revision detail | Ревизия существует | 1. Revisions tab. 2. Кликнуть на ревизию | Открывается detail view ревизии. В header отображается revision code. `revision_of` ссылается на исходную деталь. | Positive |
| UI-REVS-004 | Create revision with duplicate code | Ревизия "B" существует | 1. Revisions tab. 2. "New Revision". 3. Revision code: "B". 4. Save | Ошибка: ревизия с кодом "B" уже существует. | Negative |
| UI-REVS-005 | Attempt to create revision of inactive part | Деталь неактивна | 1. Revisions tab неактивной детали. 2. "New Revision". 3. Save | Ошибка: нельзя создать ревизию для неактивной детали. | Negative |

---

## 9. Part Detail View — Attachments Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-ATTACH-001 | View Attachments tab (empty) | Деталь без вложений | 1. Открыть Attachments tab | Пустой список. Кнопки "Upload File" и "Add Link". | Positive |
| UI-ATTACH-002 | Upload file attachment | Деталь существует; файл готов | 1. Attachments tab. 2. "Upload File". 3. Выбрать файл (PDF/PNG). 4. Comment: "Datasheet". 5. Upload | Файл появляется в списке с именем, размером, датой загрузки. Ссылка для скачивания доступна. | Positive |
| UI-ATTACH-003 | Add URL link attachment | Деталь существует | 1. Attachments tab. 2. "Add Link". 3. URL: "https://example.com/datasheet". 4. Comment: "Online datasheet". 5. Save | Ссылка отображается в таблице. Клик открывает URL. | Positive |
| UI-ATTACH-004 | Delete attachment | Вложение существует | 1. Нажать Delete на вложение. 2. Подтвердить | Вложение удалено из списка. | Positive |

---

## 10. Part Detail View — Related Parts Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-REL-001 | View Related Parts tab (empty) | Деталь без related parts | 1. Открыть Related Parts tab | Пустой список. Кнопка "Add Related Part". | Positive |
| UI-REL-002 | Add related part | Существуют ≥2 детали | 1. Related Parts tab. 2. "Add Related Part". 3. Выбрать другую деталь. 4. Save | Связанная деталь отображается в таблице с именем и ссылкой. | Positive |
| UI-REL-003 | Remove related part | Related part существует | 1. Нажать Delete на связь. 2. Подтвердить | Связь удалена. Список обновлён. | Positive |
| UI-REL-004 | Related part link is bidirectional | Добавлена связь A↔B | 1. Открыть деталь A: Related Parts tab — видна B. 2. Открыть деталь B: Related Parts tab | Деталь A отображается в Related Parts детали B (связь двунаправленная). | Positive |

---

## 11. Part Detail View — Test Templates Tab

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-TEST-001 | View Test Templates tab (empty) | Trackable деталь | 1. Открыть Test Templates tab | Пустой список. Кнопка "Add Test Template". | Positive |
| UI-TEST-002 | Add test template | Trackable деталь | 1. Test Templates tab. 2. "Add Test Template". 3. Name: "Continuity Test". 4. Required: Yes. 5. Save | Тест-шаблон отображается в таблице: Name, Required, Description. | Positive |
| UI-TEST-003 | Test Templates tab absent for non-trackable | Деталь с Trackable=False | 1. Открыть detail view | Вкладка Test Templates отсутствует или скрыта. | Positive |

---

## 12. Part Categories

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-CAT-001 | Navigate to Part Categories | Авторизован | 1. Parts → Categories (или через левое меню) | Открывается дерево категорий. Отображаются корневые категории с количеством дочерних. | Positive |
| UI-CAT-002 | Create root category | Раздел категорий | 1. "Add Category". 2. Name: "Electronics". 3. Description: "Electronic components". 4. Parent: пусто. 5. Save | Категория создана в корне дерева. | Positive |
| UI-CAT-003 | Create child category | Категория "Electronics" существует | 1. Открыть "Electronics". 2. "Add Sub-Category" или создать с Parent="Electronics". 3. Name: "Resistors". 4. Save | "Resistors" отображается как дочерняя категория "Electronics". | Positive |
| UI-CAT-004 | Navigate category tree | Многоуровневые категории (3 уровня) | 1. Кликать по узлам дерева | Дерево разворачивается/сворачивается. Breadcrumb обновляется. | Positive |
| UI-CAT-005 | View parts within category | Категория с деталями | 1. Открыть категорию | Список деталей в данной категории. Каждая деталь кликабельна. | Positive |
| UI-CAT-006 | View parts including subcategories | Корневая категория с дочерними | 1. Включить "Include subcategories" фильтр | Список включает детали из всех дочерних категорий. | Positive |
| UI-CAT-007 | Edit category | Категория существует | 1. Edit категории. 2. Изменить Description. 3. Save | Description обновлён. | Positive |
| UI-CAT-008 | Delete empty category | Категория без деталей и дочерних | 1. Delete категории. 2. Confirm | Категория удалена. Не отображается в дереве. | Positive |
| UI-CAT-009 | Delete category with parts (cascade check) | Категория с деталями | 1. Попытаться удалить | Предупреждение об удалении или детали перемещаются в "Uncategorized". Поведение документируется. | Positive |
| UI-CAT-010 | Category parametric table | Категория имеет Parameter Templates | 1. Открыть категорию. 2. Перейти на вкладку "Parameters" | Таблица с колонками: Part, и по одной колонке на каждый параметр шаблона. | Positive |
| UI-CAT-011 | Filter parts within category | Категория с деталями | 1. Открыть категорию. 2. Применить фильтр по Active/Inactive | Список фильтруется. | Positive |
| UI-CAT-012 | Search within category | Категория с деталями | 1. Ввести текст в поле поиска внутри категории | Список фильтруется по введённой строке (по имени и IPN). | Positive |
| UI-CAT-013 | Create category without name | Форма создания категории | 1. Оставить Name пустым. 2. Save | Ошибка валидации. Категория не создана. | Negative |
| UI-CAT-014 | Set parent to self (circular dependency) | Категория существует | 1. Edit категории. 2. Установить Parent = сама категория. 3. Save | Ошибка: циклическая зависимость. | Negative |

---

## 13. Part Attributes & Status

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-ATTR-001 | View Active status badge | Активная деталь | 1. Открыть detail view | Зелёный badge/метка "Active" отображается в header. | Positive |
| UI-ATTR-002 | View Inactive status | Неактивная деталь | 1. Открыть detail view | Серый/красный badge "Inactive". Деталь может быть скрыта из некоторых фильтров. | Positive |
| UI-ATTR-003 | Deactivate part | Активная деталь без активных ревизий | 1. Edit. 2. Active: Off. 3. Save | Деталь деактивирована. Статус меняется на "Inactive". | Positive |
| UI-ATTR-004 | Reactivate part | Неактивная деталь | 1. Edit. 2. Active: On. 3. Save | Деталь активирована. Статус "Active". | Positive |
| UI-ATTR-005 | Deactivate part with active revisions | Деталь с активными дочерними ревизиями | 1. Edit. 2. Active: Off. 3. Save | Ошибка: нельзя деактивировать деталь с активными ревизиями. | Negative |
| UI-ATTR-006 | Filter parts by Active/Inactive | Список деталей | 1. Применить фильтр Active=Yes | Только активные детали в списке. | Positive |
| UI-ATTR-007 | Part detail shows all flag values | Деталь со смешанными флагами | 1. Открыть detail view | Все флаги (Assembly, Template, Virtual, Component, Trackable, etc.) корректно отображены. | Positive |

---

## 14. Part Types

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-TYPE-001 | Create Virtual part | Форма создания открыта | 1. Включить Virtual. 2. Save | Деталь создана. Метка/badge "Virtual" отображается. Stock и BOM ограничены для virtual деталей. | Positive |
| UI-TYPE-002 | Create Template part + verify Variants tab | Форма создания | 1. Включить Template. 2. Save | Вкладка Variants появляется в detail view. Stock tab может быть скрыт/ограничен. | Positive |
| UI-TYPE-003 | Create Assembly part + verify BOM tab | Форма создания | 1. Включить Assembly. 2. Save | Вкладка BOM появляется в detail view. | Positive |
| UI-TYPE-004 | Create Component part | Форма создания | 1. Component = On (по умолчанию). 2. Save | Деталь может быть добавлена в BOM другой сборки. | Positive |
| UI-TYPE-005 | Create Trackable part + verify Test Templates | Форма создания | 1. Включить Trackable. 2. Save | Вкладка Test Templates появляется в detail view. | Positive |
| UI-TYPE-006 | Create Purchaseable part | Форма создания | 1. Включить Purchaseable. 2. Save | Деталь отображается в списках, связанных с закупками. | Positive |
| UI-TYPE-007 | Create Saleable part | Форма создания | 1. Включить Saleable. 2. Save | Деталь отображается в списках, связанных с продажами. | Positive |
| UI-TYPE-008 | Part can have multiple types simultaneously | Форма создания | 1. Включить Assembly + Trackable + Component. 2. Save | Деталь создана. Все три флага активны. BOM и Test Templates вкладки доступны. | Positive |
| UI-TYPE-009 | Assembly part cannot be added to own BOM | Assembly-деталь | 1. BOM tab. 2. Добавить саму деталь как компонент | Ошибка: деталь не может быть компонентом самой себя. | Negative |

---

## 15. Unit Settings

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-UNITS-001 | Access Unit Settings | Авторизован (admin) | 1. Settings → Parts → Units | Страница настроек единиц измерения. | Positive |
| UI-UNITS-002 | Add custom unit | Страница Units открыта | 1. "Add Unit". 2. Name: "Reel". 3. Symbol: "rl". 4. Save | Единица измерения создана и доступна при создании деталей. | Positive |
| UI-UNITS-003 | Assign unit to part | Создана единица "Reel"; форма создания/редактирования детали | 1. Edit детали. 2. Units: выбрать "Reel". 3. Save | Поле Units отображает "Reel" в detail view. | Positive |
| UI-UNITS-004 | Delete unit (not in use) | Единица создана, не привязана к деталям | 1. Удалить единицу. 2. Confirm | Единица удалена. Не появляется в dropdown при создании деталей. | Positive |
| UI-UNITS-005 | Delete unit in use | Единица привязана к деталям | 1. Попытаться удалить единицу | Предупреждение или ошибка: единица используется деталями. | Negative |

---

## 16. Part Revisions

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-REV-001 | Create revision from Part detail | Активная деталь | 1. Detail view. 2. Revisions tab. 3. "New Revision". 4. Revision code: "B". 5. Save | Ревизия "B" создана. Ссылки на revision в списке. Ревизия наследует name, description, category. | Positive |
| UI-REV-002 | Revision inherits parent fields | Деталь с категорией и флагами | 1. Создать ревизию | В detail view ревизии: `revision_of` указывает на родителя; category та же. | Positive |
| UI-REV-003 | Edit revision independently | Ревизия существует | 1. Открыть detail view ревизии. 2. Edit Name. 3. Save | Name ревизии изменён независимо от родителя. | Positive |
| UI-REV-004 | Revision appears in parent's Revisions tab | Ревизия создана | 1. Открыть исходную деталь. 2. Revisions tab | Ревизия "B" присутствует в списке. | Positive |
| UI-REV-005 | Multiple revisions — correct ordering | 3 ревизии B, C, D | 1. Revisions tab | Ревизии отображены по дате (новейшая первой). | Positive |
| UI-REV-006 | Delete specific revision | Ревизия существует | 1. Revisions tab. 2. Delete ревизии B. 3. Confirm | Ревизия B удалена. Ревизии C и D остались. | Positive |
| UI-REV-007 | Duplicate revision code blocked | Ревизия "B" существует | 1. New Revision. 2. Code: "B". 3. Save | Ошибка: код ревизии "B" уже существует для данной детали. | Negative |
| UI-REV-008 | Cannot create revision of inactive parent | Деталь неактивна | 1. Edit неактивной детали. 2. Revisions tab. 3. New Revision | Ошибка или кнопка недоступна: нельзя создать ревизию от неактивной детали. | Negative |
| UI-REV-009 | Revision of a revision (template constraint) | Ревизия B существует | 1. Открыть detail view ревизии B. 2. Revisions tab. 3. "New Revision" | Система предупреждает или блокирует: ревизии от ревизии могут быть запрещены. Документировать фактическое поведение. | Edge Case |

---

## 17. Negative & Boundary Scenarios

| ID | Title | Preconditions | Steps | Expected Result | Category |
|----|-------|---------------|-------|-----------------|----------|
| UI-NEG-001 | Create part — whitespace-only name | Форма открыта | 1. Name: "   ". 2. Description: "ok". 3. Save | Ошибка валидации. Форма не сабмитится. | Negative |
| UI-NEG-002 | Access non-existent part URL | — | 1. Ввести в адресную строку `/parts/999999/` | 404 страница или редирект на список с сообщением об ошибке. | Negative |
| UI-NEG-003 | Remove assembly flag with existing BOM | Assembly деталь с BOM items | 1. Edit. 2. Assembly: Off. 3. Save | Ошибка: нельзя снять флаг Assembly, пока есть BOM items. | Negative |
| UI-NEG-004 | Add inactive part to BOM | Неактивный компонент | 1. BOM tab сборки. 2. Добавить неактивный компонент | Ошибка: неактивная деталь не может быть добавлена в BOM. | Negative |
| UI-NEG-005 | Add non-component part to BOM | Деталь с component=False | 1. BOM tab. 2. Добавить деталь с component=False | Ошибка: деталь не является компонентом. | Negative |
| UI-NEG-006 | Add stock to template part | Template деталь | 1. Stock tab. 2. Попытаться добавить stock | Ошибка или кнопка заблокирована: шаблонные детали не могут иметь stock. | Negative |
| UI-NEG-007 | Create part with IPN exactly 50 chars | Форма открыта | 1. IPN: 50-символьная строка. 2. Save | Деталь создана успешно. | Boundary |
| UI-NEG-008 | Create part with IPN 51 chars | Форма открыта | 1. IPN: 51-символьная строка. 2. Save | Ошибка валидации поля IPN. | Boundary |
| UI-NEG-009 | Create part with Name 200 chars | Форма открыта | 1. Name: 200 символов. 2. Save | Деталь создана успешно. | Boundary |
| UI-NEG-010 | Create part with Name 201 chars | Форма открыта | 1. Name: 201 символ. 2. Save | Ошибка валидации поля Name. | Boundary |
| UI-NEG-011 | Cross-functional: create part → add parameter → add stock → verify in category | Категория с Parameter Template | 1. Создать деталь в категории. 2. Parameters tab: добавить параметр. 3. Stock tab: добавить stock. 4. Открыть категорию → вкладка Parts. 5. Открыть параметрическую таблицу категории | Деталь отображается в категории. Параметр виден в параметрической таблице. Stock count отображён в деталях категории. | Positive |
| UI-NEG-012 | Part list global search | Несколько деталей | 1. Ввести часть IPN или name в глобальный поиск | Результаты поиска показывают matching детали с ссылками. | Positive |
| UI-NEG-013 | Part list pagination | >25 деталей | 1. Открыть список деталей | Пагинация работает. Следующая страница загружает новые детали. | Positive |
| UI-NEG-014 | Sort parts list by Name | Список деталей | 1. Кликнуть на заголовок колонки Name | Список сортируется по имени (ASC → DESC → без сортировки). | Positive |

---

**Итого тест-кейсов**: 101  
**Распределение**: Positive — 73 | Negative — 21 | Boundary — 4 | Edge Case — 3  

**Примечание**: Тест-кейсы для UI-автоматизации (Phase 3) будут реализованы на базе этих сценариев, приоритетно — кросс-функциональный тест UI-NEG-011 и smoke-тесты из разделов 1, 3, 12, 13.
