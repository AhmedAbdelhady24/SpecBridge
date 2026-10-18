import { contextEvidence, projectCreation, reviewTask, showDraft } from './helpers';
import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
import { api, apiDraft, authHeaders, signInLocal } from './helpers';

async function openDraft(page: Page, request: APIRequestContext) {
  const data = await apiDraft(request);
  await signInLocal(page);
  await page.getByLabel('Existing project', { exact: true }).selectOption(data.project.id);
  await page.getByLabel('Existing run', { exact: true }).selectOption(data.run.id);
  await page.getByRole('button', { name: 'Open run', exact: true }).click();
  return data;
}

test('authentication errors retain and focus the private input with inline help', async ({ page }) => {
  await page.goto('/');
  const token = page.getByLabel('Session token', { exact: true });
  await token.fill('synthetic-invalid-session');
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(token).toHaveValue('synthetic-invalid-session');
  await expect(token).toHaveAttribute('aria-invalid', 'true');
  await expect(token).toBeFocused();
  await expect(page.getByText(/\.data\/session-token/)).toBeVisible();
});

test('read mode reduces controls and package actions wait for an active revision', async ({ page, request }) => {
  await signInLocal(page);
  await expect(page.getByRole('button', { name: 'Record review', exact: true })).toHaveCount(0);
  const data = await apiDraft(request);
  await page.reload();
  await signInLocal(page);
  await page.getByLabel('Existing project', { exact: true }).selectOption(data.project.id);
  await page.getByLabel('Existing run', { exact: true }).selectOption(data.run.id);
  await expect(page.getByLabel('Existing run', { exact: true }).locator('option:checked')).toContainText('DEMO fixture handoff');
  await page.getByRole('button', { name: 'Open run', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Edit draft', exact: true })).toBeVisible();
  await expect(page.getByLabel('Title', { exact: true })).toHaveCount(0);
  const draft = page.getByRole('region', { name: 'Draft review', exact: true });
  await expect(draft.getByRole('heading', { name: /DEMO fixture handoff/ })).toBeVisible();
  await expect(draft.getByRole('article',{name:'Readable draft'}).locator('textarea')).toHaveCount(0);
  await expect(draft.getByText('Human review required', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Jump to review and package', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Review & export', exact: true })).toBeFocused();
});

test('unsaved edits have reachable actions, explanatory blocking and lossless discard', async ({ page, request }) => {
  const { project, run } = await openDraft(page, request);
  await showDraft(page);
  await page.getByRole('button', { name: 'Edit draft', exact: true }).click();
  const title = page.getByLabel('Title', { exact: true });
  const original = await title.inputValue();
  await title.fill('Unsaved proposal title');
  await expect(page.getByText(/Save or discard your edits before recording/)).toBeVisible();
  await reviewTask(page);
  await expect(page.getByRole('button', { name: 'Record review', exact: true })).toBeDisabled();
  await page.evaluate(() => scrollTo(0, document.body.scrollHeight));
  await expect(page.getByRole('button', { name: 'Save revision', exact: true })).toBeInViewport();
  await expect(page.getByRole('button', { name: 'Discard changes', exact: true })).toBeInViewport();
  await page.getByRole('button', { name: 'Discard changes', exact: true }).click();
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue(original);
  await reviewTask(page);
  await expect(page.getByRole('button', { name: 'Record review', exact: true })).toBeEnabled();
  const saved = await (await request.get(`${api}/projects/${project.id}/runs/${run.id}`, { headers: authHeaders() })).json();
  expect(saved.revision_id).toBe(run.revision_id);
  await page.getByRole('button', { name: 'Expand all sections', exact: true }).click();
  const question = page.getByLabel('Open question 1', { exact: true });
  const oldQuestion = await question.inputValue();
  await page.getByRole('button', { name: 'Remove open question 1', exact: true }).click();
  await page.getByRole('button', { name: 'Undo removal', exact: true }).click();
  await expect(question).toHaveValue(oldQuestion);
  await page.getByRole('button', { name: 'Read draft', exact: true }).click();
  await expect(page.getByLabel('Title', { exact: true })).toHaveCount(0);
});

for (const width of [390, 768, 1440]) {
  test(`review remains usable and save is visible at ${width}px`, async ({ page, request }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await openDraft(page, request);
    if (width <= 900) {
      const columns = await page.locator('.workspace-grid').evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length);
      expect(columns).toBe(1);
    }
    await showDraft(page);
    await page.getByRole('button', { name: 'Edit draft', exact: true }).click();
    await page.getByLabel('Title', { exact: true }).fill('Responsive unsaved title');
    await page.getByRole('button', { name: 'Expand all sections', exact: true }).click();
    await page.evaluate(() => scrollTo(0, document.body.scrollHeight / 2));
    await expect(page.getByRole('button', { name: 'Save revision', exact: true })).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`review-${width}.png`) });
  });
}

