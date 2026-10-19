import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
import { api, apiDraft, authHeaders, signInLocal } from './helpers';

async function openFeature(page: Page, request: APIRequestContext) {
  expect((await (await request.get(`${api}/config`, { headers: authHeaders() })).json()).provider).toBe('fixture');
  const data = await apiDraft(request);
  await signInLocal(page);
  await page.getByLabel('Existing project', { exact: true }).selectOption(data.project.id);
  await page.getByLabel('Existing run', { exact: true }).selectOption(data.run.id);
  await page.getByRole('button', { name: 'Open run', exact: true }).click();
  await expect(page.getByRole('article', { name: 'Readable draft' })).toBeVisible();
  return { ...data, base: `${api}/projects/${data.project.id}/runs/${data.run.id}` };
}

test('answer beside full draft, preview only, recover after reconnect and save one revision', async ({page,request}) => {
  await page.setViewportSize({width:1440,height:900});
  const data = await openFeature(page,request);
  const before = await (await request.get(`${api}/projects/${data.project.id}/revisions/${data.run.revision_id}`,{headers:authHeaders()})).json();
  let generationCalls=0;
  page.on('request',r=>{if(r.method()==='POST' && /\/runs(?:\/[^/]+\/advance)?$/.test(new URL(r.url()).pathname)) generationCalls++;});
  await page.getByRole('button',{name:'Questions',exact:true}).click();
  await page.getByLabel('Your answer',{exact:true}).fill('Use CSV files.');
  await page.getByRole('button',{name:'Save answer',exact:true}).click();
  await expect(page.getByText('Answer saved. The draft is unchanged.',{exact:true})).toBeVisible();
  await expect(page.getByRole('article',{name:'Readable draft'})).toBeVisible();
  await page.getByLabel('Amendment text',{exact:true}).fill('Use CSV files.');
  await page.getByLabel('Amendment target',{exact:true}).selectOption(before.artifact.requirements[0].id);
  await page.getByRole('button',{name:'Preview amendment',exact:true}).click();
  await expect(page.getByRole('article',{name:'Readable draft'})).toContainText('Use CSV files.');
  expect((await (await request.get(`${api}/projects/${data.project.id}/revisions/${before.id}`,{headers:authHeaders()})).json()).artifact).toEqual(before.artifact);
  await page.getByRole('button',{name:'Save working preview',exact:true}).click();
  await expect(page.getByText('Working preview saved privately. It is not a revision.',{exact:true})).toBeVisible();
  page.once('dialog',dialog=>dialog.accept());
  await page.reload();
  const projectSelect = page.getByLabel('Existing project', { exact: true });
  const reconnected = await projectSelect.waitFor({ state: 'visible', timeout: 2000 }).then(() => true).catch(() => false);
  if (!reconnected) {
    const reloadToken = page.getByLabel('Session token', { exact: true });
    if (await reloadToken.isVisible().catch(() => false)) {
      await reloadToken.fill(process.env.SPECBRIDGE_TOKEN!);
      await page.getByRole('button', { name: 'Connect', exact: true }).click();
      await expect(projectSelect).toBeVisible();
    }
  }
  await page.getByLabel('Existing project',{exact:true}).selectOption(data.project.id);
  await page.getByLabel('Existing run',{exact:true}).selectOption(data.run.id);
  await page.getByRole('button',{name:'Open run',exact:true}).click();
  await expect(page.getByText('A saved working preview is available.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Resume working preview',exact:true}).click();
  await expect(page.getByRole('article',{name:'Readable draft'})).toContainText('Use CSV files.');
  await page.getByRole('button',{name:'Save revision',exact:true}).click();
  await expect(page.getByText('New revision saved. Review and approve it again.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Changes',exact:true}).click();
  await expect(page.getByRole('region',{name:'Feature revision history'})).toContainText('Revision 2');
  expect(generationCalls).toBe(0);
});

