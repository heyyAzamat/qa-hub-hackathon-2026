/**
 * Spec: Part Status
 *
 * Covers manual test cases:
 *   ST-001  Set an Active part to Inactive via Edit dialog           (Critical)
 *   ST-002  Inactive part shows correct visual indicator             (Critical)
 *   ST-003  Inactive part cannot be added to a new BOM              (Critical)
 *   ST-004  Reactivate an Inactive part                             (High)
 *
 * Setup strategy:
 *   - beforeEach creates a fresh Active part via API.
 *   - afterEach deletes it via API to ensure isolation.
 */
import { test, expect, APIRequestContext } from '@playwright/test';
import {
  makeApiContext,
  createPartApi,
  createCategoryApi,
  deletePartApi,
  deleteCategoryApi,
  uniqueName,
} from '../../helpers/part.helpers';
import { PartDetailPage } from '../../page-objects/PartDetailPage';

// ── Shared infrastructure ───────────────────────────────────────────────────

let apiCtx: APIRequestContext;
let categoryPk: number;

test.beforeAll(async () => {
  apiCtx = await makeApiContext();
  categoryPk = await createCategoryApi(apiCtx, uniqueName('StatusSpec_Cat'));
});

test.afterAll(async () => {
  await deleteCategoryApi(apiCtx, categoryPk).catch(() => { /* ignore */ });
  await apiCtx.dispose();
});

// ── Per-test part ────────────────────────────────────────────────────────────

let partPk: number;

test.beforeEach(async () => {
  partPk = await createPartApi(apiCtx, {
    name: uniqueName('Status_Part'),
    category: categoryPk,
    active: true,
  });
});

test.afterEach(async () => {
  await deletePartApi(apiCtx, partPk).catch(() => { /* ignore */ });
});

// ── Tests ────────────────────────────────────────────────────────────────────

test('ST-001: set an Active part to Inactive via the Edit dialog', async ({ page }) => {
  const detail = new PartDetailPage(page);
  await detail.navigate(partPk);
  await detail.expectActive();

  await detail.setInactive();

  // The status badge must update without requiring a page reload.
  await detail.expectInactive();
});

test('ST-002: Inactive status is visually indicated on the detail page', async ({ page }) => {
  const detail = new PartDetailPage(page);
  await detail.navigate(partPk);
  await detail.setInactive();

  // Reload to confirm the persisted state is also reflected after reload.
  await page.reload();
  await page.waitForLoadState('domcontentloaded');

  await detail.expectInactive();
});

test('ST-003: Inactive part does not appear as a selectable BOM item', async ({ page }) => {
  // First, make the part inactive via the API for speed.
  await apiCtx.patch(`/api/part/${partPk}/`, { data: { active: false } });

  // Create an Assembly part to test the BOM line-item picker.
  const assemblyPk = await createPartApi(apiCtx, {
    name: uniqueName('Status_Assembly'),
    category: categoryPk,
    assembly: true,
  });

  try {
    const detail = new PartDetailPage(page);
    await detail.navigate(assemblyPk);
    await detail.clickTab('BOM');

    // Open the Add BOM Item dialog via the page object.
    await detail.clickAddBomItem();
    const dialog = page.getByRole('dialog');

    // Search for the inactive part in the part selector.
    const inactivePartData = await apiCtx
      .get(`/api/part/${partPk}/`)
      .then((r) => r.json()) as { name: string };

    const partInput = dialog.getByLabel(/part/i);
    await partInput.fill(inactivePartData.name);

    // The inactive part should not appear as an available option.
    const inactiveOption = page
      .getByRole('option', { name: new RegExp(inactivePartData.name, 'i') })
      .first();

    await expect(
      inactiveOption,
      'Inactive part should not appear as a selectable BOM item',
    ).not.toBeVisible({ timeout: 5_000 });

    // Close the dialog.
    await page.keyboard.press('Escape');
  } finally {
    await deletePartApi(apiCtx, assemblyPk).catch(() => { /* ignore */ });
  }
});

test('ST-004: reactivate an Inactive part', async ({ page }) => {
  // Set the part inactive first via API.
  await apiCtx.patch(`/api/part/${partPk}/`, { data: { active: false } });

  const detail = new PartDetailPage(page);
  await detail.navigate(partPk);
  await detail.expectInactive();

  // Re-enable via the Edit dialog — setActive() asserts the checkbox is
  // unchecked before enabling it, then submits and waits for dialog close.
  await detail.setActive();

  await detail.expectActive();
});
