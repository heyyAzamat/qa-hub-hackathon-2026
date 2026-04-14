/**
 * Spec: Part Revisions
 *
 * Covers manual test cases:
 *   REV-001  Create a revision of an existing part                  (High / Positive)
 *   REV-002  Revision appears in the Revisions tab of the base part (High / Positive)
 *   REV-003  Revision code must be unique per base part             (High / Negative)
 *   REV-004  Cannot create a revision of a revision (blocked)       (High / Negative)
 *
 * InvenTree revision model:
 *   - A revision is created by "duplicating" a part from the Revisions tab.
 *   - The duplicated part inherits the base part but gets a distinct
 *     revision code (the `revision` field on the Part model).
 *   - Revision codes must be unique within the same base-part family.
 *   - A revision part cannot itself have further revisions.
 *
 * Setup strategy:
 *   - beforeAll creates a shared category and a base part via API.
 *   - Tests that create revision parts clean up those parts in afterEach.
 *   - The base part and category are cleaned up in afterAll.
 */
import { test, expect, APIRequestContext } from '@playwright/test';
import {
  makeApiContext,
  createPartApi,
  createCategoryApi,
  deletePartApi,
  deleteCategoryApi,
  findPartByNameApi,
  uniqueName,
} from '../../helpers/part.helpers';
import { PartDetailPage } from '../../page-objects/PartDetailPage';

// ── Shared state ────────────────────────────────────────────────────────────

let apiCtx: APIRequestContext;
let categoryPk: number;
let basePartPk: number;

/** Accumulates pks of revision parts created during tests for afterEach cleanup. */
const revisionPartPks: number[] = [];

test.beforeAll(async () => {
  apiCtx = await makeApiContext();

  categoryPk = await createCategoryApi(apiCtx, uniqueName('RevSpec_Cat'));

  basePartPk = await createPartApi(apiCtx, {
    name: uniqueName('RevSpec_BasePart'),
    category: categoryPk,
  });
});

test.afterAll(async () => {
  // Delete any leftover revision parts first (FK safety).
  for (const pk of revisionPartPks) {
    await deletePartApi(apiCtx, pk).catch(() => { /* ignore */ });
  }
  await deletePartApi(apiCtx, basePartPk).catch(() => { /* ignore */ });
  await deleteCategoryApi(apiCtx, categoryPk).catch(() => { /* ignore */ });
  await apiCtx.dispose();
});

// ── Tests ────────────────────────────────────────────────────────────────────

test('REV-001: create a revision of an existing part via the Revisions tab', async ({ page }) => {
  const revisionCode = 'B';

  const detail = new PartDetailPage(page);
  await detail.navigate(basePartPk);
  await detail.clickTab('Revisions');

  await detail.clickAddRevision();
  await detail.submitRevision(revisionCode);

  // Locate the newly created revision part pk for cleanup.
  const basePartData = await apiCtx
    .get(`/api/part/${basePartPk}/`)
    .then((r) => r.json()) as { name: string };

  // The revision part is typically named "<base_name> (Rev <code>)" or similar.
  // We search broadly and filter by the revision field via the API.
  const resp = await apiCtx.get(`/api/part/?revision=${encodeURIComponent(revisionCode)}&limit=50`);
  const data = await resp.json() as { results: Array<{ pk: number; name: string }> };
  const revPart = data.results.find((p) => p.name.includes(basePartData.name));

  expect(
    revPart,
    `A revision part with code "${revisionCode}" should be discoverable via the API after UI creation`,
  ).toBeDefined();

  if (revPart !== undefined) {
    revisionPartPks.push(revPart.pk);
  }
});

test('REV-002: revision appears in the Revisions tab of the base part', async ({ page }) => {
  const revisionCode = 'C';

  const detail = new PartDetailPage(page);
  await detail.navigate(basePartPk);
  await detail.clickTab('Revisions');
  await detail.clickAddRevision();
  await detail.submitRevision(revisionCode);

  // Reload the tab to ensure the list is refreshed.
  await detail.navigate(basePartPk);
  await detail.clickTab('Revisions');

  await detail.expectRevisionInList(revisionCode);

  // Cleanup.
  const resp = await apiCtx.get(`/api/part/?revision=${encodeURIComponent(revisionCode)}&limit=50`);
  const data = await resp.json() as { results: Array<{ pk: number }> };
  if ((data.results[0]?.pk) !== undefined) {
    revisionPartPks.push(data.results[0].pk);
  }
});

test('REV-003: duplicate revision code is rejected with an error', async ({ page }) => {
  const duplicateCode = 'D';

  // Create first revision via API so we can reliably use that code.
  const firstRevPk = await createPartApi(apiCtx, {
    name: uniqueName('RevSpec_RevD'),
    category: categoryPk,
    revision: duplicateCode,
  });
  revisionPartPks.push(firstRevPk);

  // Attempt to create a second revision with the same code via the UI.
  const detail = new PartDetailPage(page);
  await detail.navigate(basePartPk);
  await detail.clickTab('Revisions');
  await detail.clickAddRevision();

  const dialog = page.getByRole('dialog');
  await dialog.getByLabel(/revision/i).fill(duplicateCode);
  await dialog.getByRole('button', { name: /submit|save|create/i }).click();

  // The dialog should stay open and show an error about uniqueness.
  await expect(
    dialog,
    'Dialog should remain open when a duplicate revision code is submitted',
  ).toBeVisible();

  await expect(
    page.getByText(/unique|already exists|duplicate/i).first(),
    'An error about duplicate revision code should be visible',
  ).toBeVisible({ timeout: 5_000 });

  // Dismiss without creating.
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible({ timeout: 5_000 });
});

test('REV-004: cannot create a revision of a revision (UI blocks the action)', async ({ page }) => {
  // Create a revision part via API.
  const revPartPk = await createPartApi(apiCtx, {
    name: uniqueName('RevSpec_RevE'),
    category: categoryPk,
    revision: 'E',
  });
  revisionPartPks.push(revPartPk);

  // Navigate to the revision part's detail page.
  const detail = new PartDetailPage(page);
  await detail.navigate(revPartPk);
  await detail.clickTab('Revisions');

  // The "Add Revision" action should be absent or disabled on a revision part.
  await detail.expectAddRevisionButtonAbsent();
});
