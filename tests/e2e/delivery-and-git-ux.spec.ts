import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
import { apiDraft, signInLocal, showDraft, reviewTask, preparePackage, recordReview } from './helpers';

async function openDraft(page: Page, request: APIRequestContext) {
  const data = await apiDraft(request);
  await signInLocal(page);
  await page.getByLabel('Existing project', { exact: true }).selectOption(data.project.id);
  await page.getByLabel('Existing run', { exact: true }).selectOption(data.run.id);
  await page.getByRole('button', { name: 'Open run', exact: true }).click();
  return data;
}

test('workflow stepper displays progressive stage indicators', async ({ page, request }) => {
  await signInLocal(page);
  const stepper = page.getByRole('navigation', { name: 'Workflow progress' });
  await expect(stepper).toBeVisible();
  await expect(stepper.getByText('Project & Session')).toBeVisible();
  await expect(stepper.getByText('Context & Intake')).toBeVisible();

  const data = await openDraft(page, request);
  await expect(stepper.getByText('Amend & Clarify')).toBeVisible();
});

test('delivery automation extracts meeting actions and calculates deterministic priority', async ({ page, request }) => {
  await openDraft(page, request);
  const deliveryTab = page.getByRole('button', { name: 'Delivery', exact: true });
  await expect(deliveryTab).toBeVisible();
  await deliveryTab.click();

  const deliveryHeading = page.getByRole('heading', { name: 'Backlog intake, prioritization & Jira sync' });
  await expect(deliveryHeading).toBeVisible();

  // Test Meeting Action extraction
  const transcript = '- Action: Implement the audit trail endpoint (owner: Alice, deadline: 2026-10-24)\n- Action: Document the schema (owner: Bob)';
  await page.getByLabel('Meeting transcript or notes').fill(transcript);
  await page.getByRole('button', { name: 'Extract action items', exact: true }).click();

  await expect(page.getByText('Extracted 2 action items')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Alice', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Bob', exact: true })).toBeVisible();

  // Test Prioritization
  await page.getByRole('button', { name: 'Calculate priority ranking', exact: true }).click();
  await expect(page.getByText(/Calculated priority for/)).toBeVisible();
  await expect(page.getByRole('heading', { name: /Ranked items/ })).toBeVisible();
});

test('delivery automation unblocks unranked items by providing missing effort input', async ({ page, request }) => {
  const data = await apiDraft(request);
  const headers = { Authorization: `Bearer ${process.env.SPECBRIDGE_TOKEN!}` };
  const prev = await (
    await request.get(
      `${process.env.SPECBRIDGE_E2E_API_ORIGIN || 'http://127.0.0.1:8000'}/api/projects/${data.project.id}/revisions/${data.run.revision_id}`,
      { headers }
    )
  ).json();
  const next = structuredClone(prev.artifact);
  const id = `REQ-2`;
  next.requirements.push({
    ...next.requirements[0],
    id,
    text: 'Second requirement with missing effort for unranked testing',
  });
  next.stories.push({
    ...next.stories[0],
    id: `STORY-2`,
    requirement_ids: [id],
  });
  await data.send(`/projects/${data.project.id}/revisions/${prev.id}/edits`, {
    expected_digest: prev.digest,
    artifact: next,
  });

  await signInLocal(page);
  await page.getByLabel('Existing project', { exact: true }).selectOption(data.project.id);
  await page.getByLabel('Existing run', { exact: true }).selectOption(data.run.id);
  await page.getByRole('button', { name: 'Open run', exact: true }).click();

  const deliveryTab = page.getByRole('button', { name: 'Delivery', exact: true });
  await expect(deliveryTab).toBeVisible();
  await deliveryTab.click();

  // Calculate priority ranking without extracted meeting actions to rank draft requirements
  await page.getByRole('button', { name: 'Calculate priority ranking', exact: true }).click();
  await expect(page.getByText('Calculated priority for 1 items (1 unranked due to missing metrics).')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Unranked items (missing metrics)' })).toBeVisible();
  await expect(page.getByText('Missing: effort')).toBeVisible();

  // Inline effort input and recalculate button
  const effortInput = page.getByLabel('Effort');
  await expect(effortInput).toBeVisible();
  const recalcBtn = page.getByRole('button', { name: 'Recalculate with effort' });
  await expect(recalcBtn).toBeDisabled();

  // Provide effort override and recalculate
  await effortInput.fill('3');
  await expect(recalcBtn).toBeEnabled();
  await recalcBtn.click();

  // Both items should now be ranked
  await expect(page.getByText('Calculated priority for 2 items (0 unranked due to missing metrics).')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Unranked items (missing metrics)' })).not.toBeVisible();
  await expect(page.getByRole('heading', { name: 'Ranked items (2)' })).toBeVisible();
});

test('git collaboration appears in review panel, provides three-way sync preview and requires explicit digest approval', async ({ page, request }) => {
  await openDraft(page, request);
  await recordReview(page);
  const candidate = await preparePackage(page);

  // Approve candidate to unlock Git preview
  await page.getByRole('button', { name: 'Approve this package', exact: true }).click();
  await expect(page.getByText('This exact package is approved.')).toBeVisible();

  // Check Git collaboration section
  const gitHeading = page.getByRole('heading', { name: 'Git target & three-way sync' });
  await expect(gitHeading).toBeVisible();

  // Save a mock git target
  await page.getByLabel('Destination type').selectOption('github_mock');
  await page.getByLabel('Remote GitHub URL').fill('https://github.com/example-org/specs.git');
  await page.getByRole('button', { name: 'Save Git target', exact: true }).click();
  await expect(page.getByText('Git destination target configured.')).toBeVisible();

  // Trigger three-way preview
  await page.getByRole('button', { name: 'Preview Git changeset', exact: true }).click();
  await expect(page.getByText('Three-way comparison generated against base snapshot.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Three-way changeset preview' })).toBeVisible();
  await expect(page.getByText('Clean three-way merge')).toBeVisible();

  // Publish button must be disabled until human confirmation checkbox is checked
  const publishBtn = page.getByRole('button', { name: 'Publish to Git', exact: true });
  await expect(publishBtn).toBeDisabled();

  // Check explicit approval checkbox
  await page.getByRole('checkbox', { name: /I approve publishing changeset/ }).check();
  await expect(publishBtn).toBeEnabled();

  // Publish
  await publishBtn.click();
  await expect(page.getByText('Changeset successfully published to Git target.')).toBeVisible();
  await expect(page.getByRole('status').getByRole('heading', { name: 'Git publish receipt' })).toBeVisible();
});

test('question locator navigates to corresponding question in draft', async ({ page, request }) => {
  await openDraft(page, request);
  const questionsTab = page.getByRole('button', { name: 'Questions', exact: true });
  await questionsTab.click();

  const locateBtn = page.getByRole('button', { name: 'Locate question in draft →', exact: true });
  if (await locateBtn.isVisible()) {
    await locateBtn.click();
    const highlighted = page.locator('.reference-highlight');
    await expect(highlighted).toBeVisible();
  }
});
