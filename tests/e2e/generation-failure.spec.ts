import { projectCreation } from './helpers';
import { test, expect } from '@playwright/test';
import { signInLocal } from './helpers';

for (const [code, message] of [
  ['incomplete_response', 'The provider did not finish its response.'],
  ['generation_failed', 'its specific cause was not recorded'],
]) {
  test(`generation failure shows safe ${code} guidance and refreshes the run picker`, async ({ page }) => {
    // UI-only transport simulation; backend persistence/redaction has real workflow tests.
    let failed: Record<string, unknown> | undefined;
    await page.route('**/runs/*/advance', async route => {
      const runId = route.request().url().split('/').at(-2)!;
      const runURL = route.request().url().replace('/advance', '');
      const state = await page.request.get(runURL, { headers: { Authorization: `Bearer ${process.env.SPECBRIDGE_TOKEN}` } });
      failed = { ...await state.json(), id: runId, stage: 'execute', status: 'failed', error: code, attempts: 1 };
      await route.fulfill({ status: 502, contentType: 'application/json', body: JSON.stringify({ error: { code, message: 'RAW_PROVIDER_DETAIL_MUST_NOT_APPEAR' } }) });
    });
    await page.route('**/runs/*', async route => {
      if (failed && route.request().method() === 'GET') {
        await route.fulfill({ json: failed });
      } else await route.continue();
    });
    await page.route('**/projects/*/runs', async route => {
      if (failed && route.request().method() === 'GET') {
        await route.fulfill({ json: [{ ...failed, title: 'Generation attempt', revision_number: null, created_at: null }] });
      } else await route.continue();
    });
    await signInLocal(page);
    await projectCreation(page);
    await page.getByLabel('Project name', { exact: true }).fill('Safe failure fixture');
    await page.getByRole('button', { name: 'Create project', exact: true }).click();
    await page.getByLabel('Feature idea', { exact: true }).fill('Synthetic export feature.');
    if(!await page.getByLabel('I acknowledge generation uses this destination',{exact:true}).isVisible())await page.getByRole('button',{name:'Review generation',exact:true}).click();
    await page.getByLabel('I acknowledge generation uses this destination', { exact: true }).check();
    await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
    await expect(page.getByRole('alert').first()).toContainText(message);
    await expect(page.getByText('RAW_PROVIDER_DETAIL_MUST_NOT_APPEAR', { exact: false })).toHaveCount(0);
    await expect(page.getByLabel('Existing run', { exact: true }).locator('option:checked')).toContainText('failed');
    await expect(page.getByRole('button', { name: 'Retry stage', exact: true })).toBeDisabled();
  });
}
