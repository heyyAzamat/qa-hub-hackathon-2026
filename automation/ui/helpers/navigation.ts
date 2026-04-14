/**
 * Navigation helpers.
 *
 * InvenTree's Platform UI (React SPA) is served under /ui/.
 * If your deployment exposes the SPA at a different prefix, update URLS here —
 * that is the only place that needs changing.
 *
 * Waiting strategy: `waitForLoadState('networkidle')` is unreliable for SPAs
 * because background polling keeps the network active. Instead we use
 * `Promise.all` to race the goto against the first matching API response,
 * which gives us a deterministic "data has arrived" signal and implicitly
 * asserts the HTTP 200 status.
 */
import { Page } from '@playwright/test';

export const URLS = {
  login: '/accounts/login/',
  home: '/ui/',
  parts: '/ui/part/',
  partDetail: (pk: number): string => `/ui/part/${pk}/`,
  category: (pk: number): string => `/ui/part/category/${pk}/`,
} as const;

/** Navigate to the Parts list and wait for the page to settle. */
export async function navigateToParts(page: Page): Promise<void> {
  await Promise.all([
    page.waitForResponse(
      (r) =>
        r.url().includes('/api/part/') &&
        !r.url().includes('/category/') &&
        r.status() === 200,
    ),
    page.goto(URLS.parts),
  ]);
}

/** Navigate directly to a part's detail page by primary key. */
export async function navigateToPartDetail(page: Page, pk: number): Promise<void> {
  await Promise.all([
    page.waitForResponse(
      (r) => r.url().includes(`/api/part/${pk}/`) && r.status() === 200,
    ),
    page.goto(URLS.partDetail(pk)),
  ]);
}

/** Navigate to a part category page by primary key. */
export async function navigateToCategory(page: Page, pk: number): Promise<void> {
  await Promise.all([
    page.waitForResponse(
      (r) => r.url().includes('/api/part/category/') && r.status() === 200,
    ),
    page.goto(URLS.category(pk)),
  ]);
}
