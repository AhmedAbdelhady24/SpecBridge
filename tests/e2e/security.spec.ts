import { test, expect } from '@playwright/test';
import { api, apiDraft, authHeaders } from './helpers';

test('local API rejects foreign origin, foreign host and missing or invalid session', async ({ request }) => {
  for (const [headers, status] of [
    [{}, 401],
    [{ Authorization: 'Bearer invalid-local-session' }, 401],
    [{ ...authHeaders(), Origin: 'https://attacker.example' }, 403],
    [{ ...authHeaders(), Origin: 'null' }, 403],
    [{ ...authHeaders(), Host: 'attacker.example' }, 403],
  ] as const) {
    const response = await request.get(`${api}/projects`, { headers });
    expect(response.status()).toBe(status);
    expect(Object.keys(await response.json())).toEqual(['error']);
  }
  expect((await request.get(`${api}/projects`, { headers: authHeaders() })).status()).toBe(200);
});

test('candidate approval is project scoped and stale candidates cannot export', async ({ request }) => {
  const { project, run, send } = await apiDraft(request);
  const revisionURL = `/projects/${project.id}/revisions/${run.revision_id}`;
  await send(`${revisionURL}/reviews`, { disposition: 'reviewed', notes: 'Reviewed exact fixture revision; keep API conflict unresolved.' });
  const candidate = await send(`${revisionURL}/candidates`, {});
  const other = await send('/projects', { name: 'Other project' });
  for (const path of [
    `/projects/${other.id}/revisions/${run.revision_id}`,
    `/projects/${other.id}/runs/${run.id}`,
    `/projects/${other.id}/candidates/${candidate.id}/download`,
  ]) expect((await request.get(`${api}${path}`, { headers: authHeaders() })).status()).toBe(404);
  expect((await request.post(`${api}/projects/${other.id}/candidates/${candidate.id}/approve`, {
    headers: authHeaders(), data: { digest: candidate.digest },
  })).status()).toBe(404);
  const candidateURL = `/projects/${project.id}/candidates/${candidate.id}`;
  expect((await request.get(`${api}${candidateURL}/download`, { headers: authHeaders() })).status()).toBe(409);
  expect((await request.post(`${api}${candidateURL}/approve`, {
    headers: authHeaders(), data: { digest: '0'.repeat(64) },
  })).status()).toBe(409);
  await send(`${candidateURL}/approve`, { digest: candidate.digest });
  const revision = await (await request.get(`${api}${revisionURL}`, { headers: authHeaders() })).json();
  await send(`${revisionURL}/edits`, {
    expected_digest: revision.digest, artifact: { ...revision.artifact, purpose: 'An edit invalidates exact-package approval.' },
  });
  expect((await request.get(`${api}${candidateURL}/download`, { headers: authHeaders() })).status()).toBe(409);
  expect((await request.post(`${api}${candidateURL}/approve`, {
    headers: authHeaders(), data: { digest: candidate.digest },
  })).status()).toBe(409);
});
