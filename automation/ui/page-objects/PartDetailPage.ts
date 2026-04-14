/**
 * Page Object: Part detail page (/ui/part/{pk}/).
 *
 * InvenTree Platform UI renders the detail view as a tabbed panel
 * using Mantine's <Tabs> component, which produces role="tab" elements.
 * Tab panels have role="tabpanel".
 *
 * Tab visibility rules (from InvenTree docs):
 *   BOM         — only visible when part.assembly = true
 *   Variants    — only visible when part.is_template = true
 *   Test Templates — only visible when part.trackable = true
 */
import { Page, Locator, expect } from '@playwright/test';
import { navigateToPartDetail } from '../helpers/navigation';

/** All known tabs in InvenTree's part detail view. */
export type TabName =
  | 'Details'
  | 'Stock'
  | 'BOM'
  | 'Allocated'
  | 'Build Orders'
  | 'Parameters'
  | 'Variants'
  | 'Revisions'
  | 'Attachments'
  | 'Related Parts'
  | 'Test Templates';

export class PartDetailPage {
  constructor(private readonly page: Page) {}

  /** Navigate to /ui/part/{pk}/ and wait for the page to be ready. */
  async navigate(pk: number): Promise<void> {
    await navigateToPartDetail(this.page, pk);
  }

  // ── Tab navigation ─────────────────────────────────────────────────────

  /**
   * Click the tab with the given name and assert the tab panel renders.
   * Uses a regex match so minor label changes ("Build Orders" vs "Builds") are tolerated.
   */
  async clickTab(tabName: TabName): Promise<void> {
    const tab = this.page.getByRole('tab', { name: new RegExp(tabName, 'i') });
    await tab.waitFor({ state: 'visible', timeout: 5_000 });
    await tab.click();

    await expect(
      this.page.getByRole('tabpanel').first(),
      `Tab panel for "${tabName}" should be visible after clicking the tab`,
    ).toBeVisible({ timeout: 10_000 });
  }

  /** Assert that a tab with the given name exists in the tab list. */
  async expectTabVisible(tabName: TabName): Promise<void> {
    await expect(
      this.page.getByRole('tab', { name: new RegExp(tabName, 'i') }),
      `Tab "${tabName}" should be present in the tab bar`,
    ).toBeVisible({ timeout: 5_000 });
  }

  /** Assert that a tab is NOT present (e.g. BOM on a non-Assembly part). */
  async expectTabHidden(tabName: TabName): Promise<void> {
    await expect(
      this.page.getByRole('tab', { name: new RegExp(tabName, 'i') }),
      `Tab "${tabName}" should NOT be present on this part`,
    ).not.toBeVisible({ timeout: 5_000 });
  }

  // ── Status ─────────────────────────────────────────────────────────────

  async expectActive(): Promise<void> {
    await expect(
      this.page.getByText(/\bactive\b/i).first(),
      'Part detail page should show Active status',
    ).toBeVisible({ timeout: 5_000 });
  }

  async expectInactive(): Promise<void> {
    await expect(
      this.page.getByText(/\binactive\b/i).first(),
      'Part detail page should show Inactive status',
    ).toBeVisible({ timeout: 5_000 });
  }

  // ── Type badges ────────────────────────────────────────────────────────

  /**
   * Assert that a type badge or label for the given type is visible.
   * InvenTree renders type flags as coloured badges near the part header.
   */
  async expectTypeBadge(type: string): Promise<void> {
    await expect(
      this.page.getByText(new RegExp(`\\b${type}\\b`, 'i')).first(),
      `Part detail page should display a "${type}" badge or label`,
    ).toBeVisible({ timeout: 5_000 });
  }

  // ── Edit actions ───────────────────────────────────────────────────────

  /** Open the Edit Part dialog. */
  async clickEditPart(): Promise<void> {
    await this.page
      .getByRole('button', { name: /^edit( part)?$/i })
      .first()
      .click();

    await expect(
      this.page.getByRole('dialog'),
      'Edit Part dialog should open',
    ).toBeVisible({ timeout: 10_000 });
  }

  /**
   * Toggle the Active checkbox off via the Edit dialog, then submit.
   * Leaves the dialog closed on exit.
   */
  async setInactive(): Promise<void> {
    await this.clickEditPart();

    const dialog = this.page.getByRole('dialog');
    const activeCheckbox = dialog.getByRole('checkbox', { name: /active/i });
    if (await activeCheckbox.isChecked()) {
      await activeCheckbox.uncheck();
    }

    await dialog.getByRole('button', { name: /submit|save/i }).click();
    await expect(dialog, 'Edit dialog should close after saving').not.toBeVisible({
      timeout: 10_000,
    });
  }

