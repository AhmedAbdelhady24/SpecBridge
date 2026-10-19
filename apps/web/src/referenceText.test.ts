import test from 'node:test';
import assert from 'node:assert/strict';
import { exactPassage, sourceExcerpt } from './referenceText.ts';
test('only exact source text is identified as matching wording',()=>{
 const source='Context: Export saved reports as CSV. Unknown owners.';
 assert.deepEqual(exactPassage(source,'Export saved reports as CSV.'),{start:9,end:37});
 assert.equal(exactPassage(source,'Everyone can export reports.'),null);
 assert.equal(exactPassage(source,''),null);
});
test('quotes retain literal Unicode and hostile markup without substitution',()=>{
 const source='أهلاً <script>not executable</script> 👩🏽‍💻';
 assert.equal(sourceExcerpt(source,null),source);
 const match=exactPassage(source,'<script>not executable</script>');
 assert.equal(source.slice(match!.start,match!.end),'<script>not executable</script>');
});