test('mobile switches panes without losing answer or producing horizontal overflow', async({page,request})=>{
  await page.setViewportSize({width:390,height:844});
  await openFeature(page,request);
  await page.getByRole('button',{name:'Task pane',exact:true}).click();
  await page.getByLabel('Your answer',{exact:true}).fill('Keep this pending answer');
  await page.getByRole('button',{name:'Draft pane',exact:true}).click();
  await expect(page.getByRole('article',{name:'Readable draft'})).toBeVisible();
  await page.getByRole('button',{name:'Task pane',exact:true}).click();
  await expect(page.getByLabel('Your answer',{exact:true})).toHaveValue('Keep this pending answer');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('section editing keeps the rest of the specification readable',async({page,request})=>{
  await page.setViewportSize({width:1440,height:900});
  await openFeature(page,request);
  await page.getByRole('button',{name:'Edit requirements',exact:true}).click();
  await expect(page.getByLabel('Requirement 1',{exact:true})).toBeVisible();
  await expect(page.getByRole('article',{name:'Readable draft'})).toContainText('As a reviewer, I want to inspect the proposed scope');
  await expect(page.getByLabel('Title',{exact:true})).toHaveCount(0);
  await page.getByLabel('Requirement 1',{exact:true}).fill('A clearer proposed scope.');
  await page.getByRole('button',{name:'Save revision',exact:true}).click();
  await expect(page.getByText('New revision saved. Review and approve it again.',{exact:true})).toBeVisible();
});

test('review and exact package content stay alongside the full draft',async({page,request})=>{
  await page.setViewportSize({width:1440,height:900});
  await openFeature(page,request);
  await page.getByRole('button',{name:'Review & export',exact:true}).click();
  await page.getByLabel('Review notes',{exact:true}).fill('Synthetic human review; unknowns remain visible.');
  await expect(page.getByRole('article',{name:'Readable draft'})).toBeVisible();
  await page.getByRole('button',{name:'Record review',exact:true}).click();
  await page.getByRole('button',{name:'Prepare package',exact:true}).click();
  await expect(page.getByRole('article',{name:'Packaged documentation'})).toBeVisible();
  await page.getByLabel('Documentation file',{exact:true}).selectOption('src/content/docs/requirements.md');
  await expect(page.getByRole('article',{name:'Packaged documentation'})).toContainText('Present a proposed feature scope');
  await expect(page.getByRole('button',{name:'Download package',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Approve this package',exact:true}).click();
  await expect(page.getByRole('button',{name:'Download package',exact:true})).toBeEnabled();
  await page.screenshot({path:'test-results/focused-workspace-desktop.png',fullPage:true});
});

test('a lost commit response can be reconciled without a duplicate revision',async({page,request})=>{
  const data=await openFeature(page,request);
  await page.getByRole('button',{name:'Edit overview',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('A single committed update');
  let intercepted=false;
  await page.route('**/commits',async route=>{if(!intercepted){intercepted=true;await route.fetch();await route.abort('failed');}else await route.continue();});
  await page.getByRole('button',{name:'Save revision',exact:true}).click();
  await page.getByRole('button',{name:'Check or retry this revision save',exact:true}).click();
  await expect(page.getByText('New revision saved. Review and approve it again.',{exact:true})).toBeVisible();
  expect((await (await request.get(data.base+'/history',{headers:authHeaders()})).json()).length).toBe(2);
});

test('project background is directly selectable and remains an exact version',async({page,request})=>{
  const project=await(await request.post(`${api}/projects`,{headers:authHeaders(),data:{name:'Direct context audit'}})).json();
  await signInLocal(page);
  await page.getByLabel('Existing project',{exact:true}).selectOption(project.id);
  await page.getByText('Project context',{exact:true}).click();
  await page.getByLabel('Background title',{exact:true}).fill('Care-plan background');
  await page.getByLabel('Background text',{exact:true}).fill('Patients can read their own care plans.');
  await page.getByRole('button',{name:'Save background',exact:true}).click();
  await page.getByRole('button',{name:'Use in next draft',exact:true}).click();
  await expect(page.getByRole('button',{name:'Remove from next draft',exact:true})).toHaveAttribute('aria-pressed','true');
  const records=await(await request.get(`${api}/projects/${project.id}/knowledge`,{headers:authHeaders()})).json();
  const snapshot=await(await request.get(`${api}/projects/${project.id}/sources/knowledge-${records[0].id}-v1`,{headers:authHeaders()})).json();
  await page.getByLabel('Background text',{exact:true}).fill('A newly revised background note.');
  await page.getByRole('button',{name:'Save background',exact:true}).click();
  expect(snapshot.knowledge_ref).toBe(`${records[0].id}@1`);
  const saved=await(await request.get(`${api}/projects/${project.id}/sources/${snapshot.id}`,{headers:authHeaders()})).json();
  expect(saved.text).toContain('Patients can read their own care plans.');
  await page.getByRole('button',{name:'Remove context',exact:true}).click();
  await expect(page.getByRole('button',{name:'Remove context',exact:true})).toHaveCount(0);
});

test('requested changes resolve only with a saved revision and travel in its package',async({page,request})=>{
  const data=await openFeature(page,request);
  await page.getByRole('button',{name:'Changes',exact:true}).click();
  const feedback='Clarify the scope for engineering review.';
  await page.getByLabel('Requested change',{exact:true}).fill(feedback);
  await page.getByRole('button',{name:'Record requested change',exact:true}).click();
  await page.getByLabel('Address in next revision',{exact:true}).check();
  await page.getByRole('button',{name:'Edit overview',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('A clarified handoff');
  await page.getByRole('button',{name:'Save revision',exact:true}).click();
  await expect(page.getByText('New revision saved. Review and approve it again.',{exact:true})).toBeVisible();
  await expect(page.getByRole('region',{name:'Feature revision history'})).toContainText('addressed');
  const history=await(await request.get(data.base+'/history',{headers:authHeaders()})).json();
  const comparison=await(await request.get(data.base+`/compare?base=${history[1].revision_id}&head=${history[0].revision_id}`,{headers:authHeaders()})).json();
  expect(comparison.head_decisions.requests[0].text).toBe(feedback);
  await page.getByRole('button',{name:'Review & export',exact:true}).click();
  await page.getByLabel('Review notes',{exact:true}).fill('Reviewed the explicit amendment.');
  await page.getByRole('button',{name:'Record review',exact:true}).click();
  await page.getByRole('button',{name:'Prepare package',exact:true}).click();
  await page.getByLabel('Documentation file',{exact:true}).selectOption('src/content/docs/decisions.md');
  await expect(page.getByRole('article',{name:'Packaged documentation'})).toContainText(feedback);
});

test('packaged documentation renders hostile input as text without external requests',async({page,request})=>{
  await openFeature(page,request);
  const attack='<img src="https://attacker.example/pixel" onerror="window.__attack=true"> [click](javascript:alert(1))';
  const remote:string[]=[];page.on('request',r=>{if(r.url().startsWith('https://attacker.example'))remote.push(r.url());});
  await page.getByRole('button',{name:'Edit overview',exact:true}).click();
  await page.getByLabel('Purpose',{exact:true}).fill(attack);
  await page.getByRole('button',{name:'Save revision',exact:true}).click();
  await expect(page.getByText('New revision saved. Review and approve it again.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Review & export',exact:true}).click();
  await page.getByLabel('Review notes',{exact:true}).fill('Synthetic hostile-content fixture only.');
  await page.getByRole('button',{name:'Record review',exact:true}).click();
  await page.getByRole('button',{name:'Prepare package',exact:true}).click();
  await expect(page.getByRole('article',{name:'Packaged documentation'})).toContainText(attack);
  await expect(page.locator('img[src^="https://attacker.example"],a[href^="javascript:"]')).toHaveCount(0);
  expect(remote).toEqual([]);
  expect(await page.evaluate(()=>'__attack' in window)).toBe(false);
});

test('late revision save cannot replace a newly selected project',async({page,request})=>{
  const data=await apiDraft(request);
  const other=await(await request.post(`${api}/projects`,{headers:authHeaders(),data:{name:'Other workspace'}})).json();
  await signInLocal(page);
  await page.getByLabel('Existing project',{exact:true}).selectOption(data.project.id);
  await page.getByLabel('Existing run',{exact:true}).selectOption(data.run.id);
  await page.getByRole('button',{name:'Open run',exact:true}).click();
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  let release!:()=>void;const held=new Promise<void>(resolve=>{release=resolve;});
  let captured!:()=>void;const arrived=new Promise<void>(resolve=>{captured=resolve;});
  await page.route('**/commits',async route=>{const response=await route.fetch();captured();await held;await route.fulfill({response});});
  await page.getByRole('button',{name:'Edit overview',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('Late save from prior workspace');
  await page.getByRole('button',{name:'Save revision',exact:true}).click();await arrived;
  page.once('dialog',d=>d.accept());
  await page.getByLabel('Existing project',{exact:true}).selectOption(other.id);
  release();
  await expect(page.getByLabel('Existing project',{exact:true})).toHaveValue(other.id);
  await expect(page.getByRole('article',{name:'Readable draft'})).toHaveCount(0);
  await expect(page.getByText('New revision saved. Review and approve it again.',{exact:true})).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('unpreviewed amendment is protected when leaving the feature',async({page,request})=>{
  await openFeature(page,request);
  await page.getByLabel('Your answer',{exact:true}).fill('An explicit saved answer.');
  await page.getByRole('button',{name:'Save answer',exact:true}).click();
  await expect(page.getByText('Answer saved. The draft is unchanged.',{exact:true})).toBeVisible();
  await page.getByLabel('Amendment text',{exact:true}).fill('Unpreviewed wording that must be retained.');
  let warned=false;page.once('dialog',async d=>{warned=true;await d.dismiss();});
  await page.getByLabel('Existing project',{exact:true}).selectOption('');
  expect(warned).toBe(true);
  await expect(page.getByLabel('Amendment text',{exact:true})).toHaveValue('Unpreviewed wording that must be retained.');
});

test('expired workbench session reconnects without losing local draft',async({page,request})=>{
  await openFeature(page,request);
  await page.getByRole('button',{name:'Edit overview',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('Retain this private local edit');
  let rejected=false;
  await page.route('**/working-copy',async route=>{
    if(route.request().method()==='PUT'&&!rejected){rejected=true;await route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({detail:{code:'unauthorized',message:'Session expired'}})});}
    else await route.continue();
  });
  await page.getByRole('button',{name:'Save working preview',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Connect your workspace',exact:true})).toBeVisible();
  await expect(page.getByLabel('Title',{exact:true})).toHaveValue('Retain this private local edit');
  await page.getByLabel('Session token',{exact:true}).fill(process.env.SPECBRIDGE_TOKEN!);
  await page.getByRole('button',{name:'Connect',exact:true}).click();
  await page.getByRole('button',{name:'Save working preview',exact:true}).click();
  await expect(page.getByText('Working preview saved privately. It is not a revision.',{exact:true})).toBeVisible();
});

test('delayed answer history stays associated with its question',async({page,request})=>{
  const data=await openFeature(page,request);
  const questions=await(await request.get(data.base+'/questions',{headers:authHeaders()})).json();
  expect(questions.length).toBeGreaterThan(1);
  await page.getByLabel('Your answer',{exact:true}).fill('Answer belonging only to question A');
  await page.getByRole('button',{name:'Save answer',exact:true}).click();
  await expect(page.getByText('Answer saved. The draft is unchanged.',{exact:true})).toBeVisible();
  let release!:()=>void;const held=new Promise<void>(r=>{release=r;});
  let captured!:()=>void;const arrived=new Promise<void>(r=>{captured=r;});
  await page.route(`**/questions/${questions[0].id}/answers`,async route=>{const response=await route.fetch();captured();await held;await route.fulfill({response});});
  await page.getByText('Answer history',{exact:true}).click();await arrived;
  await page.getByRole('button',{name:`2. ${questions[1].text}`,exact:true}).click();
  const completed=page.waitForResponse(r=>r.url().endsWith(`/questions/${questions[0].id}/answers`));
  release();await completed;
  await expect(page.locator('.decision-card')).not.toContainText('Answer belonging only to question A');
});

test('reauthentication after commit retains the receipt for safe reconciliation',async({page,request})=>{
  const data=await openFeature(page,request);
  let committed=false;let rejected=false;
  page.on('response',r=>{if(r.url().endsWith('/commits')&&r.ok())committed=true;});
  await page.route('**/revisions/*',async route=>{
    if(committed&&!rejected&&route.request().method()==='GET'){rejected=true;await route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({detail:{code:'unauthorized'}})});}
    else await route.continue();
  });
  await page.getByRole('button',{name:'Edit overview',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('Committed once despite auth interruption');
  await page.getByRole('button',{name:'Save revision',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Connect your workspace',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Connect',exact:true}).click();
  await page.getByRole('button',{name:'Check or retry this revision save',exact:true}).click();
  await expect(page.getByText('New revision saved. Review and approve it again.',{exact:true})).toBeVisible();
  expect((await(await request.get(data.base+'/history',{headers:authHeaders()})).json()).length).toBe(2);
});

test('saving refuses to silently drop amendment text edited after preview',async({page,request})=>{
  const data=await openFeature(page,request);
  await page.getByLabel('Your answer',{exact:true}).fill('First explicit answer');
  await page.getByRole('button',{name:'Save answer',exact:true}).click();
  await expect(page.getByText('Answer saved. The draft is unchanged.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Preview amendment',exact:true}).click();
  await page.getByLabel('Amendment text',{exact:true}).fill('Newer unpreviewed amendment');
  await page.getByRole('button',{name:'Save revision',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Preview or discard your unpreviewed amendment text');
  await expect(page.getByLabel('Amendment text',{exact:true})).toHaveValue('Newer unpreviewed amendment');
  expect((await(await request.get(data.base+'/history',{headers:authHeaders()})).json()).length).toBe(1);
  await page.getByRole('button',{name:'Discard unpreviewed amendment text',exact:true}).click();
  await page.getByRole('button',{name:'Save revision',exact:true}).click();
  await expect(page.getByText('New revision saved. Review and approve it again.',{exact:true})).toBeVisible();
});

test('late revision save cannot replace another feature in the same project',async({page,request})=>{
  const data=await apiDraft(request);
  let second=await data.send(`/projects/${data.project.id}/runs`,{source_ids:[data.source.id],skill_id:'feature-handoff',intent:'Another feature',acknowledged_destination:'fixture'});
  for(let i=0;i<6;i++)second=await data.send(`/projects/${data.project.id}/runs/${second.id}/advance`,{});
  await signInLocal(page);
  await page.getByLabel('Existing project',{exact:true}).selectOption(data.project.id);
  await page.getByLabel('Existing run',{exact:true}).selectOption(data.run.id);
  await page.getByRole('button',{name:'Open run',exact:true}).click();
  let release!:()=>void;const held=new Promise<void>(r=>{release=r;});
  let captured!:()=>void;const arrived=new Promise<void>(r=>{captured=r;});
  await page.route('**/commits',async route=>{const response=await route.fetch();captured();await held;await route.fulfill({response});});
  await page.getByRole('button',{name:'Edit overview',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('Late title belonging to first feature');
  await page.getByRole('button',{name:'Save revision',exact:true}).click();await arrived;
  await page.getByText('Choose or start a feature',{exact:true}).click();
  await page.getByLabel('Existing run',{exact:true}).selectOption(second.id);
  page.once('dialog',d=>d.accept());
  await page.getByRole('button',{name:'Open run',exact:true}).click();
  await expect(page.getByRole('article',{name:'Readable draft'})).toBeVisible();
  const completion=page.waitForResponse(r=>r.url().includes('/revisions/')&&r.request().method()==='GET');
  release();await completion;
  await expect(page.getByRole('article',{name:'Readable draft'})).not.toContainText('Late title belonging to first feature');
  await expect(page.getByLabel('Existing run',{exact:true})).toHaveValue(second.id);
});
