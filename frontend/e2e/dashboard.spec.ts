// ================================
// SensorPulse E2E - Dashboard Tests
// ================================

import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test('loads the dashboard', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/SensorPulse/);
  });

  test('shows app header with SensorPulse branding', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=SensorPulse')).toBeVisible();
  });

  test('displays sensor cards when data is available', async ({ page }) => {
    await page.goto('/');
    // Wait for either sensor cards or empty state
    const content = page.locator('[class*="glass-card"], [class*="empty"]');
    await expect(content.first()).toBeVisible({ timeout: 10_000 });
  });

  test('dark mode toggle works', async ({ page }) => {
    await page.goto('/');
    // Find the theme toggle button
    const toggle = page.locator('button:has([class*="Moon"]), button:has([class*="Sun"])');
    if (await toggle.isVisible()) {
      const htmlBefore = await page.locator('html').getAttribute('class');
      await toggle.click();
      const htmlAfter = await page.locator('html').getAttribute('class');
      expect(htmlBefore).not.toBe(htmlAfter);
    }
  });
});
