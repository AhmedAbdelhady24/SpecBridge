/** Original synthetic fixture captures. Never connect this runner to an owner's workspace. */
import { test, expect } from '@playwright/test';
import { execFileSync, spawn } from 'node:child_process';
import { mkdirSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { createServer } from 'node:net';
import { resolve } from 'node:path';
import { editDraft, preparePackage, signInLocal } from '../tests/e2e/helpers';

const root = resolve(__dirname, '..');
const output = resolve(root, 'docs/media');

test('capture an isolated fixture handoff and its independently built documentation', async ({ page, request }) => {
  mkdirSync(output, { recursive: true });
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await signInLocal(page);
  // Sign-in form is unmounted after connection; no authentication footage or trace is retained.
  await expect(page.getByLabel('Session token', { exact: true })).toHaveCount(0);
  await page.getByLabel('Project name', { exact: true }).fill('Report exports · demo workspace');
  await page.getByRole('button', { name: 'Create project', exact: true }).click();
  await expect(page.getByLabel('Feature idea', { exact: true })).toBeEnabled();
  await page.getByLabel('Feature idea', { exact: true }).fill(
    'Export saved reports as CSV with column headers. Owner, deadline, report-size limit and permission rules are unknown.',
  );
  await page.getByLabel('I acknowledge generation uses this destination', { exact: true }).check();
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: resolve(output, 'intake.png'), animations: 'disabled' });
  await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Edit draft', exact: true })).toBeVisible();
  await page.getByRole('heading', { name: 'Draft review', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: resolve(output, 'review.png'), animations: 'disabled' });
  await editDraft(page);
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue(/DEMO fixture/);
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeDisabled();
  const requirementLabel = await page.getByText('Requirement ID:', { exact: false }).first().textContent();
  const requirementId = requirementLabel?.match(/REQ-[a-z0-9-]+/i)?.[0];
  expect(requirementId).toBeTruthy();
  await page.getByRole('button', { name: 'Read draft', exact: true }).click();
  await page.getByLabel('Review notes', { exact: true }).fill(
    'Demo review only: fixture assertions remain proposals. Resolve ownership, permissions and size limits before implementation.',
  );
  await page.getByRole('button', { name: 'Record review', exact: true }).click();
  await expect(page.getByText('Review recorded for this revision.', { exact: true })).toBeVisible();
  const candidate = await preparePackage(page);
  await expect(page.getByRole('button', { name: 'Approve this package', exact: true })).toBeEnabled();
  await page.getByRole('heading', { name: 'Exact package preview', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: resolve(output, 'approval.png'), animations: 'disabled' });
  await page.getByRole('button', { name: 'Approve this package', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeEnabled();
  const workspace = mkdtempSync(resolve(tmpdir(), 'specbridge-readme-site-'));
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download package', exact: true }).click();
  await (await downloadEvent).saveAs(resolve(workspace, 'handoff.zip'));
  const site = resolve(workspace, 'site');
  execFileSync('python3', ['-m', 'zipfile', '-e', resolve(workspace, 'handoff.zip'), site]);
  execFileSync('npm', ['ci', '--ignore-scripts', '--no-fund'], { cwd: site, stdio: 'pipe' });
  execFileSync('npm', ['run', 'build'], { cwd: site, stdio: 'pipe' });
  const port = await new Promise<number>((resolvePort, reject) => {
    const probe = createServer();
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', () => {
      const address = probe.address();
      if (!address || typeof address === 'string') throw new Error('No preview port');
      probe.close(error => error ? reject(error) : resolvePort(address.port));
    });
  });
  const origin = `http://127.0.0.1:${port}`;
  const server = spawn(process.execPath, [resolve(site, 'node_modules/astro/bin/astro.mjs'), 'preview', '--host', '127.0.0.1', '--ignore-lock', '--port', String(port)], {
    cwd: site, stdio: 'ignore', detached: true,
    env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1' },
  });
  try {
    await expect.poll(async () => {
      if (server.exitCode !== null) throw new Error('Documentation preview exited before capture');
      try { return (await request.get(origin)).status(); }
      catch { return 0; }
    }, { timeout: 30_000 }).toBe(200);
    await page.goto(`${origin}/requirements/`);
    await expect(page.getByRole('heading', { name: 'Requirements', exact: true }).first()).toBeVisible();
    await expect(page.locator('main')).toContainText(requirementId!);
    await page.screenshot({ path: resolve(output, 'documentation.png'), animations: 'disabled' });
    expect(errors).toEqual([]);
    expect(candidate.digest).toMatch(/^[a-f0-9]{64}$/);
  } finally {
    if (server.pid) {
      try { process.kill(-server.pid, 'SIGTERM'); }
      catch (error) { if ((error as NodeJS.ErrnoException).code !== 'ESRCH') throw error; }
    }
    await expect.poll(async () => {
      try { await request.get(origin, { timeout: 1000 }); return true; }
      catch { return false; }
    }, { timeout: 5000 }).toBe(false);
  }
});
