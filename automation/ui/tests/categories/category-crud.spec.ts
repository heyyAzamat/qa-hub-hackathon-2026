/**
 * Spec: Category CRUD
 *
 * Covers manual test cases:
 *   CAT-001  Create a root-level category                           (High / Positive)
 *   CAT-002  Edit a category's name                                 (High / Positive)
 *   CAT-003  Assign a part to a category                            (High / Positive)
 *   CAT-004  Delete an empty category                               (High / Positive)
 *   CAT-005  Delete a category that contains parts — blocked/warned (Medium / Negative)
 *
 * Setup strategy:
 *   - Tests that delete a category create their own disposable category
 *     via API in beforeEach and are responsible for their own cleanup.
 *   - Parts used for CAT-003 / CAT-005 are created via API.
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
import { PartDetailPage } from '../../page-objects/PartDetailPage';
import { navigateToCategory } from '../../helpers/navigation';

// ── Shared state ────────────────────────────────────────────────────────────

let apiCtx: APIRequestContext;

test.beforeAll(async () => {
  apiCtx = await makeApiContext();
});

test.afterAll(async () => {
  await apiCtx.dispose();
});

// ── Tests ────────────────────────────────────────────────────────────────────

test('CAT-001: create a root-level category via the UI', async ({ page }) => {
  const newCatName = uniqueName('CAT001_RootCat');
  let newCategoryPk: number | null = null;

  try {
    // Navigate to the parts categories page (root).
    await navigateToCategory(page, 0); // pk=0 typically shows the root view

    const categoryPage = new CategoryPage(page);
    await categoryPage.clickNewCategory();
    await categoryPage.fillCategoryName(newCatName);
    await categoryPage.submitDialog();

    // Verify the new category appears in the list.
    await categoryPage.expectSubCategoryInList(newCatName);

    // Resolve pk for cleanup.
    const resp = await apiCtx.get(`/api/part/category/?name=${encodeURIComponent(newCatName)}`);
    const data = await resp.json() as { results: Array<{ pk: number }> };
    newCategoryPk = data.results[0]?.pk ?? null;
  } finally {
    if (newCategoryPk !== null) {
      await deleteCategoryApi(apiCtx, newCategoryPk).catch(() => { /* ignore */ });
    }
  }
});

test('CAT-002: edit a category name', async ({ page }) => {
  const originalName = uniqueName('CAT002_Original');
  const updatedName = uniqueName('CAT002_Updated');
  const catPk = await createCategoryApi(apiCtx, originalName);

  try {
    const categoryPage = new CategoryPage(page);
    await categoryPage.navigate(catPk);
    await categoryPage.expectCategoryTitle(originalName);

    await categoryPage.clickEditCategory();
    await categoryPage.fillCategoryName(updatedName);
    await categoryPage.submitDialog();

    // After save the page heading should reflect the new name.
    await categoryPage.expectCategoryTitle(updatedName);
  } finally {
    await deleteCategoryApi(apiCtx, catPk).catch(() => { /* ignore */ });
  }
});

test('CAT-003: assign a part to a category', async ({ page }) => {
  // Create source and target categories.
  const sourcePk = await createCategoryApi(apiCtx, uniqueName('CAT003_Source'));
  const targetPk = await createCategoryApi(apiCtx, uniqueName('CAT003_Target'));

  // Create a part in the source category.
  const partName = uniqueName('CAT003_Part');
  const partPk = await createPartApi(apiCtx, { name: partName, category: sourcePk });

  try {
    // Navigate to the part detail and move it to the target category via Edit.
    const detail = new PartDetailPage(page);
    await detail.navigate(partPk);
    await detail.clickEditPart();

    const dialog = page.getByRole('dialog');
    const categoryInput = dialog.getByLabel(/category/i);

    // Fetch target category name to type into the autocomplete.
    const catResp = await apiCtx.get(`/api/part/category/${targetPk}/`);
    const catData = await catResp.json() as { name: string };

    await categoryInput.clear();
    await categoryInput.fill(catData.name);

    const option = page.getByRole('option', { name: new RegExp(catData.name, 'i') }).first();
    await option.waitFor({ state: 'visible', timeout: 5_000 });
    await option.click();

    await dialog.getByRole('button', { name: /submit|save/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10_000 });

    // Verify the part now appears in the target category.
    const catPage = new CategoryPage(page);
    await catPage.navigate(targetPk);
    await catPage.expectPartInList(partName);
  } finally {
    await deletePartApi(apiCtx, partPk).catch(() => { /* ignore */ });
    await deleteCategoryApi(apiCtx, sourcePk).catch(() => { /* ignore */ });
    await deleteCategoryApi(apiCtx, targetPk).catch(() => { /* ignore */ });
  }
});

test('CAT-004: delete an empty category', async ({ page }) => {
  const catName = uniqueName('CAT004_Empty');
  const catPk = await createCategoryApi(apiCtx, catName);

  const categoryPage = new CategoryPage(page);
  await categoryPage.navigate(catPk);

  await categoryPage.clickDeleteCategory();
  await categoryPage.confirmDelete();

  // After deletion the category should no longer be accessible.
  const resp = await apiCtx.get(`/api/part/category/${catPk}/`);
  expect(
    resp.status(),
    'Deleted category should return 404 from the API',
  ).toBe(404);
});

test('CAT-005: deleting a category that contains parts shows a warning', async ({ page }) => {
  const catName = uniqueName('CAT005_WithParts');
  const catPk = await createCategoryApi(apiCtx, catName);
  const partPk = await createPartApi(apiCtx, { name: uniqueName('CAT005_Part'), category: catPk });

  try {
    const categoryPage = new CategoryPage(page);
    await categoryPage.navigate(catPk);

    await categoryPage.clickDeleteCategory();

    // The system must either block the delete or show a prominent warning.
    await categoryPage.expectDeleteBlockedOrWarned();
  } finally {
    await deletePartApi(apiCtx, partPk).catch(() => { /* ignore */ });
    await deleteCategoryApi(apiCtx, catPk).catch(() => { /* ignore */ });
  }
});
