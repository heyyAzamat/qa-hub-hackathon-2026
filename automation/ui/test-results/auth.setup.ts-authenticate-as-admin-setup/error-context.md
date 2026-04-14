# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ..\helpers\auth.setup.ts >> authenticate as admin
- Location: helpers\auth.setup.ts:18:6

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8000/accounts/login/
Call log:
  - navigating to "http://localhost:8000/accounts/login/", waiting until "load"

```

# Test source

```ts
  1  | /**
  2  |  * Global authentication setup — runs once before all test projects.
  3  |  *
  4  |  * Logs in via Django's built-in auth form (/accounts/login/),
  5  |  * then persists the session cookie as playwright/.auth/user.json.
  6  |  * All spec projects consume that file via storageState in playwright.config.ts.
  7  |  *
  8  |  * Selector notes:
  9  |  *   Django's LoginView renders inputs with id="id_username" / id="id_password".
  10 |  *   If your InvenTree deployment uses a custom login template, adjust accordingly.
  11 |  */
  12 | import { test as setup, expect } from '@playwright/test';
  13 | import * as fs from 'fs';
  14 | import * as path from 'path';
  15 | 
  16 | const AUTH_FILE = path.join('playwright', '.auth', 'user.json');
  17 | 
  18 | setup('authenticate as admin', async ({ page }) => {
  19 |   // Ensure the auth directory exists before we write to it.
  20 |   const authDir = path.dirname(AUTH_FILE);
  21 |   if (!fs.existsSync(authDir)) {
  22 |     fs.mkdirSync(authDir, { recursive: true });
  23 |   }
  24 | 
> 25 |   await page.goto('/accounts/login/');
     |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8000/accounts/login/
  26 | 
  27 |   // Wait for the form to be ready.
  28 |   await page.locator('#id_username').waitFor({ state: 'visible' });
  29 | 
  30 |   await page.locator('#id_username').fill('admin');
  31 |   await page.locator('#id_password').fill('inventree');
  32 | 
  33 |   // Submit — works for both <input type="submit"> and <button type="submit">.
  34 |   await page.locator('input[type="submit"], button[type="submit"]').first().click();
  35 | 
  36 |   // A successful login redirects away from /accounts/login/.
  37 |   await expect(
  38 |     page,
  39 |     'Login should redirect to the application after successful authentication',
  40 |   ).not.toHaveURL(/\/accounts\/login/, { timeout: 15_000 });
  41 | 
  42 |   // Persist the authenticated session for all spec projects.
  43 |   await page.context().storageState({ path: AUTH_FILE });
  44 | });
  45 | 
```