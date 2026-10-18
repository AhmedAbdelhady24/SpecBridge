import test from 'node:test';
import assert from 'node:assert/strict';
import { diffArtifacts } from './artifactDiff.ts';
import type { components } from './api/schema.d.ts';
type Artifact=components['schemas']['Artifact'];
const base:Artifact={title:'Export',purpose:'Reports',scope:[{text:'CSV',kind:'recommendation',source_ids:[]},{text:'Headers',kind:'recommendation',source_ids:[]}],non_goals:[],edge_cases:[],dependencies:[],risks:[],success_metrics:[],open_questions:['Who?','Who?'],requirements:[{id:'REQ-1',text:'Export CSV',kind:'recommendation',source_ids:[]}],stories:[{id:'STORY-1',text:'Export my reports',kind:'recommendation',source_ids:[],requirement_ids:['REQ-1'],acceptance_criteria:['A file downloads']}]};
test('list insertion preserves following entries rather than marking every item changed',()=>{
  const next=structuredClone(base);next.scope.unshift({text:'Saved reports only',kind:'recommendation',source_ids:[]});
  const changes=diffArtifacts(base,next);
  assert.equal(changes.length,1);assert.equal(changes[0].kind,'added');assert.equal(changes[0].section,'scope');
});
test('evidence, story links, criteria and duplicate list changes remain visible',()=>{
  const next=structuredClone(base);next.requirements[0].source_ids=['source-1'];next.stories[0].acceptance_criteria.push('Headers appear');next.open_questions.pop();
  const changes=diffArtifacts(base,next);
  assert.equal(changes.filter(c=>c.field==='source_ids').length,1);
  assert.equal(changes.filter(c=>c.field==='acceptance_criteria').length,1);
  assert.equal(changes.filter(c=>c.section==='open_questions').length,1);
});
