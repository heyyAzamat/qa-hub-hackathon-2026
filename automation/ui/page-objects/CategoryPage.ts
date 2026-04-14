/**
 * Page Object: Part category page (/ui/part/category/{pk}/).
 *
 * Covers:
 *   - Breadcrumb hierarchy verification
 *   - Parts list within a category
 *   - Sub-category list
 *   - Category CRUD actions (New, Edit, Delete)
 */
import { Page, expect } from '@playwright/test';
import { navigateToCategory } from '../helpers/navigation';

export class CategoryPage {
  constructor(private readonly page: Page) {}

  /** Navigate to /ui/part/category/{pk}/ and wait for the page to settle. */
  async navigate(pk: number): Promise<void> {
    await navigateToCategory(this.page, pk);
  }

  // ── Breadcrumb ─────────────────────────────────────────────────────────

  /**
   * Assert the breadcrumb trail contains the given text.
   * Mantine renders breadcrumbs as an <ol> or <nav> with a known class.
   */
  async expectBreadcrumbContains(text: string): Promise<void> {
    // Prefer the ARIA landmark; the Mantine class fallback ([class*="Breadcrumbs"])
    // was removed because class names are minified in production builds.
    // If this locator misses, add data-testid="breadcrumb" to the component.
    const breadcrumb = this.page
      .locator('[aria-label="breadcrumb"], nav[aria-label="breadcrumb"]')
      .first();

    await expect(
      breadcrumb,
      `Breadcrumb should contain text "${text}"`,
    ).toContainText(text, { timeout: 5_000 });
  }

  // ── Parts list ─────────────────────────────────────────────────────────

  /** Assert a part appears in the parts table for this category. */
  async expectPartInList(partName: string): Promise<void> {
    await expect(
      this.page.getByRole('cell', { name: partName }).first(),
      `Part "${partName}" should appear in the category parts list`,
    ).toBeVisible({ timeout: 10_000 });
  }

  // ── Sub-category list ──────────────────────────────────────────────────

  /** Assert a sub-category appears in the sub-category table. */
  async expectSubCategoryInList(name: string): Promise<void> {
    await expect(
      this.page.getByRole('cell', { name }).first(),
      `Sub-category "${name}" should appear in the category list`,
    ).toBeVisible({ timeout: 10_000 });
  }

  // ── Category CRUD ──────────────────────────────────────────────────────

  /** Click the button to create a new sub-category. */
  async clickNewCategory(): Promise<void> {
    await this.page
      .getByRole('button', { name: /new category|add category/i })
      .click();

    await expect(
      this.page.getByRole('dialog'),
      'New Category dialog should open',
    ).toBeVisible({ timeout: 10_000 });
  }

  /** Click the Edit category button. */
  async clickEditCategory(): Promise<void> {
    await this.page
      .getByRole('button', { name: /edit category|edit/i })
      .first()
      .click();

    await expect(
      this.page.getByRole('dialog'),
      'Edit Category dialog should open',
    ).toBeVisible({ timeout: 10_000 });
  }

  /** Click the Delete category button. */
  async clickDeleteCategory(): Promise<void> {
    await this.page
      .getByRole('button', { name: /delete category|delete/i })
      .first()
      .click();

    await expect(
      this.page.getByRole('dialog'),
      'Delete confirmation dialog should open',
    ).toBeVisible({ timeout: 10_000 });
  }

  // ── Dialog helpers ─────────────────────────────────────────────────────

  /** Fill the Name field in the currently open category dialog. */
  async fillCategoryName(name: string): Promise<void> {
    const dialog = this.page.getByRole('dialog');
    const nameField = dialog.getByLabel(/^name$/i);
    await nameField.clear();
    await nameField.fill(name);
  }

  /** Submit the open dialog and wait for it to close. */
  async submitDialog(): Promise<void> {
    const dialog = this.page.getByRole('dialog');
    await dialog.getByRole('button', { name: /submit|save|confirm/i }).click();
    await expect(dialog, 'Dialog should close after submitting').not.toBeVisible({
      timeout: 10_000,
    });
  }

  /** Confirm a delete dialog (the destructive action button). */
  async confirmDelete(): Promise<void> {
    const dialog = this.page.getByRole('dialog');
    await dialog.getByRole('button', { name: /confirm|delete|yes/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10_000 });
  }

  // ── Assertions ─────────────────────────────────────────────────────────

  /** Assert the page heading matches the category name. */
  async expectCategoryTitle(name: string): Promise<void> {
    await expect(
      this.page.getByRole('heading', { name }).first(),
      `Category page heading should be "${name}"`,
    ).toBeVisible({ timeout: 10_000 });
  }

  /**
   * Assert that a warning / error is shown when attempting to delete
   * a category that still contains parts.
   */
  async expectDeleteBlockedOrWarned(): Promise<void> {
    // Either the dialog contains an error, or a toast / notification appears.
    const warningInDialog = this.page
      .getByRole('dialog')
      .getByText(/cannot be deleted|contains parts|not empty|has parts/i)
      .first();

    const toastWarning = this.page
      .getByRole('alert')
      .getByText(/cannot be deleted|contains parts|not empty/i)
      .first();

    const eitherVisible = (await warningInDialog.isVisible()) || (await toastWarning.isVisible());

    expect(
      eitherVisible,
      'A warning about non-empty category should be shown when deleting a category with parts',
    ).toBe(true);
  }
}
