/**
 * Spec: Part Creation
 *
 * Covers manual test cases:
 *   PC-001  Create part with required fields only                    (Critical / Positive)
 *   PC-002  Create part with all optional fields                     (High / Positive)
 *   PC-003  Verify part appears in the list after creation           (High / Positive)
 *   PC-004  Submit with empty Name → validation error                (Critical / Negative)
 *   PC-005  Submit with duplicate IPN → server error                 (High / Negative)
 *   E2E-001 Create part → add parameter → navigate to category →
 *           verify part appears in category view                     (High / E2E)
 *
 * Setup strategy:
 *   - One shared category is created via API in beforeAll.
 *   - Parts created through the UI are cleaned up via API in afterAll.
 *   - Tests that need a pre-existing IPN create the seed part via API.
 */
import { test, expect, APIRequestContext } from '@playwright/test';
import {
  makeApiContext,
  createPartApi,
  createCategoryApi,
  deleteCategoryApi,
  deletePartApi,
  findPartByNameApi,
  createParameterTemplateApi,
  uniqueName,
} from '../../helpers/part.helpers';
import { PartsPage } from '../../page-objects/PartsPage';
import { PartDetailPage } from '../../page-objects/PartDetailPage';
import { CategoryPage } from '../../page-objects/CategoryPage';

// ── Shared state ────────────────────────────────────────────────────────────

let apiCtx: APIRequestContext;
let sharedCategoryPk: number;
let sharedCategoryName: string;

/** Tracks PKs of parts created through the UI so afterAll can remove them. */
const uiCreatedPartPks: number[] = [];
/** Tracks PKs of parts created through the API seed so afterAll can remove them. */
const apiCreatedPartPks: number[] = [];

test.beforeAll(async () => {
  apiCtx = await makeApiContext();

  sharedCategoryName = uniqueName('CreateSpec_Cat');
  sharedCategoryPk = await createCategoryApi(apiCtx, sharedCategoryName);
});

test.afterAll(async () => {
  for (const pk of [...uiCreatedPartPks, ...apiCreatedPartPks]) {
    await deletePartApi(apiCtx, pk).catch(() => { /* already deleted */ });
  }
  await deleteCategoryApi(apiCtx, sharedCategoryPk).catch(() => { /* already deleted */ });
  await apiCtx.dispose();
});

// ── Helpers ─────────────────────────────────────────────────────────────────

/**
 * After a successful form submission the modal closes.
 * We search the API for the part by name to get its pk.
 */
async function resolveCreatedPartPk(name: string): Promise<number> {
  const pk = await findPartByNameApi(apiCtx, name);
  if (pk === null) throw new Error(`Could not find part "${name}" via API after UI creation`);
  uiCreatedPartPks.push(pk);
  return pk;
}

// ── Tests ────────────────────────────────────────────────────────────────────

test.describe('Part Creation — positive paths', () => {
  test('PC-001: create a part with required fields only', async ({ page }) => {
    const partName = uniqueName('PC001_RequiredOnly');
    const partsPage = new PartsPage(page);

    await partsPage.navigate();
    const modal = await partsPage.clickNewPart();

    await modal.fillName(partName);
    await modal.fillCategory(sharedCategoryName);
    await modal.submit();

    // Modal should close on success.
    await expect(
      page.getByRole('dialog'),
      'Modal should close after successful part creation',
    ).not.toBeVisible({ timeout: 10_000 });

    // Verify the part exists via API.
    const pk = await resolveCreatedPartPk(partName);
    expect(pk, 'Part should have a valid primary key').toBeGreaterThan(0);
  });

  test('PC-002: create a part with all optional fields populated', async ({ page }) => {
    const partName = uniqueName('PC002_AllFields');
    const ipn = `IPN-${Date.now()}`;
    const partsPage = new PartsPage(page);

    await partsPage.navigate();
    const modal = await partsPage.clickNewPart();

    await modal.fill({
      name: partName,
      category: sharedCategoryName,
      ipn,
      description: 'Created by automated test — all optional fields',
      units: 'kg',
      revision: 'A',
      assembly: true,
      component: true,
      trackable: true,
      purchaseable: true,
      saleable: true,
    });
    await modal.submit();

    await expect(
      page.getByRole('dialog'),
      'Modal should close after successful part creation',
    ).not.toBeVisible({ timeout: 10_000 });

    // Navigate to the new part and verify a representative field is shown.
    const pk = await resolveCreatedPartPk(partName);
    const detailPage = new PartDetailPage(page);
    await detailPage.navigate(pk);

    await expect(
      page.getByText(partName),
      'Part name should be visible on the detail page',
    ).toBeVisible();
  });

  test('PC-003: part created via UI appears in the parts list', async ({ page }) => {
    // Create via API so this test solely validates list rendering.
    const partName = uniqueName('PC003_ListCheck');
    const pk = await createPartApi(apiCtx, { name: partName, category: sharedCategoryPk });
    apiCreatedPartPks.push(pk);

    const partsPage = new PartsPage(page);
    await partsPage.navigate();
    await partsPage.searchPart(partName);
    await partsPage.expectPartInList(partName);
  });
});

