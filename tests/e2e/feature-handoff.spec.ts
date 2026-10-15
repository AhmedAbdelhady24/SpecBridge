import { test, expect } from '@playwright/test';
import { api, authHeaders, createFeatureDraft, preparePackage, recordReview, signInLocal } from './helpers';

test('human review binds the exact package before download', async ({ page, request }, testInfo) => {
  await signInLocal(page);
  const { projectId, runId } = await createFeatureDraft(page, 'Export saved reports. API ownership is unresolved; do not invent a decision.');
  await expect(page.getByLabel('Purpose', { exact: true })).toHaveValue(/not AI validation/);
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeDisabled();
  await recordReview(page);
  const candidate = await preparePackage(page);
  const url = `${api}/projects/${projectId}/candidates/${candidate.id}/download`;
  expect((await request.get(url, { headers: authHeaders() })).status()).toBe(409);
  await page.getByRole('button', { name: 'Approve this package', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeEnabled();
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download package', exact: true }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toMatch(/\.zip$/);
  await download.saveAs(testInfo.outputPath('approved-documentation.zip'));
  const exported = await request.get(url, { headers: authHeaders() });
  expect(exported.status()).toBe(200);
  expect((await exported.body()).subarray(0, 2).toString()).toBe('PK');

  const run = await (await request.get(`${api}/projects/${projectId}/runs/${runId}`, { headers: authHeaders() })).json();
  const revision = await (await request.get(`${api}/projects/${projectId}/revisions/${run.revision_id}`, { headers: authHeaders() })).json();
  const ids = revision.artifact.requirements.map((r: { id: string }) => r.id);
  for (const id of ids) await expect(page.getByText(`Requirement ID: ${id}`, { exact: false })).toBeVisible();
  expect(revision.artifact.requirements[0].source_ids).toEqual(run.source_ids);
  const saveResponse = page.waitForResponse(r => r.url().endsWith('/edits') && r.request().method() === 'POST');
  await page.getByLabel('Purpose', { exact: true }).fill('Revised purpose; keep source and requirement IDs unchanged.');
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  const edited = await (await saveResponse).json();
  expect(edited.artifact.requirements.map((r: { id: string }) => r.id)).toEqual(ids);
  expect(edited.digest).not.toBe(revision.digest);
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeDisabled();
  expect((await request.get(url, { headers: authHeaders() })).status()).toBe(409);
});

test('reload recovers an existing run without repeating generation', async ({ page, request }) => {
  await signInLocal(page);
  const { projectId, runId } = await createFeatureDraft(page);
  const runURL = `${api}/projects/${projectId}/runs/${runId}`;
  const before = await (await request.get(runURL, { headers: authHeaders() })).json();
  await page.reload();
  await expect(page.getByLabel('Session token', { exact: true })).toHaveValue('');
  expect(await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } }))).toEqual({ local: {}, session: {} });
  await page.getByLabel('Session token', { exact: true }).fill(process.env.SPECBRIDGE_TOKEN!);
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByLabel('Existing project', { exact: true }).selectOption(projectId);
  await page.getByLabel('Existing run', { exact: true }).selectOption(runId);
  await page.getByRole('button', { name: 'Open run', exact: true }).click();
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue(/DEMO fixture/);
  await page.getByText('Selected source evidence', { exact: true }).click();
  await expect(page.getByText('Allow a customer to export their saved report.', { exact: true })).toBeVisible();
  const after = await (await request.get(runURL, { headers: authHeaders() })).json();
  expect(after.attempts).toBe(before.attempts);
  expect(after.history).toEqual(before.history);
  expect(after.revision_id).toBe(before.revision_id);
});

test('raw HTML and remote images remain inert in preview', async ({ page }) => {
  const remoteRequests: string[] = [];
  page.on('request', r => { if (r.url().startsWith('https://attacker.example')) remoteRequests.push(r.url()); });
  await signInLocal(page);
  await createFeatureDraft(page, '<script>window.__specbridgeAttack = true</script> ![remote](https://attacker.example/source.png)');
  const attack = '<img src="https://attacker.example/pixel.png" onerror="window.__specbridgeAttack=true"><script>window.__specbridgeAttack=true</script> [click](javascript:alert(1))';
  await page.getByLabel('Purpose', { exact: true }).fill(attack);
  const savedResponse = page.waitForResponse(r => r.url().endsWith('/edits') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  expect((await savedResponse).ok()).toBeTruthy();
  await expect(page.getByLabel('Purpose', { exact: true })).toHaveValue(attack);
  expect(await page.evaluate(() => '__specbridgeAttack' in window)).toBe(false);
  await expect(page.locator('img[src^="https://attacker.example"], a[href^="javascript:"]')).toHaveCount(0);
  expect(remoteRequests).toEqual([]);
});

test('local sign in supports keyboard and a narrow viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');
  const token = page.getByLabel('Session token', { exact: true });
  await token.focus();
  await page.keyboard.type(process.env.SPECBRIDGE_TOKEN!);
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Connect', exact: true })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByLabel('Project name', { exact: true })).toBeVisible();
  await createFeatureDraft(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('invalid local authorization does not open project data', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Session token', { exact: true }).fill('invalid-local-session');
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByLabel('Project name', { exact: true })).not.toBeVisible();
});


test('a transport failure preserves the run and requires an acknowledged retry', async ({ page }) => {
  await signInLocal(page);
  await page.getByLabel('Project name', { exact: true }).fill('Retry demonstration');
  await page.getByRole('button', { name: 'Create project', exact: true }).click();
  await page.getByLabel('Feature idea', { exact: true }).fill('Allow report exports.');
  await page.getByLabel('I acknowledge generation uses this destination', { exact: true }).check();
  // Inject a transport failure only; real provider interruption is covered by backend tests.
  await page.route('**/runs/*/advance', route => route.fulfill({
    status: 502, contentType: 'application/json',
    body: JSON.stringify({ error: { code: 'stage_failed', message: 'Injected transport failure' } }),
  }), { times: 1 });
  await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Injected transport failure');
  const retry = page.getByRole('button', { name: 'Retry stage', exact: true });
  await expect(retry).toBeDisabled();
  await page.getByLabel('I acknowledge this retry may repeat a billable provider call', { exact: true }).check();
  const retried = page.waitForRequest(r => r.url().endsWith('/advance'));
  await retry.click();
  expect((await retried).postDataJSON().retry_acknowledged).toBe(true);
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue(/DEMO fixture/);
});

test('human rejection blocks package preparation', async ({ page, request }) => {
  await signInLocal(page);
  const { projectId, runId } = await createFeatureDraft(page);
  await page.getByLabel('Review notes', { exact: true }).fill('Reject: unresolved conflicting API owners require a new revision.');
  await page.getByRole('button', { name: 'Reject revision', exact: true }).click();
  await expect(page.getByText('Revision rejected. Edit and save a new revision to continue.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Prepare package', exact: true })).toBeDisabled();
  const run = await (await request.get(`${api}/projects/${projectId}/runs/${runId}`, { headers: authHeaders() })).json();
  expect((await request.post(`${api}/projects/${projectId}/revisions/${run.revision_id}/candidates`, { headers: authHeaders() })).status()).toBe(409);
});
