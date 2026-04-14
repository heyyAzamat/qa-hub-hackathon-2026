/**
 * Page Object: Create Part modal / drawer.
 *
 * InvenTree Platform UI opens a Mantine <Modal> when the user clicks
 * "New Part". The dialog has role="dialog"; its form fields use standard
 * HTML labels wired via htmlFor, so getByLabel() works reliably.
 *
 * Category field: InvenTree renders a searchable Mantine <Select>.
 * After typing, Mantine renders <option> elements in a portal outside
 * the dialog — that is why option lookups use `page` not `dialog`.
 *
 * Selector adjustment guide:
 *   If a selector fails, open the app with `--headed` and use the
 *   Playwright Inspector (`test:debug` script) to locate the element.
 */
import { Page, Locator, expect } from '@playwright/test';

export interface CreatePartData {
  name: string;
  /** Category display name as shown in the UI autocomplete. */
  category?: string;
  ipn?: string;
  description?: string;
  units?: string;
  revision?: string;
  // Boolean type flags
  virtual?: boolean;
  template?: boolean;
  assembly?: boolean;
  component?: boolean;
  trackable?: boolean;
  purchaseable?: boolean;
  saleable?: boolean;
}

type PartFlag = 'virtual' | 'template' | 'assembly' | 'component' | 'trackable' | 'purchaseable' | 'saleable';

const FLAG_LABELS: Record<PartFlag, RegExp> = {
  virtual: /virtual/i,
  template: /template/i,
  assembly: /assembly/i,
  component: /component/i,
  trackable: /trackable/i,
  purchaseable: /purchaseable/i,
  saleable: /saleable/i,
};

export class CreatePartModal {
  /** The Mantine modal root — all field lookups scope to this. */
  private readonly dialog: Locator;

  constructor(private readonly page: Page) {
    this.dialog = page.getByRole('dialog');
  }

  /** Wait for the modal to become visible before interacting with it. */
  async waitForOpen(): Promise<void> {
    await expect(this.dialog, 'Create Part modal should open').toBeVisible({
      timeout: 10_000,
    });
  }

  // ── Field setters ─────────────────────────────────────────────────────

  async fillName(name: string): Promise<void> {
    const field = this.dialog.getByLabel(/^name$/i);
    await field.clear();
    await field.fill(name);
  }

  /**
   * Type the category name into the autocomplete and select the first
   * matching option from the dropdown portal.
   */
  async fillCategory(categoryName: string): Promise<void> {
    const input = this.dialog.getByLabel(/category/i);
    await input.fill(categoryName);

    // Mantine portals the listbox outside the dialog.
    const option = this.page
      .getByRole('option', { name: new RegExp(categoryName, 'i') })
      .first();
    await option.waitFor({ state: 'visible', timeout: 8_000 });
    await option.click();
  }

  async fillIPN(ipn: string): Promise<void> {
    await this.dialog.getByLabel(/ipn|internal part number/i).fill(ipn);
  }

  async fillDescription(desc: string): Promise<void> {
    await this.dialog.getByLabel(/description/i).fill(desc);
  }

  async fillUnits(units: string): Promise<void> {
    await this.dialog.getByLabel(/units/i).fill(units);
  }

  async fillRevision(revision: string): Promise<void> {
    await this.dialog.getByLabel(/revision/i).fill(revision);
  }

  /** Set a boolean flag checkbox to the desired state. */
  async setFlag(flag: PartFlag, value: boolean): Promise<void> {
    const checkbox = this.dialog.getByRole('checkbox', { name: FLAG_LABELS[flag] });
    const current = await checkbox.isChecked();
    if (current !== value) {
      await checkbox.click();
    }
  }

  /** Fill all fields defined in `data` in a single call. */
  async fill(data: CreatePartData): Promise<void> {
    await this.fillName(data.name);

    if (data.category !== undefined) await this.fillCategory(data.category);
    if (data.ipn !== undefined) await this.fillIPN(data.ipn);
    if (data.description !== undefined) await this.fillDescription(data.description);
    if (data.units !== undefined) await this.fillUnits(data.units);
    if (data.revision !== undefined) await this.fillRevision(data.revision);

    for (const flag of Object.keys(FLAG_LABELS) as PartFlag[]) {
      if (data[flag] !== undefined) {
        await this.setFlag(flag, data[flag] as boolean);
      }
    }
  }

  // ── Actions ───────────────────────────────────────────────────────────

  /** Click the primary submit / save button inside the modal. */
  async submit(): Promise<void> {
    await this.dialog
      .getByRole('button', { name: /submit|save|create|add/i })
      .click();
  }

  /**
   * Close the modal without submitting.
   * Tries the Close/Cancel button first; falls back to Escape.
   */
  async close(): Promise<void> {
    const closeBtn = this.dialog.getByRole('button', { name: /close|cancel/i });
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
    } else {
      await this.page.keyboard.press('Escape');
    }
    await expect(this.dialog).not.toBeVisible({ timeout: 5_000 });
  }

  // ── Assertions ────────────────────────────────────────────────────────

  /**
   * Assert that at least one validation error is visible inside the modal.
   * Targets common Mantine error class patterns.
   */
  async expectValidationErrors(): Promise<void> {
    // [class*="error"] was removed — Mantine class names are minified in production.
    // Fallback strategy: add data-testid="field-error" to InvenTree's form error
    // components if aria-invalid and data-error prove insufficient.
    const errorLocator = this.dialog
      .locator('[aria-invalid="true"], [data-error]')
      .first();
    await expect(
      errorLocator,
      'At least one validation error should be visible inside the modal',
    ).toBeVisible({ timeout: 5_000 });
  }

  /** Assert that a server-side error message matching `pattern` is shown. */
  async expectErrorMessage(pattern: string | RegExp): Promise<void> {
    await expect(
      this.page.getByText(pattern).first(),
      `Error message matching "${pattern}" should be visible`,
    ).toBeVisible({ timeout: 5_000 });
  }

  /** Assert the modal is still open (form was not accepted). */
  async expectStillOpen(): Promise<void> {
    await expect(
      this.dialog,
      'Modal should remain open when form has validation errors',
    ).toBeVisible();
  }
}
