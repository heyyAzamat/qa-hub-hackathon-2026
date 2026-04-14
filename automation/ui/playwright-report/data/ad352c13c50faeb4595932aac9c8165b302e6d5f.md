# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: categories/category-hierarchy.spec.ts >> CAT-003h: parts list filtered by child category shows only parts in that category
- Location: tests/categories/category-hierarchy.spec.ts:100:5

# Error details

```
Error: Part "Hierarchy_Part_1776170517703" should appear in the category parts list

expect(locator).toBeVisible() failed

Locator: getByRole('cell', { name: 'Hierarchy_Part_1776170517703' }).first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Part "Hierarchy_Part_1776170517703" should appear in the category parts list with timeout 10000ms
  - waiting for getByRole('cell', { name: 'Hierarchy_Part_1776170517703' }).first()

```

# Test source

```ts
  1   | /**
  2   |  * Page Object: Part category page (/ui/part/category/{pk}/).
  3   |  *
  4   |  * Covers:
  5   |  *   - Breadcrumb hierarchy verification
  6   |  *   - Parts list within a category
  7   |  *   - Sub-category list
  8   |  *   - Category CRUD actions (New, Edit, Delete)
  9   |  */
  10  | import { Page, expect } from '@playwright/test';
  11  | import { navigateToCategory } from '../helpers/navigation';
  12  | 
  13  | export class CategoryPage {
  14  |   constructor(private readonly page: Page) {}
  15  | 
  16  |   /** Navigate to /ui/part/category/{pk}/ and wait for the page to settle. */
  17  |   async navigate(pk: number): Promise<void> {
  18  |     await navigateToCategory(this.page, pk);
  19  |   }
  20  | 
  21  |   // ── Breadcrumb ─────────────────────────────────────────────────────────
  22  | 
  23  |   /**
  24  |    * Assert the breadcrumb trail contains the given text.
  25  |    * Mantine renders breadcrumbs as an <ol> or <nav> with a known class.
  26  |    */
  27  |   async expectBreadcrumbContains(text: string): Promise<void> {
  28  |     // Prefer the ARIA landmark; the Mantine class fallback ([class*="Breadcrumbs"])
  29  |     // was removed because class names are minified in production builds.
  30  |     // If this locator misses, add data-testid="breadcrumb" to the component.
  31  |     const breadcrumb = this.page
  32  |       .locator('[aria-label="breadcrumb"], nav[aria-label="breadcrumb"]')
  33  |       .first();
  34  | 
  35  |     await expect(
  36  |       breadcrumb,
  37  |       `Breadcrumb should contain text "${text}"`,
  38  |     ).toContainText(text, { timeout: 5_000 });
  39  |   }
  40  | 
  41  |   // ── Parts list ─────────────────────────────────────────────────────────
  42  | 
  43  |   /** Assert a part appears in the parts table for this category. */
  44  |   async expectPartInList(partName: string): Promise<void> {
  45  |     await expect(
  46  |       this.page.getByRole('cell', { name: partName }).first(),
  47  |       `Part "${partName}" should appear in the category parts list`,
> 48  |     ).toBeVisible({ timeout: 10_000 });
      |       ^ Error: Part "Hierarchy_Part_1776170517703" should appear in the category parts list
  49  |   }
  50  | 
  51  |   // ── Sub-category list ──────────────────────────────────────────────────
  52  | 
  53  |   /** Assert a sub-category appears in the sub-category table. */
  54  |   async expectSubCategoryInList(name: string): Promise<void> {
  55  |     await expect(
  56  |       this.page.getByRole('cell', { name }).first(),
  57  |       `Sub-category "${name}" should appear in the category list`,
  58  |     ).toBeVisible({ timeout: 10_000 });
  59  |   }
  60  | 
  61  |   // ── Category CRUD ──────────────────────────────────────────────────────
  62  | 
  63  |   /** Click the button to create a new sub-category. */
  64  |   async clickNewCategory(): Promise<void> {
  65  |     await this.page
  66  |       .getByRole('button', { name: /new category|add category/i })
  67  |       .click();
  68  | 
  69  |     await expect(
  70  |       this.page.getByRole('dialog'),
  71  |       'New Category dialog should open',
  72  |     ).toBeVisible({ timeout: 10_000 });
  73  |   }
  74  | 
  75  |   /** Click the Edit category button. */
  76  |   async clickEditCategory(): Promise<void> {
  77  |     await this.page
  78  |       .getByRole('button', { name: /edit category|edit/i })
  79  |       .first()
  80  |       .click();
  81  | 
  82  |     await expect(
  83  |       this.page.getByRole('dialog'),
  84  |       'Edit Category dialog should open',
  85  |     ).toBeVisible({ timeout: 10_000 });
  86  |   }
  87  | 
  88  |   /** Click the Delete category button. */
  89  |   async clickDeleteCategory(): Promise<void> {
  90  |     await this.page
  91  |       .getByRole('button', { name: /delete category|delete/i })
  92  |       .first()
  93  |       .click();
  94  | 
  95  |     await expect(
  96  |       this.page.getByRole('dialog'),
  97  |       'Delete confirmation dialog should open',
  98  |     ).toBeVisible({ timeout: 10_000 });
  99  |   }
  100 | 
  101 |   // ── Dialog helpers ─────────────────────────────────────────────────────
  102 | 
  103 |   /** Fill the Name field in the currently open category dialog. */
  104 |   async fillCategoryName(name: string): Promise<void> {
  105 |     const dialog = this.page.getByRole('dialog');
  106 |     const nameField = dialog.getByLabel(/^name$/i);
  107 |     await nameField.clear();
  108 |     await nameField.fill(name);
  109 |   }
  110 | 
  111 |   /** Submit the open dialog and wait for it to close. */
  112 |   async submitDialog(): Promise<void> {
  113 |     const dialog = this.page.getByRole('dialog');
  114 |     await dialog.getByRole('button', { name: /submit|save|confirm/i }).click();
  115 |     await expect(dialog, 'Dialog should close after submitting').not.toBeVisible({
  116 |       timeout: 10_000,
  117 |     });
  118 |   }
  119 | 
  120 |   /** Confirm a delete dialog (the destructive action button). */
  121 |   async confirmDelete(): Promise<void> {
  122 |     const dialog = this.page.getByRole('dialog');
  123 |     await dialog.getByRole('button', { name: /confirm|delete|yes/i }).click();
  124 |     await expect(dialog).not.toBeVisible({ timeout: 10_000 });
  125 |   }
  126 | 
  127 |   // ── Assertions ─────────────────────────────────────────────────────────
  128 | 
  129 |   /** Assert the page heading matches the category name. */
  130 |   async expectCategoryTitle(name: string): Promise<void> {
  131 |     await expect(
  132 |       this.page.getByRole('heading', { name }).first(),
  133 |       `Category page heading should be "${name}"`,
  134 |     ).toBeVisible({ timeout: 10_000 });
  135 |   }
  136 | 
  137 |   /**
  138 |    * Assert that a warning / error is shown when attempting to delete
  139 |    * a category that still contains parts.
  140 |    */
  141 |   async expectDeleteBlockedOrWarned(): Promise<void> {
  142 |     // Either the dialog contains an error, or a toast / notification appears.
  143 |     const warningInDialog = this.page
  144 |       .getByRole('dialog')
  145 |       .getByText(/cannot be deleted|contains parts|not empty|has parts/i)
  146 |       .first();
  147 | 
  148 |     const toastWarning = this.page
```