test.describe('Part Creation — negative paths', () => {
  test('PC-004: submitting with an empty Name shows a validation error', async ({ page }) => {
    const partsPage = new PartsPage(page);
    await partsPage.navigate();
    const modal = await partsPage.clickNewPart();

    // Select category but leave Name blank.
    await modal.fillCategory(sharedCategoryName);
    await modal.submit();

    await modal.expectStillOpen();
    await modal.expectValidationErrors();
  });

  test('PC-005: submitting with a duplicate IPN shows an error', async ({ page }) => {
    const duplicateIPN = `DUP-IPN-${Date.now()}`;

    // Seed: create a part that already holds the IPN.
    const seedPk = await createPartApi(apiCtx, {
      name: uniqueName('PC005_Seed'),
      category: sharedCategoryPk,
      ipn: duplicateIPN,
    });
    apiCreatedPartPks.push(seedPk);

    // Attempt to create a second part with the same IPN.
    const partsPage = new PartsPage(page);
    await partsPage.navigate();
    const modal = await partsPage.clickNewPart();

    await modal.fill({
      name: uniqueName('PC005_Duplicate'),
      category: sharedCategoryName,
      ipn: duplicateIPN,
    });
    await modal.submit();

    // Either the modal stays open with a field error, or an error toast appears.
    await modal.expectErrorMessage(/unique|already exists|duplicate/i);
  });
});

test.describe('E2E: create → parameter → category view', () => {
  test('E2E-001: create part, add a parameter, verify part in category view', async ({ page }) => {
    // ── Arrange ───────────────────────────────────────────────────────────
    const e2eCategoryName = uniqueName('E2E_Cat');
    const e2eCategoryPk = await createCategoryApi(apiCtx, e2eCategoryName);

    // Create the parameter template via API (avoids needing settings access in the UI).
    const templatePk = await createParameterTemplateApi(apiCtx, uniqueName('E2E_Param'), 'Ω');

    const partName = uniqueName('E2E_Part');

    try {
      // ── Act: create part via UI ─────────────────────────────────────────
      const partsPage = new PartsPage(page);
      await partsPage.navigate();
      const modal = await partsPage.clickNewPart();

      await modal.fill({ name: partName, category: e2eCategoryName });
      await modal.submit();

      await expect(
        page.getByRole('dialog'),
        'Create Part modal should close',
      ).not.toBeVisible({ timeout: 10_000 });

      const partPk = await resolveCreatedPartPk(partName);

      // ── Act: navigate to the part and add a parameter ───────────────────
      const detailPage = new PartDetailPage(page);
      await detailPage.navigate(partPk);
      await detailPage.clickTab('Parameters');
      await detailPage.addParameter(
        // The template name we just created.
        (await apiCtx.get(`/api/part/parameter/template/${templatePk}/`).then((r) => r.json()) as { name: string }).name,
        '470',
      );

      // ── Act: navigate to the category and verify the part is listed ─────
      const categoryPage = new CategoryPage(page);
      await categoryPage.navigate(e2eCategoryPk);
      await categoryPage.expectPartInList(partName);
    } finally {
      await deleteCategoryApi(apiCtx, e2eCategoryPk).catch(() => { /* ignore */ });
    }
  });
});
