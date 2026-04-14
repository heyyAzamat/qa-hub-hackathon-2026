# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: parts/part-detail-tabs.spec.ts >> Part detail tabs — rendering >> DV-002: BOM tab is visible and renders for an Assembly part
- Location: tests/parts/part-detail-tabs.spec.ts:91:7

# Error details

```
Error: Tab "BOM" should be present in the tab bar

expect(locator).toBeVisible() failed

Locator: getByRole('tab', { name: /BOM/i })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Tab "BOM" should be present in the tab bar with timeout 5000ms
  - waiting for getByRole('tab', { name: /BOM/i })

```

# Test source

```ts
  1   | /**
  2   |  * Page Object: Part detail page (/ui/part/{pk}/).
  3   |  *
  4   |  * InvenTree Platform UI renders the detail view as a tabbed panel
  5   |  * using Mantine's <Tabs> component, which produces role="tab" elements.
  6   |  * Tab panels have role="tabpanel".
  7   |  *
  8   |  * Tab visibility rules (from InvenTree docs):
  9   |  *   BOM         — only visible when part.assembly = true
  10  |  *   Variants    — only visible when part.is_template = true
  11  |  *   Test Templates — only visible when part.trackable = true
  12  |  */
  13  | import { Page, Locator, expect } from '@playwright/test';
  14  | import { navigateToPartDetail } from '../helpers/navigation';
  15  | 
  16  | /** All known tabs in InvenTree's part detail view. */
  17  | export type TabName =
  18  |   | 'Details'
  19  |   | 'Stock'
  20  |   | 'BOM'
  21  |   | 'Allocated'
  22  |   | 'Build Orders'
  23  |   | 'Parameters'
  24  |   | 'Variants'
  25  |   | 'Revisions'
  26  |   | 'Attachments'
  27  |   | 'Related Parts'
  28  |   | 'Test Templates';
  29  | 
  30  | export class PartDetailPage {
  31  |   constructor(private readonly page: Page) {}
  32  | 
  33  |   /** Navigate to /ui/part/{pk}/ and wait for the page to be ready. */
  34  |   async navigate(pk: number): Promise<void> {
  35  |     await navigateToPartDetail(this.page, pk);
  36  |   }
  37  | 
  38  |   // ── Tab navigation ─────────────────────────────────────────────────────
  39  | 
  40  |   /**
  41  |    * Click the tab with the given name and assert the tab panel renders.
  42  |    * Uses a regex match so minor label changes ("Build Orders" vs "Builds") are tolerated.
  43  |    */
  44  |   async clickTab(tabName: TabName): Promise<void> {
  45  |     const tab = this.page.getByRole('tab', { name: new RegExp(tabName, 'i') });
  46  |     await tab.waitFor({ state: 'visible', timeout: 5_000 });
  47  |     await tab.click();
  48  | 
  49  |     await expect(
  50  |       this.page.getByRole('tabpanel').first(),
  51  |       `Tab panel for "${tabName}" should be visible after clicking the tab`,
  52  |     ).toBeVisible({ timeout: 10_000 });
  53  |   }
  54  | 
  55  |   /** Assert that a tab with the given name exists in the tab list. */
  56  |   async expectTabVisible(tabName: TabName): Promise<void> {
  57  |     await expect(
  58  |       this.page.getByRole('tab', { name: new RegExp(tabName, 'i') }),
  59  |       `Tab "${tabName}" should be present in the tab bar`,
> 60  |     ).toBeVisible({ timeout: 5_000 });
      |       ^ Error: Tab "BOM" should be present in the tab bar
  61  |   }
  62  | 
  63  |   /** Assert that a tab is NOT present (e.g. BOM on a non-Assembly part). */
  64  |   async expectTabHidden(tabName: TabName): Promise<void> {
  65  |     await expect(
  66  |       this.page.getByRole('tab', { name: new RegExp(tabName, 'i') }),
  67  |       `Tab "${tabName}" should NOT be present on this part`,
  68  |     ).not.toBeVisible({ timeout: 5_000 });
  69  |   }
  70  | 
  71  |   // ── Status ─────────────────────────────────────────────────────────────
  72  | 
  73  |   async expectActive(): Promise<void> {
  74  |     await expect(
  75  |       this.page.getByText(/\bactive\b/i).first(),
  76  |       'Part detail page should show Active status',
  77  |     ).toBeVisible({ timeout: 5_000 });
  78  |   }
  79  | 
  80  |   async expectInactive(): Promise<void> {
  81  |     await expect(
  82  |       this.page.getByText(/\binactive\b/i).first(),
  83  |       'Part detail page should show Inactive status',
  84  |     ).toBeVisible({ timeout: 5_000 });
  85  |   }
  86  | 
  87  |   // ── Type badges ────────────────────────────────────────────────────────
  88  | 
  89  |   /**
  90  |    * Assert that a type badge or label for the given type is visible.
  91  |    * InvenTree renders type flags as coloured badges near the part header.
  92  |    */
  93  |   async expectTypeBadge(type: string): Promise<void> {
  94  |     await expect(
  95  |       this.page.getByText(new RegExp(`\\b${type}\\b`, 'i')).first(),
  96  |       `Part detail page should display a "${type}" badge or label`,
  97  |     ).toBeVisible({ timeout: 5_000 });
  98  |   }
  99  | 
  100 |   // ── Edit actions ───────────────────────────────────────────────────────
  101 | 
  102 |   /** Open the Edit Part dialog. */
  103 |   async clickEditPart(): Promise<void> {
  104 |     await this.page
  105 |       .getByRole('button', { name: /^edit( part)?$/i })
  106 |       .first()
  107 |       .click();
  108 | 
  109 |     await expect(
  110 |       this.page.getByRole('dialog'),
  111 |       'Edit Part dialog should open',
  112 |     ).toBeVisible({ timeout: 10_000 });
  113 |   }
  114 | 
  115 |   /**
  116 |    * Toggle the Active checkbox off via the Edit dialog, then submit.
  117 |    * Leaves the dialog closed on exit.
  118 |    */
  119 |   async setInactive(): Promise<void> {
  120 |     await this.clickEditPart();
  121 | 
  122 |     const dialog = this.page.getByRole('dialog');
  123 |     const activeCheckbox = dialog.getByRole('checkbox', { name: /active/i });
  124 |     if (await activeCheckbox.isChecked()) {
  125 |       await activeCheckbox.uncheck();
  126 |     }
  127 | 
  128 |     await dialog.getByRole('button', { name: /submit|save/i }).click();
  129 |     await expect(dialog, 'Edit dialog should close after saving').not.toBeVisible({
  130 |       timeout: 10_000,
  131 |     });
  132 |   }
  133 | 
  134 |   /**
  135 |    * Toggle the Active checkbox on via the Edit dialog, then submit.
  136 |    * Asserts the checkbox is unchecked before enabling it.
  137 |    * Leaves the dialog closed on exit.
  138 |    */
  139 |   async setActive(): Promise<void> {
  140 |     await this.clickEditPart();
  141 | 
  142 |     const dialog = this.page.getByRole('dialog');
  143 |     const activeCheckbox = dialog.getByRole('checkbox', { name: /active/i });
  144 | 
  145 |     await expect(
  146 |       activeCheckbox,
  147 |       'Active checkbox should be unchecked before re-enabling the part',
  148 |     ).not.toBeChecked();
  149 |     await activeCheckbox.check();
  150 | 
  151 |     await dialog.getByRole('button', { name: /submit|save/i }).click();
  152 |     await expect(dialog, 'Edit dialog should close after saving').not.toBeVisible({
  153 |       timeout: 10_000,
  154 |     });
  155 |   }
  156 | 
  157 |   /**
  158 |    * Open the Add BOM Item dialog from the BOM tab.
  159 |    * Call after `clickTab('BOM')`.
  160 |    */
```