/**
 * Spec: Part Types
 *
 * Covers manual test cases:
 *   PT-001  Virtual part — badge visible on detail page             (High)
 *   PT-002  Template part — badge visible                           (High)
 *   PT-003  Assembly part — badge visible + BOM tab present         (Critical)
 *   PT-004  Component part — badge visible                          (High)
 *   PT-005  Trackable part — badge visible + Test Templates tab     (High)
 *   PT-006  Purchaseable part — badge visible                       (High)
 *   PT-007  Saleable part — badge visible                           (High)
 *
 * Strategy:
 *   Each part is created through the UI form so the form interaction itself
 *   is validated. Parts are cleaned up via API in afterAll.
 */
import { test, expect, APIRequestContext } from '@playwright/test';
import {
  makeApiContext,
  createCategoryApi,
  deleteCategoryApi,
  deletePartApi,
  findPartByNameApi,
  uniqueName,
} from '../../helpers/part.helpers';
import { PartsPage } from '../../page-objects/PartsPage';
import { PartDetailPage, TabName } from '../../page-objects/PartDetailPage';

// ── Shared state ────────────────────────────────────────────────────────────

let apiCtx: APIRequestContext;
let categoryPk: number;
let categoryName: string;
const createdPartPks: number[] = [];

test.beforeAll(async () => {
  apiCtx = await makeApiContext();
  categoryName = uniqueName('TypesSpec_Cat');
  categoryPk = await createCategoryApi(apiCtx, categoryName);
});

test.afterAll(async () => {
  for (const pk of createdPartPks) {
    await deletePartApi(apiCtx, pk).catch(() => { /* ignore */ });
  }
  await deleteCategoryApi(apiCtx, categoryPk).catch(() => { /* ignore */ });
  await apiCtx.dispose();
});

// ── Helper ───────────────────────────────────────────────────────────────────

interface TypeTestCase {
  id: string;
  type: string;
  formFlag: 'virtual' | 'template' | 'assembly' | 'component' | 'trackable' | 'purchaseable' | 'saleable';
  /** Extra tab that must be visible as a result of this type. Optional. */
  expectedTab?: TabName;
  /** Badge / label text to look for on the detail page. */
  badgeText: string;
}

const TYPE_CASES: TypeTestCase[] = [
  { id: 'PT-001', type: 'Virtual',      formFlag: 'virtual',      badgeText: 'Virtual' },
  { id: 'PT-002', type: 'Template',     formFlag: 'template',     badgeText: 'Template',   expectedTab: 'Variants' },
  { id: 'PT-003', type: 'Assembly',     formFlag: 'assembly',     badgeText: 'Assembly',   expectedTab: 'BOM' },
  { id: 'PT-004', type: 'Component',    formFlag: 'component',    badgeText: 'Component' },
  { id: 'PT-005', type: 'Trackable',    formFlag: 'trackable',    badgeText: 'Trackable',  expectedTab: 'Test Templates' },
  { id: 'PT-006', type: 'Purchaseable', formFlag: 'purchaseable', badgeText: 'Purchaseable' },
  { id: 'PT-007', type: 'Saleable',     formFlag: 'saleable',     badgeText: 'Saleable' },
];

// ── Tests ────────────────────────────────────────────────────────────────────

for (const tc of TYPE_CASES) {
  test(`${tc.id}: create a ${tc.type} part and verify badge on detail page`, async ({ page }) => {
    const partName = uniqueName(`${tc.id}_${tc.type}`);

    // ── Arrange / Act: create via UI ─────────────────────────────────────
    const partsPage = new PartsPage(page);
    await partsPage.navigate();
    const modal = await partsPage.clickNewPart();

    await modal.fill({
      name: partName,
      category: categoryName,
      [tc.formFlag]: true,
    });
    await modal.submit();

    await expect(
      page.getByRole('dialog'),
      `Create Part modal should close after creating ${tc.type} part`,
    ).not.toBeVisible({ timeout: 10_000 });

    // Resolve pk so we can navigate and clean up.
    const pk = await findPartByNameApi(apiCtx, partName);
    expect(pk, `Part "${partName}" should be findable via API after UI creation`).not.toBeNull();
    createdPartPks.push(pk!);

    // ── Assert: detail page shows the correct badge ───────────────────────
    const detailPage = new PartDetailPage(page);
    await detailPage.navigate(pk!);
    await detailPage.expectTypeBadge(tc.badgeText);

    // ── Assert: type-specific tab is present ─────────────────────────────
    if (tc.expectedTab !== undefined) {
      await detailPage.expectTabVisible(tc.expectedTab);
    }
  });
}
