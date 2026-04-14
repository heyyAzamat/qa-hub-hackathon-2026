/**
 * Global authentication setup — runs once before all test projects.
 *
 * InvenTree Platform UI (React/Mantine) serves the login page at /ui/.
 * Form fields use placeholder text, not Django's #id_username selectors.
 *
 * Persists the session as playwright/.auth/user.json so all spec projects
 * start already authenticated.
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

  // InvenTree React SPA — navigating to /web/ redirects to the login page.
  await page.goto('/web/');

  // Wait for the React login form to render.
  await page.getByPlaceholder('Your username').waitFor({ state: 'visible', timeout: 30_000 });

  await page.getByPlaceholder('Your username').fill('admin');
  await page.getByPlaceholder('Your password').fill('inventree');

  await page.getByRole('button', { name: /log in/i }).click();

  // Successful login redirects to the dashboard (/ui/dashboard or similar).
  await expect(
    page,
    'Login should redirect away from the login page',
  ).not.toHaveURL(/\/login/, { timeout: 15_000 });

  // Persist the authenticated session for all spec projects.
  await page.context().storageState({ path: AUTH_FILE });
});
