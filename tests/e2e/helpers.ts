import { expect, type APIRequestContext, type Page, type Response } from '@playwright/test';

export function sessionToken(): string {
  const token = process.env.SPECBRIDGE_TOKEN;
  if (!token) throw new Error('Run through playwright.config.ts to create an isolated local session');
  return token;
}

export const authHeaders = () => ({ Authorization: `Bearer ${sessionToken()}` });
export const api = `${process.env.SPECBRIDGE_E2E_API_ORIGIN || 'http://127.0.0.1:8000'}/api`;

export async function signInLocal(page: Page) {
  await page.goto('/');
  await page.getByLabel('Session token', { exact: true }).fill(sessionToken());
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.getByLabel('Project name', { exact: true })).toBeVisible();
}

export async function editDraft(page: Page) {
  await showDraft(page);
  const edit = page.getByRole('button', { name: 'Edit draft', exact: true });
  if (await edit.getAttribute('aria-pressed') !== 'true') await edit.click();
  await page.getByRole('button', { name: 'Expand all sections', exact: true }).click();
}

export async function createFeatureDraft(page: Page, idea = 'Allow a customer to export their saved report.') {
  await page.getByLabel('Project name', { exact: true }).fill(`Browser handoff ${Date.now()}`);
  const projectResponse = page.waitForResponse(r => r.url().endsWith('/api/projects') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Create project', exact: true }).click();
  const project = await (await projectResponse).json();
  await page.getByLabel('Feature idea', { exact: true }).fill(idea);
  if(!await page.getByLabel('I acknowledge generation uses this destination',{exact:true}).isVisible())await page.getByRole('button',{name:'Review generation',exact:true}).click();
  await page.getByLabel('I acknowledge generation uses this destination', { exact: true }).check();
  const runResponse = page.waitForResponse(r => r.url().endsWith(`/projects/${project.id}/runs`) && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
  const run = await (await runResponse).json();
  await editDraft(page);
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue(/DEMO fixture/);
  return { projectId: project.id as string, runId: run.id as string };
}

export async function recordReview(page: Page) {
  await reviewTask(page);
  await page.getByLabel('Review notes', { exact: true }).fill('Human review: retain unresolved API ownership; demo assertions are proposals.');
  await page.getByRole('button', { name: 'Record review', exact: true }).click();
}

export async function preparePackage(page: Page) {
  await reviewTask(page);
  const response = page.waitForResponse(r => r.url().endsWith('/candidates') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Prepare package', exact: true }).click();
  const candidate = await (await response).json();
  expect(candidate.digest).toMatch(/^[a-f0-9]{64}$/);
  await page.getByText('Technical manifest',{exact:true}).click();
  await expect(page.getByText(`Package digest: ${candidate.digest}`, { exact: false })).toBeVisible();
  return candidate as { id: string; project_id: string; revision_id: string; digest: string; manifest: Record<string, string> };
}

export async function apiDraft(request: APIRequestContext) {
  const send = async (path: string, data: unknown) => {
    const response = await request.post(`${api}${path}`, { headers: authHeaders(), data });
    expect(response.ok()).toBeTruthy();
    return response.json();
  };
  const project = await send('/projects', { name: `Security ${Date.now()}` });
  const source = await send(`/projects/${project.id}/sources`, { text: 'Allow report exports. Keep conflicting API ownership unresolved.' });
  let run = await send(`/projects/${project.id}/runs`, {
    source_ids: [source.id], skill_id: 'feature-handoff', intent: 'Create a feature handoff', acknowledged_destination: 'fixture',
  });
  for (let stage = 0; stage < 6; stage++) run = await send(`/projects/${project.id}/runs/${run.id}/advance`, {});
  expect(run.status).toBe('review');
  return { project, source, run, send };
}

export async function showDraft(page: Page) {
  const switcher=page.getByRole('button',{name:'Draft pane',exact:true});
  if((page.viewportSize()?.width||1280)<=900)await switcher.click();
}
export async function reviewTask(page: Page) {
  const switcher=page.getByRole('button',{name:'Task pane',exact:true});
  if((page.viewportSize()?.width||1280)<=900)await switcher.click();
  const tab=page.getByRole('button',{name:'Review & export',exact:true});
  await expect(tab).toBeVisible();
  await tab.click();
}
export async function projectCreation(page: Page) {
  if(!await page.getByLabel('Project name',{exact:true}).isVisible())await page.getByText('Create a project',{exact:true}).click();
}
export async function contextClassification(page: Page) {
  if(!await page.getByLabel('Background type',{exact:true}).isVisible())await page.getByText('Background classification',{exact:true}).click();
}
export async function contextEvidence(page: Page) {
  if(!await page.getByLabel('Information type',{exact:true}).isVisible())await page.getByText('Supporting evidence & classification',{exact:true}).click();
}

export async function committedRevision(page:Page,response:Response) {
  expect(response.status()).toBe(201);
  const receipt=await response.json();
  const projectUrl=response.url().split('/runs/')[0];
  const stored=await page.request.get(`${projectUrl}/revisions/${receipt.revision_id}`,{headers:authHeaders()});
  expect(stored.status()).toBe(200);
  return stored.json();
}
