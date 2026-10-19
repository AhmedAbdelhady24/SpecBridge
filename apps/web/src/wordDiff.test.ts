import test from 'node:test';
import assert from 'node:assert/strict';
import { wordDiff } from './wordDiff.ts';
test('word diff reconstructs both inputs and marks only changed wording',()=>{
 const parts=wordDiff('Export saved reports as PDF.','Export saved reports as CSV.');
 assert.equal(parts.filter(p=>p.kind!=='added').map(p=>p.text).join(''),'Export saved reports as PDF.');
 assert.equal(parts.filter(p=>p.kind!=='removed').map(p=>p.text).join(''),'Export saved reports as CSV.');
 assert.deepEqual(parts.filter(p=>p.kind==='removed').map(p=>p.text),['PDF.']);
 assert.deepEqual(parts.filter(p=>p.kind==='added').map(p=>p.text),['CSV.']);
});
test('large Unicode and hostile text remain literal with bounded fallback',()=>{
 const before='أهلاً <img> '+ 'x '.repeat(3000);
 const after='أهلاً <script> '+ 'y '.repeat(3000);
 const parts=wordDiff(before,after);
 assert.equal(parts.filter(p=>p.kind!=='added').map(p=>p.text).join(''),before);
 assert.equal(parts.filter(p=>p.kind!=='removed').map(p=>p.text).join(''),after);
});