test('evidence selection uses original source previews, persists across search and clears verification consent', async ({ page, request }) => {
  const { project, source } = await apiDraft(request);
  for (let n = 0; n < 21; n++) {
    await request.post(`${api}/projects/${project.id}/sources`, { headers: authHeaders(), data: { text: `Original evidence ${n}: accessible CSV reports.` } });
  }
  await signInLocal(page);
  await page.getByLabel('Existing project', { exact: true }).selectOption(project.id);
  await page.getByText('Project context', { exact: true }).click();
  await page.getByLabel('Background title', { exact: true }).fill('Evidence-backed scope');
  await page.getByLabel('Background text', { exact: true }).fill('A proposed CSV export scope.');
  await contextEvidence(page);
  await page.getByText(/Choose evidence/).click();
  await expect(page.getByRole('checkbox', { name: /^Use evidence:/ })).toHaveCount(20);
  await page.getByRole('button', { name: 'Load more evidence', exact: true }).click();
  await expect(page.getByRole('checkbox', { name: /^Use evidence:/ })).toHaveCount(22);
  await page.getByLabel('Search evidence', { exact: true }).fill(source.text);
  let knowledgeWrites = 0;
  page.on('request', r => { if (r.method() === 'POST' && r.url().endsWith('/knowledge')) knowledgeWrites++; });
  await page.getByLabel('Search evidence', { exact: true }).press('Enter');
  await page.getByRole('checkbox', { name: `Use evidence: ${source.text}`, exact: true }).check();
  expect(knowledgeWrites).toBe(0);
  await page.getByLabel('Search evidence', { exact: true }).fill('nothing matches');
  await page.getByRole('button', { name: 'Find evidence', exact: true }).click();
  await expect(page.getByRole('button', { name: /^Remove evidence:/ })).toHaveCount(1);
  await page.getByRole('button', { name: 'Save background', exact: true }).click();
  await page.getByLabel('Verification note', { exact: true }).fill('Checked original stakeholder evidence.');
  await page.getByLabel('I confirm this knowledge against the cited original evidence', { exact: true }).check();
  await expect(page.getByRole('button', { name: 'Record human verification', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: /^Remove evidence:/ }).click();
  await expect(page.getByLabel('I confirm this knowledge against the cited original evidence', { exact: true })).not.toBeChecked();
  await expect(page.getByRole('button', { name: 'Record human verification', exact: true })).toBeDisabled();
});

test('discard preserves exact saved approval while saving requires a new review', async ({ page, request }) => {
  const { project } = await openDraft(page, request);
  await reviewTask(page);
  await page.getByLabel('Review notes', { exact: true }).fill('Synthetic reviewer accepts the fixture limitations.');
  await reviewTask(page);
  await page.getByRole('button', { name: 'Record review', exact: true }).click();
  const candidateResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/candidates'));
  await reviewTask(page);
  await page.getByRole('button', { name: 'Prepare package', exact: true }).click();
  const candidate = await (await candidateResponse).json();
  await page.getByRole('button', { name: 'Approve this package', exact: true }).click();
  await reviewTask(page);
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeEnabled();
  await showDraft(page);
  await page.getByRole('button', { name: 'Edit draft', exact: true }).click();
  await page.getByLabel('Title', { exact: true }).fill('Local unsaved proposal');
  await reviewTask(page);
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Discard changes', exact: true }).click();
  await reviewTask(page);
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeEnabled();
  const url = `${api}/projects/${project.id}/candidates/${candidate.id}/download`;
  expect((await request.get(url, { headers: authHeaders() })).status()).toBe(200);
  await page.getByLabel('Title', { exact: true }).fill('Saved updated proposal');
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  await expect(page.getByText('New revision saved. Review and approve it again.', { exact: true })).toBeVisible();
  expect((await request.get(url, { headers: authHeaders() })).status()).toBe(409);
  await reviewTask(page);
  await expect(page.getByRole('button', { name: 'Prepare package', exact: true })).toBeDisabled();
  await expect(page.getByLabel('Existing run', { exact: true }).locator('option:checked')).toContainText('Saved updated proposal');
});

test('switching projects requires explicit discard of unsaved edits', async ({ page, request }) => {
  const other = await (await request.post(`${api}/projects`, { headers: authHeaders(), data: { name: 'Another isolated project' } })).json();
  const { project } = await openDraft(page, request);
  await showDraft(page);
  await page.getByRole('button', { name: 'Edit draft', exact: true }).click();
  await page.getByLabel('Title', { exact: true }).fill('Keep this unsaved title');
  page.once('dialog', dialog => dialog.dismiss());
  await page.getByLabel('Existing project', { exact: true }).selectOption(other.id);
  await expect(page.getByLabel('Existing project', { exact: true })).toHaveValue(project.id);
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue('Keep this unsaved title');
  page.once('dialog', dialog => dialog.accept());
  await page.getByLabel('Existing project', { exact: true }).selectOption(other.id);
  await expect(page.getByRole('button', { name: 'Edit draft', exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Existing project', { exact: true })).toHaveValue(other.id);
});

test('read mode renders hostile draft text inertly', async ({ page, request }) => {
  await openDraft(page, request);
  await showDraft(page);
  await page.getByRole('button', { name: 'Edit draft', exact: true }).click();
  const text = '<img src="https://attacker.example/pixel" onerror="window.__attack=true">';
  await page.getByLabel('Purpose', { exact: true }).fill(text);
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  await expect(page.getByText('New revision saved. Review and approve it again.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Read draft', exact: true }).click();
  await expect(page.getByRole('article', { name: 'Readable draft' })).toContainText(text);
  await expect(page.locator('img[src^="https://attacker.example"]')).toHaveCount(0);
  expect(await page.evaluate(() => '__attack' in window)).toBe(false);
});

test('creating a project asks once and never writes after a canceled discard', async ({ page, request }) => {
  await openDraft(page, request);
  await showDraft(page);
  await page.getByRole('button', { name: 'Edit draft', exact: true }).click();
  await page.getByLabel('Title', { exact: true }).fill('An unsaved title worth keeping');
  await projectCreation(page);
  await page.getByLabel('Project name', { exact: true }).fill('Explicitly created after discard');
  let writes = 0;
  page.on('request', r => { if (r.method() === 'POST' && r.url().endsWith('/projects')) writes++; });
  page.once('dialog', dialog => dialog.dismiss());
  await page.getByRole('button', { name: 'Create project', exact: true }).click();
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue('An unsaved title worth keeping');
  expect(writes).toBe(0);
  let dialogs = 0;
  page.on('dialog', dialog => { dialogs++; void dialog.accept(); });
  await page.getByRole('button', { name: 'Create project', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Edit draft', exact: true })).toHaveCount(0);
  expect(dialogs).toBe(1);
  expect(writes).toBe(1);
  await expect(page.getByLabel('Existing project', { exact: true }).locator('option:checked')).toHaveText('Explicitly created after discard');
});

test('the keyboard skip link avoids branding and moves focus into the workspace', async ({ page }) => {
  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/');
    await page.keyboard.press('Tab');
    const skip = page.getByRole('link', { name: 'Skip to workspace', exact: true });
    await expect(skip).toBeFocused();
    const target = await skip.boundingBox();
    const brand = await page.getByRole('link', { name: 'SpecBridge home', exact: true }).boundingBox();
    expect(target && brand && (target.y + target.height <= brand.y || target.y >= brand.y + brand.height || target.x + target.width <= brand.x || target.x >= brand.x + brand.width)).toBe(true);
    await page.keyboard.press('Enter');
    await expect(page.locator('#workspace')).toBeFocused();
  }
});

test('saving reveals and focuses a missing required field inside a closed edit section', async ({ page, request }) => {
  await openDraft(page, request);
  await showDraft(page);
  await page.getByRole('button', { name: 'Edit draft', exact: true }).click();
  await page.getByRole('button', { name: 'Expand all sections', exact: true }).click();
  await page.getByRole('button', { name: 'Add open question', exact: true }).click();
  const missing = page.getByLabel('Open question 4', { exact: true });
  const section = page.locator('details.editor-section').filter({ has: missing });
  await section.locator('summary').click();
  await expect(missing).not.toBeVisible();
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  await expect(missing).toBeVisible();
  await expect(missing).toBeFocused();
});
