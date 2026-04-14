/**
 * Page Object: Parts list page (/ui/part/).
 *
 * Responsibilities:
 *   - Navigate to the parts list
 *   - Open the Create Part modal
 *   - Search / filter the list
 *   - Assert that a part does or does not appear in the list
 */
import { Page, Locator, expect } from '@playwright/test';
import { navigateToParts } from '../helpers/navigation';
import { CreatePartModal } from './CreatePartModal';

export class PartsPage {
  /**
   * The "New Part" / "Add Part" / "Create Part" button in the page toolbar.
   * Matches common label variants across InvenTree versions.
   */
  private readonly newPartButton: Locator;

  constructor(private readonly page: Page) {
    this.newPartButton = page.getByRole('button', {
      name: /new part|add part|create part/i,
    });
  }

  /** Navigate to /ui/part/ and wait for the page to settle. */
  async navigate(): Promise<void> {
    await navigateToParts(this.page);
  }

  /**
   * Click the New Part button and return the opened modal wrapper.
   * The caller should use the returned object to fill and submit the form.
   */
  async clickNewPart(): Promise<CreatePartModal> {
    await this.newPartButton.click();
    const modal = new CreatePartModal(this.page);
    await modal.waitForOpen();
    return modal;
  }

  /**
   * Type into the search input and wait for the API response that
   * refreshes the table data.
   */
  async searchPart(name: string): Promise<void> {
    const searchInput = this.page.getByPlaceholder(/search/i).first();
    await searchInput.fill(name);
    // Wait for the server round-trip before asserting.
    await this.page.waitForResponse((resp) =>
      resp.url().includes('/api/part/') && resp.status() === 200,
    );
  }

  /** Click the part row identified by the given name to open its detail page. */
  async clickPart(name: string): Promise<void> {
    await this.page.getByRole('cell', { name }).first().click();
  }

  // ── Assertions ─────────────────────────────────────────────────────────

  async expectPartInList(name: string): Promise<void> {
    await expect(
      this.page.getByRole('cell', { name }).first(),
      `Part "${name}" should appear in the parts list`,
    ).toBeVisible({ timeout: 10_000 });
  }

  async expectPartNotInList(name: string): Promise<void> {
    await expect(
      this.page.getByRole('cell', { name }).first(),
      `Part "${name}" should NOT appear in the parts list`,
    ).not.toBeVisible({ timeout: 5_000 });
  }
}
