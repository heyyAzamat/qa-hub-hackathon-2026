/**
 * Global authentication setup — runs once before all test projects.
 *
 * Logs in via Django's built-in auth form (/accounts/login/),
 * then persists the session cookie as playwright/.auth/user.json.
 * All spec projects consume that file via storageState in playwright.config.ts.
 *
 * Selector notes:
 *   Django's LoginView renders inputs with id="id_username" / id="id_password".
 *   If your InvenTree deployment uses a custom login template, adjust accordingly.
 */
import { test as setup, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const AUTH_FILE = path.join('playwright', '.auth', 'user.json');

setup('authenticate as admin', async ({ page }) => {
  // Ensure the auth directory exists before we write to it.
  const authDir = path.dirname(AUTH_FILE);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  await page.goto('/accounts/login/');

  // Wait for the form to be ready.
  await page.locator('#id_username').waitFor({ state: 'visible' });

  await page.locator('#id_username').fill('admin');
  await page.locator('#id_password').fill('inventree');

  // Submit — works for both <input type="submit"> and <button type="submit">.
  await page.locator('input[type="submit"], button[type="submit"]').first().click();

  // A successful login redirects away from /accounts/login/.
  await expect(
    page,
    'Login should redirect to the application after successful authentication',
  ).not.toHaveURL(/\/accounts\/login/, { timeout: 15_000 });

  // Persist the authenticated session for all spec projects.
  await page.context().storageState({ path: AUTH_FILE });
});
