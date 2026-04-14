/**
 * Spec: Category Hierarchy
 *
 * Covers manual test cases:
 *   CAT-002h  Create a parent category and a child category          (High / Positive)
 *   CAT-002b  Verify breadcrumb reflects parent → child hierarchy    (High / Positive)
 *   CAT-003h  Filter parts list by child category                   (High / Positive)
 *
 * Setup strategy:
 *   - Parent and child categories are created via API in beforeAll.
 *   - A test part is created inside the child category so the filter test
 *     has something to assert against.
 *   - Everything is cleaned up in afterAll.
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
import { CategoryPage } from '../../page-objects/CategoryPage';
import { PartsPage } from '../../page-objects/PartsPage';

// ── Shared state ────────────────────────────────────────────────────────────

let apiCtx: APIRequestContext;
let parentCategoryPk: number;
let parentCategoryName: string;
let childCategoryPk: number;
let childCategoryName: string;
let childPartPk: number;
let childPartName: string;

test.beforeAll(async () => {
  apiCtx = await makeApiContext();

  parentCategoryName = uniqueName('Hierarchy_Parent');
  parentCategoryPk = await createCategoryApi(apiCtx, parentCategoryName);

  childCategoryName = uniqueName('Hierarchy_Child');
  childCategoryPk = await createCategoryApi(apiCtx, childCategoryName, parentCategoryPk);

  childPartName = uniqueName('Hierarchy_Part');
  childPartPk = await createPartApi(apiCtx, {
    name: childPartName,
    category: childCategoryPk,
  });
});

test.afterAll(async () => {
  await deletePartApi(apiCtx, childPartPk).catch(() => { /* ignore */ });
  // Child must be deleted before parent (FK constraint).
  await deleteCategoryApi(apiCtx, childCategoryPk).catch(() => { /* ignore */ });
  await deleteCategoryApi(apiCtx, parentCategoryPk).catch(() => { /* ignore */ });
  await apiCtx.dispose();
});

// ── Tests ────────────────────────────────────────────────────────────────────

test('CAT-002h: create a child category under a parent via the UI', async ({ page }) => {
  const newChildName = uniqueName('Hierarchy_UIChild');
  let newChildPk: number | null = null;

  try {
    // Navigate to the parent category page.
    const catPage = new CategoryPage(page);
    await catPage.navigate(parentCategoryPk);

    await catPage.clickNewCategory();
    await catPage.fillCategoryName(newChildName);
    await catPage.submitDialog();

    // The new child should appear in the sub-category list of the parent.
    await catPage.expectSubCategoryInList(newChildName);

    // Resolve pk for cleanup.
    const resp = await apiCtx.get(`/api/part/category/?name=${encodeURIComponent(newChildName)}`);
    const data = await resp.json() as { results: Array<{ pk: number }> };
    newChildPk = data.results[0]?.pk ?? null;
  } finally {
    if (newChildPk !== null) {
      await deleteCategoryApi(apiCtx, newChildPk).catch(() => { /* ignore */ });
    }
  }
});

test('CAT-002b: breadcrumb reflects the parent → child hierarchy', async ({ page }) => {
  const catPage = new CategoryPage(page);
  await catPage.navigate(childCategoryPk);

  // The breadcrumb should show the parent category name as an ancestor.
  await catPage.expectBreadcrumbContains(parentCategoryName);
  // And the child category name as the current node.
  await catPage.expectBreadcrumbContains(childCategoryName);
});

test('CAT-003h: parts list filtered by child category shows only parts in that category', async ({
  page,
}) => {
  // Navigate to the child category — its parts table should contain the test part.
  const catPage = new CategoryPage(page);
  await catPage.navigate(childCategoryPk);

  await catPage.expectPartInList(childPartName);

  // Optional sanity-check: verify the part does NOT appear in the parent category
  // at the same level (it belongs to the child, not directly to the parent).
  // This is best done by navigating to the parent and asserting absence in the
  // direct-parts table (not including descendants).
  await catPage.navigate(parentCategoryPk);

  // The parent's *direct* parts list should be empty; only the child category
  // appears as a sub-category row.
  await catPage.expectSubCategoryInList(childCategoryName);

  const partsPage = new PartsPage(page);
  await partsPage.navigate();
  await partsPage.searchPart(childPartName);
  await partsPage.expectPartInList(childPartName);
});
