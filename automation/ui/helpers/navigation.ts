/**
 * Navigation helpers.
 *
 * InvenTree's Platform UI (React SPA) is served under /ui/.
 * If your deployment exposes the SPA at a different prefix, update URLS here.
 *
 * Waiting strategy: goto + waitForURL confirms the React router accepted the
 * route. For SPAs, waitForResponse can race with the initial page load, so we
 * rely on URL confirmation + a short networkidle window instead.
 */
import { Page } from '@playwright/test';

export const URLS = {
  login: '/web/',
  home: '/web/',
  parts: '/web/part/',
  partDetail: (pk: number): string => `/web/part/${pk}/`,
  category: (pk: number): string => `/web/part/category/${pk}/`,
} as const;

/** Navigate to the Parts list and wait for the page to settle. */
export async function navigateToParts(page: Page): Promise<void> {
  await page.goto(URLS.parts);
  await page.waitForURL('**/web/part/**', { timeout: 30_000 });
  await page.waitForLoadState('domcontentloaded');
}

/** Navigate directly to a part's detail page by primary key. */
export async function navigateToPartDetail(page: Page, pk: number): Promise<void> {
  await page.goto(URLS.partDetail(pk));
  await page.waitForURL(`**/web/part/${pk}/**`, { timeout: 30_000 });
  await page.waitForLoadState('domcontentloaded');
}

/** Navigate to a part category page by primary key. */
export async function navigateToCategory(page: Page, pk: number): Promise<void> {
  if (pk === 0) {
    await page.goto(URLS.parts);
    await page.waitForURL('**/web/part/**', { timeout: 30_000 });
  } else {
    await page.goto(URLS.category(pk));
    await page.waitForURL(`**/web/part/category/${pk}/**`, { timeout: 30_000 });
  }
  await page.waitForLoadState('domcontentloaded');
}
