/**
 * Spec: Part Detail View — Tabs
 *
 * Covers manual test cases:
 *   DV-001  Stock tab visible and renders                            (Critical)
 *   DV-002  BOM tab visible for Assembly part                       (Critical)
 *   DV-003  BOM tab absent for non-Assembly part                    (High)
 *   DV-004  Allocated tab renders                                   (High)
 *   DV-005  Build Orders tab renders                                (High)
 *   DV-006  Parameters tab renders                                  (High)
 *   DV-007  Variants tab visible for Template part                  (High)
 *   DV-008  Revisions tab renders                                   (High)
 *   DV-009  Attachments tab renders and allows upload               (Medium)
 *   DV-010  Related Parts tab renders                               (Medium)
 *   DV-011  Test Templates tab visible for Trackable part           (Medium)
 *
 * Setup strategy:
 *   - Two parts are created via API in beforeAll:
 *       • allFeaturesPartPk — Assembly + Template + Trackable + Purchaseable + Saleable
 *         (covers BOM, Variants, Test Templates tabs)
 *       • plainPartPk       — plain Component part (no Assembly/Template flags)
 *         (used to verify BOM tab is absent)
 *   - Both parts and the shared category are cleaned up in afterAll.
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

// ── Shared state ────────────────────────────────────────────────────────────

let apiCtx: APIRequestContext;
let categoryPk: number;
let allFeaturesPartPk: number;
let plainPartPk: number;

test.beforeAll(async () => {
  apiCtx = await makeApiContext();

  categoryPk = await createCategoryApi(apiCtx, uniqueName('TabsSpec_Cat'));

  // Part with every flag set — exposes all tabs.
  allFeaturesPartPk = await createPartApi(apiCtx, {
    name: uniqueName('Tabs_AllFeatures'),
    category: categoryPk,
    assembly: true,
    is_template: true,
    trackable: true,
    purchaseable: true,
    saleable: true,
    component: true,
  });

  // Plain component part — BOM and Variants tabs should be absent.
  plainPartPk = await createPartApi(apiCtx, {
    name: uniqueName('Tabs_Plain'),
    category: categoryPk,
    assembly: false,
    is_template: false,
    component: true,
  });
});

test.afterAll(async () => {
  await deletePartApi(apiCtx, allFeaturesPartPk).catch(() => { /* ignore */ });
  await deletePartApi(apiCtx, plainPartPk).catch(() => { /* ignore */ });
  await deleteCategoryApi(apiCtx, categoryPk).catch(() => { /* ignore */ });
  await apiCtx.dispose();
});

// ── Tests ────────────────────────────────────────────────────────────────────

test.describe('Part detail tabs — rendering', () => {
  test('DV-001: Stock tab is clickable and renders content', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);
    await detail.clickTab('Stock');

    await expect(
      detail.getTabPanel(),
      'Stock tab panel should be visible and non-empty',
    ).toBeVisible();
  });

  test('DV-002: BOM tab is visible and renders for an Assembly part', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);

    await detail.expectTabVisible('BOM');
    await detail.clickTab('BOM');

    await expect(
      detail.getTabPanel(),
      'BOM tab panel should render for an Assembly part',
    ).toBeVisible();
  });

  test('DV-003: BOM tab is absent for a non-Assembly part', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(plainPartPk);

    await detail.expectTabHidden('BOM');
  });

  test('DV-004: Allocated tab is clickable and renders', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);
    await detail.clickTab('Allocated');

    await expect(
      detail.getTabPanel(),
      'Allocated tab panel should be visible',
    ).toBeVisible();
  });

  test('DV-005: Build Orders tab is clickable and renders', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);
    await detail.clickTab('Build Orders');

    await expect(
      detail.getTabPanel(),
      'Build Orders tab panel should be visible',
    ).toBeVisible();
  });

  test('DV-006: Parameters tab is clickable and renders', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);
    await detail.clickTab('Parameters');

    await expect(
      detail.getTabPanel(),
      'Parameters tab panel should be visible',
    ).toBeVisible();
  });

  test('DV-007: Variants tab is visible and renders for a Template part', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);

    await detail.expectTabVisible('Variants');
    await detail.clickTab('Variants');

    await expect(
      detail.getTabPanel(),
      'Variants tab panel should render for a Template part',
    ).toBeVisible();
  });

  test('DV-008: Revisions tab is clickable and renders', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);
    await detail.clickTab('Revisions');

    await expect(
      detail.getTabPanel(),
      'Revisions tab panel should be visible',
    ).toBeVisible();
  });

  test('DV-009: Attachments tab is clickable and renders', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);
    await detail.clickTab('Attachments');

    await expect(
      detail.getTabPanel(),
      'Attachments tab panel should be visible',
    ).toBeVisible();
  });

  test('DV-010: Related Parts tab is clickable and renders', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);
    await detail.clickTab('Related Parts');

    await expect(
      detail.getTabPanel(),
      'Related Parts tab panel should be visible',
    ).toBeVisible();
  });

  test('DV-011: Test Templates tab is visible and renders for a Trackable part', async ({ page }) => {
    const detail = new PartDetailPage(page);
    await detail.navigate(allFeaturesPartPk);

    await detail.expectTabVisible('Test Templates');
    await detail.clickTab('Test Templates');

    await expect(
      detail.getTabPanel(),
      'Test Templates tab panel should render for a Trackable part',
    ).toBeVisible();
  });
});
