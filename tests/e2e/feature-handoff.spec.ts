import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { api, authHeaders, editDraft, createFeatureDraft, preparePackage, recordReview, signInLocal } from './helpers';

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
  await editDraft(page);
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
  await editDraft(page);
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

test('review correction adds missing questions and criteria with fresh approval and reload', async ({ page, request }) => {
  await signInLocal(page);
  const { projectId, runId } = await createFeatureDraft(page, 'Catalog draft A returns an items array and next_cursor; the next request format is unknown.');
  const runURL = `${api}/projects/${projectId}/runs/${runId}`;
  const beforeRun = await (await request.get(runURL, { headers: authHeaders() })).json();
  const before = await (await request.get(`${api}/projects/${projectId}/revisions/${beforeRun.revision_id}`, { headers: authHeaders() })).json();
  const originalQuestion = await page.getByLabel('Open question 1', { exact: true }).inputValue();
  await recordReview(page);
  const oldCandidate = await preparePackage(page);
  await page.getByRole('button', { name: 'Approve this package', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeEnabled();
  const addQuestion = page.getByRole('button', { name: 'Add open question', exact: true });
  await expect(addQuestion).toBeVisible();
  await addQuestion.click();
  const question = 'How does a client supply continuation information in the subsequent request?';
  await page.getByLabel('Open question 4', { exact: true }).fill(question);
  await page.getByRole('button', { name: 'Add acceptance criterion to story 1', exact: true }).click();
  const criterion = 'Given draft A and continuation input have been agreed, when next-page navigation completes, then the next set of items is displayed.';
  await page.getByLabel('Acceptance criterion 1.2', { exact: true }).fill(criterion);
  await expect(page.getByLabel('Open question 1', { exact: true })).toHaveValue(originalQuestion);
  await expect(page.getByRole('button', { name: 'Download package', exact: true })).toBeDisabled();
  const response = page.waitForResponse(r => r.url().endsWith('/edits') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  const savedResponse = await response;
  expect(savedResponse.status()).toBe(201);
  const saved = await savedResponse.json();
  expect(saved.artifact.open_questions).toEqual([...before.artifact.open_questions, question]);
  expect(saved.artifact.stories[0].acceptance_criteria).toEqual([...before.artifact.stories[0].acceptance_criteria, criterion]);
  expect(saved.artifact.requirements.map((r: { id: string }) => r.id)).toEqual(before.artifact.requirements.map((r: { id: string }) => r.id));
  expect(saved.artifact.stories.map((s: { id: string }) => s.id)).toEqual(before.artifact.stories.map((s: { id: string }) => s.id));
  await expect(page.getByRole('button', { name: 'Prepare package', exact: true })).toBeDisabled();
  expect((await request.get(`${api}/projects/${projectId}/candidates/${oldCandidate.id}/download`, { headers: authHeaders() })).status()).toBe(409);
  await page.reload();
  await page.getByLabel('Session token', { exact: true }).fill(process.env.SPECBRIDGE_TOKEN!);
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByLabel('Existing project', { exact: true }).selectOption(projectId);
  await page.getByLabel('Existing run', { exact: true }).selectOption(runId);
  await page.getByRole('button', { name: 'Open run', exact: true }).click();
  await editDraft(page);
  await expect(page.getByLabel('Open question 4', { exact: true })).toHaveValue(question);
  await expect(page.getByLabel('Acceptance criterion 1.2', { exact: true })).toHaveValue(criterion);
  await recordReview(page);
  const correctedCandidate = await preparePackage(page);
  await page.getByRole('button', { name: 'Approve this package', exact: true }).click();
  expect((await request.get(`${api}/projects/${projectId}/candidates/${correctedCandidate.id}/download`, { headers: authHeaders() })).status()).toBe(200);
});

test('review correction requires nonblank entries and preserves the last criterion', async ({ page }) => {
  await signInLocal(page);
  await createFeatureDraft(page);
  const lastCriterion = page.getByRole('button', { name: 'Remove acceptance criterion 1.1', exact: true });
  await expect(lastCriterion).toBeVisible();
  await expect(lastCriterion).toBeDisabled();
  let edits = 0;
  page.on('request', r => { if (r.url().endsWith('/edits')) edits++; });
  await page.getByRole('button', { name: 'Add open question', exact: true }).click();
  const question = page.getByLabel('Open question 4', { exact: true });
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  await expect(question).toBeFocused();
  expect(await question.evaluate((node: HTMLTextAreaElement) => node.validity.valueMissing)).toBe(true);
  expect(edits).toBe(0);
  await question.fill('Which request parameter is authoritative?');
  await page.getByRole('button', { name: 'Add acceptance criterion to story 1', exact: true }).click();
  const criterion = page.getByLabel('Acceptance criterion 1.2', { exact: true });
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  await expect(criterion).toBeFocused();
  expect(edits).toBe(0);
  await criterion.fill('Given an agreed request, when it succeeds, then its result is visible.');
  await page.getByRole('button', { name: 'Remove acceptance criterion 1.2', exact: true }).click();
  await expect(criterion).toHaveCount(0);
  await expect(lastCriterion).toBeDisabled();
  await page.getByRole('button', { name: 'Remove open question 4', exact: true }).click();
  await expect(question).toHaveCount(0);
});

test('review correction uses explicit evidence labels and retains source validation', async ({ page, request }) => {
  await signInLocal(page);
  const idea = 'Members can change their weekly email digest setting.';
  const { projectId, runId } = await createFeatureDraft(page, idea);
  const evidence = page.getByLabel('Evidence type for Requirement 1', { exact: true });
  await expect(evidence).toBeVisible();
  await expect(evidence.locator('option[value="unknown"], option[value="verified"]')).toHaveCount(0);
  await expect(page.locator('select option[value="verified"]')).toHaveCount(0);
  await expect(page.getByLabel('Evidence type for Scope 1', { exact: true }).locator('option[value="unknown"]')).toHaveCount(1);
  await page.getByLabel('Requirement 1', { exact: true }).fill(idea);
  await evidence.selectOption('user_provided');
  const firstResponse = page.waitForResponse(r => r.url().endsWith('/edits') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  const first = await (await firstResponse).json();
  expect(first.artifact.requirements[0].kind).toBe('user_provided');
  const run = await (await request.get(`${api}/projects/${projectId}/runs/${runId}`, { headers: authHeaders() })).json();
  expect(first.artifact.requirements[0].source_ids).toEqual(run.source_ids);
  await page.getByLabel('Requirement 1', { exact: true }).fill('Proposed behavior: deliver a digest when the preference is on.');
  await expect(evidence).toHaveValue('user_provided');
  const invalidResponse = page.waitForResponse(r => r.url().endsWith('/edits') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  expect((await invalidResponse).status()).toBe(422);
  await evidence.selectOption('recommendation');
  const secondResponse = page.waitForResponse(r => r.url().endsWith('/edits') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  const second = await (await secondResponse).json();
  expect(second.artifact.requirements[0].kind).toBe('recommendation');
  expect(second.artifact.requirements[0].id).toBe(first.artifact.requirements[0].id);
  expect(second.artifact.requirements[0].source_ids).toEqual(first.artifact.requirements[0].source_ids);
});

test('review correction respects question and criterion bounds', async ({ page, request }) => {
  await signInLocal(page);
  const { projectId, runId } = await createFeatureDraft(page);
  const run = await (await request.get(`${api}/projects/${projectId}/runs/${runId}`, { headers: authHeaders() })).json();
  const revision = await (await request.get(`${api}/projects/${projectId}/revisions/${run.revision_id}`, { headers: authHeaders() })).json();
  revision.artifact.open_questions = Array.from({ length: 100 }, (_, i) => `Unresolved question ${i + 1}?`);
  revision.artifact.stories[0].acceptance_criteria = Array.from({ length: 30 }, (_, i) => `Observable proposed criterion ${i + 1}.`);
  const saved = await request.post(`${api}/projects/${projectId}/revisions/${revision.id}/edits`, {
    headers: authHeaders(), data: { expected_digest: revision.digest, artifact: revision.artifact },
  });
  expect(saved.status()).toBe(201);
  await page.getByLabel('Existing run', { exact: true }).selectOption(runId);
  await page.getByRole('button', { name: 'Open run', exact: true }).click();
  await editDraft(page);
  await expect(page.getByRole('button', { name: 'Add open question', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Add open question', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Add acceptance criterion to story 1', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Remove open question 100', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Add open question', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Remove acceptance criterion 1.30', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Add acceptance criterion to story 1', exact: true })).toBeEnabled();
});


test('review correction repairs a saved model omission without regenerating', async ({ page, request }) => {
  const folder = resolve(__dirname, '../../docs/evaluations/reasoning-low-comparison-2026-10-16');
  const preview = JSON.parse(readFileSync(resolve(folder, 'preview.json'), 'utf8'));
  const originalCase = preview.requests.find((item: { id: string }) => item.id === 'notification-preferences');
  const originalArtifact = JSON.parse(readFileSync(resolve(folder, 'notification-preferences.json'), 'utf8'));
  await signInLocal(page);
  const { projectId, runId } = await createFeatureDraft(page, originalCase.sources[0].text);
  const runURL = `${api}/projects/${projectId}/runs/${runId}`;
  const run = await (await request.get(runURL, { headers: authHeaders() })).json();
  const revisionURL = `${api}/projects/${projectId}/revisions/${run.revision_id}`;
  const revision = await (await request.get(revisionURL, { headers: authHeaders() })).json();
  // Import the recorded synthetic draft into this temporary project, retaining evidence origin.
  for (const section of ['scope', 'non_goals', 'requirements', 'stories', 'edge_cases', 'dependencies', 'risks', 'success_metrics']) {
    for (const statement of originalArtifact[section]) {
      statement.source_ids = statement.source_ids.map(() => run.source_ids[0]);
    }
  }
  const importedResponse = await request.post(revisionURL + '/edits', {
    headers: authHeaders(), data: { expected_digest: revision.digest, artifact: originalArtifact },
  });
  expect(importedResponse.status()).toBe(201);
  const imported = await importedResponse.json();
  await page.getByLabel('Existing run', { exact: true }).selectOption(runId);
  await page.getByRole('button', { name: 'Open run', exact: true }).click();
  await editDraft(page);
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue(originalArtifact.title);
  const add = page.getByRole('button', { name: 'Add acceptance criterion to story 1', exact: true });
  await expect(add).toBeVisible();
  const on = 'Given a member has enabled weekly digests, when a weekly digest becomes due, then that digest is sent to the member.';
  const off = 'Given a member has disabled weekly digests, when a weekly digest becomes due, then that digest is not sent to the member.';
  const initial = 'Given a new member has not enabled weekly digests, when a weekly digest becomes due, then that digest is not sent to the member.';
  await add.click();
  await page.getByLabel('Acceptance criterion 1.3', { exact: true }).fill(on);
  await add.click();
  await page.getByLabel('Acceptance criterion 1.4', { exact: true }).fill(off);
  await page.getByRole('button', { name: 'Add acceptance criterion to story 4', exact: true }).click();
  await page.getByLabel('Acceptance criterion 4.2', { exact: true }).fill(initial);
  const response = page.waitForResponse(r => r.url().endsWith('/edits') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Save revision', exact: true }).click();
  const savedResponse = await response;
  expect(savedResponse.status()).toBe(201);
  const saved = await savedResponse.json();
  expect(saved.artifact.stories[0].acceptance_criteria).toContain(on);
  expect(saved.artifact.stories[0].acceptance_criteria).toContain(off);
  expect(saved.artifact.stories[3].acceptance_criteria).toContain(initial);
  expect(saved.artifact.stories.map((s: { id: string }) => s.id)).toEqual(imported.artifact.stories.map((s: { id: string }) => s.id));
  const after = await (await request.get(runURL, { headers: authHeaders() })).json();
  expect(after.attempts).toBe(run.attempts);
  expect(after.history).toEqual(run.history);
  expect(after.revision_id).toBe(saved.id);
});