  /**
   * Toggle the Active checkbox on via the Edit dialog, then submit.
   * Asserts the checkbox is unchecked before enabling it.
   * Leaves the dialog closed on exit.
   */
  async setActive(): Promise<void> {
    await this.clickEditPart();

    const dialog = this.page.getByRole('dialog');
    const activeCheckbox = dialog.getByRole('checkbox', { name: /active/i });

    await expect(
      activeCheckbox,
      'Active checkbox should be unchecked before re-enabling the part',
    ).not.toBeChecked();
    await activeCheckbox.check();

    await dialog.getByRole('button', { name: /submit|save/i }).click();
    await expect(dialog, 'Edit dialog should close after saving').not.toBeVisible({
      timeout: 10_000,
    });
  }

  /**
   * Open the Add BOM Item dialog from the BOM tab.
   * Call after `clickTab('BOM')`.
   */
  async clickAddBomItem(): Promise<void> {
    await this.page.getByRole('button', { name: /add bom item|add item/i }).click();
    await expect(
      this.page.getByRole('dialog'),
      'Add BOM Item dialog should open',
    ).toBeVisible({ timeout: 10_000 });
  }

  // ── Revisions tab helpers ─────────────────────────────────────────────

  /**
   * Click the "Add Revision" / "Duplicate Part" action in the Revisions tab.
   * The exact label depends on InvenTree version; the regex matches both.
   */
  async clickAddRevision(): Promise<void> {
    await this.page
      .getByRole('button', { name: /new revision|add revision|duplicate/i })
      .first()
      .click();

    await expect(
      this.page.getByRole('dialog'),
      'Add Revision dialog should open',
    ).toBeVisible({ timeout: 10_000 });
  }

  /** Fill the revision code field in the open dialog and submit. */
  async submitRevision(code: string): Promise<void> {
    const dialog = this.page.getByRole('dialog');
    await dialog.getByLabel(/revision/i).fill(code);
    await dialog.getByRole('button', { name: /submit|save|create/i }).click();
    await expect(dialog, 'Revision dialog should close after saving').not.toBeVisible({
      timeout: 10_000,
    });
  }

  /** Assert the revision code appears as a cell in the revisions table. */
  async expectRevisionInList(code: string): Promise<void> {
    await expect(
      this.page.getByRole('cell', { name: code }).first(),
      `Revision "${code}" should appear in the Revisions tab table`,
    ).toBeVisible({ timeout: 10_000 });
  }

  /**
   * Assert that no "Add Revision" button is visible (used to verify
   * that creating a revision-of-a-revision is blocked in the UI).
   */
  async expectAddRevisionButtonAbsent(): Promise<void> {
    const btn = this.page.getByRole('button', { name: /new revision|add revision/i });
    const isVisible = await btn.isVisible().catch(() => false);

    if (isVisible) {
      await expect(
        btn,
        'Add Revision button should be disabled on a revision part',
      ).toBeDisabled();
    }
    // If the button is simply absent, the expectation passes implicitly.
  }

  // ── Parameters tab helpers ────────────────────────────────────────────

  /** Click "Add Parameter" in the Parameters tab and fill in the dialog. */
  async addParameter(templateName: string, value: string): Promise<void> {
    await this.page.getByRole('button', { name: /add parameter/i }).click();

    const dialog = this.page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 10_000 });

    // Select the template (searchable select).
    const templateInput = dialog.getByLabel(/template/i);
    await templateInput.fill(templateName);
    const option = this.page.getByRole('option', { name: new RegExp(templateName, 'i') }).first();
    await option.waitFor({ state: 'visible', timeout: 5_000 });
    await option.click();

    await dialog.getByLabel(/value|data/i).fill(value);
    await dialog.getByRole('button', { name: /submit|save/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10_000 });
  }

  /** Assert a parameter row is visible in the Parameters tab. */
  async expectParameterVisible(templateName: string, value: string): Promise<void> {
    await expect(
      this.page.getByRole('cell', { name: templateName }).first(),
      `Parameter "${templateName}" should be listed in the Parameters tab`,
    ).toBeVisible({ timeout: 5_000 });

    await expect(
      this.page.getByRole('cell', { name: value }).first(),
      `Parameter value "${value}" should be listed in the Parameters tab`,
    ).toBeVisible({ timeout: 5_000 });
  }

  // ── Generic locator access ─────────────────────────────────────────────

  /** Returns the currently active tab panel. */
  getTabPanel(): Locator {
    return this.page.getByRole('tabpanel').first();
  }
}
