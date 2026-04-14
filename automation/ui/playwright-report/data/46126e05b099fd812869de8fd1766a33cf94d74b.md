# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: parts/part-types.spec.ts >> PT-003: create a Assembly part and verify badge on detail page
- Location: tests/parts/part-types.spec.ts:75:7

# Error details

```
TimeoutError: locator.click: Timeout 15000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: /new part|add part|create part/i })

```

# Test source

```ts
  1  | /**
  2  |  * Page Object: Parts list page (/ui/part/).
  3  |  *
  4  |  * Responsibilities:
  5  |  *   - Navigate to the parts list
  6  |  *   - Open the Create Part modal
  7  |  *   - Search / filter the list
  8  |  *   - Assert that a part does or does not appear in the list
  9  |  */
  10 | import { Page, Locator, expect } from '@playwright/test';
  11 | import { navigateToParts } from '../helpers/navigation';
  12 | import { CreatePartModal } from './CreatePartModal';
  13 | 
  14 | export class PartsPage {
  15 |   /**
  16 |    * The "New Part" / "Add Part" / "Create Part" button in the page toolbar.
  17 |    * Matches common label variants across InvenTree versions.
  18 |    */
  19 |   private readonly newPartButton: Locator;
  20 | 
  21 |   constructor(private readonly page: Page) {
  22 |     this.newPartButton = page.getByRole('button', {
  23 |       name: /new part|add part|create part/i,
  24 |     });
  25 |   }
  26 | 
  27 |   /** Navigate to /ui/part/ and wait for the page to settle. */
  28 |   async navigate(): Promise<void> {
  29 |     await navigateToParts(this.page);
  30 |   }
  31 | 
  32 |   /**
  33 |    * Click the New Part button and return the opened modal wrapper.
  34 |    * The caller should use the returned object to fill and submit the form.
  35 |    */
  36 |   async clickNewPart(): Promise<CreatePartModal> {
> 37 |     await this.newPartButton.click();
     |                              ^ TimeoutError: locator.click: Timeout 15000ms exceeded.
  38 |     const modal = new CreatePartModal(this.page);
  39 |     await modal.waitForOpen();
  40 |     return modal;
  41 |   }
  42 | 
  43 |   /**
  44 |    * Type into the search input and wait for the API response that
  45 |    * refreshes the table data.
  46 |    */
  47 |   async searchPart(name: string): Promise<void> {
  48 |     const searchInput = this.page.getByPlaceholder(/search/i).first();
  49 |     await searchInput.fill(name);
  50 |     // Wait for the server round-trip before asserting.
  51 |     await this.page.waitForResponse((resp) =>
  52 |       resp.url().includes('/api/part/') && resp.status() === 200,
  53 |     );
  54 |   }
  55 | 
  56 |   /** Click the part row identified by the given name to open its detail page. */
  57 |   async clickPart(name: string): Promise<void> {
  58 |     await this.page.getByRole('cell', { name }).first().click();
  59 |   }
  60 | 
  61 |   // ── Assertions ─────────────────────────────────────────────────────────
  62 | 
  63 |   async expectPartInList(name: string): Promise<void> {
  64 |     await expect(
  65 |       this.page.getByRole('cell', { name }).first(),
  66 |       `Part "${name}" should appear in the parts list`,
  67 |     ).toBeVisible({ timeout: 10_000 });
  68 |   }
  69 | 
  70 |   async expectPartNotInList(name: string): Promise<void> {
  71 |     await expect(
  72 |       this.page.getByRole('cell', { name }).first(),
  73 |       `Part "${name}" should NOT appear in the parts list`,
  74 |     ).not.toBeVisible({ timeout: 5_000 });
  75 |   }
  76 | }
  77 | 
```