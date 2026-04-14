import { defineConfig, devices } from '@playwright/test';

/**
 * InvenTree UI — Playwright configuration.
 *
 * Auth flow:
 *   1. The "setup" project runs helpers/auth.setup.ts once.
 *   2. It logs in via the Django login form and persists the session
 *      as playwright/.auth/user.json.
 *   3. All spec projects depend on "setup" and consume that storageState,
 *      so every test starts already authenticated.
 *
 * URL assumptions:
 *   InvenTree Platform UI (React SPA) is served at /ui/ by default.
 *   Adjust URLS in helpers/navigation.ts if your deployment differs.
 */
export default defineConfig({
  testDir: './tests',

  // Run tests sequentially — tests share a live InvenTree instance.
  fullyParallel: false,
  workers: 1,

  // Fail the build on CI when test.only is accidentally left in source.
  forbidOnly: !!process.env.CI,

  retries: 1,

  reporter: [['html', { outputFolder: 'playwright-report', open: 'never' }]],

  use: {
    baseURL: 'http://localhost:8000',

    // Record trace on the first retry so failures are diagnosable.
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // Generous timeouts for a Dockerised dev server.
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  projects: [
    // ── Auth setup ─────────────────────────────────────────────────────────
    {
      name: 'setup',
      // Override testDir so Playwright finds auth.setup.ts in helpers/,
      // not in the global testDir (./tests).
      testDir: './helpers',
      testMatch: /auth\.setup\.ts/,
      // No storageState here — this project IS the one that creates it.
    },

    // ── Main test run (Chromium) ────────────────────────────────────────────
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
        viewport: { width: 1440, height: 900 },
      },
      dependencies: ['setup'],
    },
  ],

  outputDir: 'test-results',
});
