import type { components } from './api/schema';
type Artifact = components['schemas']['Artifact'];
export type ArtifactChange = {
  section: string;
  itemId: string | null;
  field: string;
  kind: 'added' | 'removed' | 'modified';
  before: unknown;
  after: unknown;
};
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);
export function diffArtifacts(base: Artifact, head: Artifact): ArtifactChange[] {
  const changes: ArtifactChange[] = [];
  for (const field of ['title', 'purpose'] as const)
    if (!same(base[field], head[field]))
      changes.push({ section: field, itemId: null, field, kind: 'modified', before: base[field], after: head[field] });
  for (const section of ['requirements', 'stories'] as const) {
    const before = new Map(base[section].map(x => [x.id, x]));
    const after = new Map(head[section].map(x => [x.id, x]));
    for (const id of new Set([...before.keys(), ...after.keys()])) {
      const a = before.get(id), b = after.get(id);
      if (!a || !b) {
        changes.push({ section, itemId: id, field: section, kind: a ? 'removed' : 'added', before: a, after: b });
        continue;
      }
      for (const field of Object.keys(a)) {
        const av = (a as unknown as Record<string, unknown>)[field], bv = (b as unknown as Record<string, unknown>)[field];
        if (!same(av, bv))
          changes.push({ section, itemId: id, field, kind: 'modified', before: av, after: bv });
      }
    }
    const sharedBefore = base[section].filter(x => after.has(x.id)).map(x => x.id);
    const sharedAfter = head[section].filter(x => before.has(x.id)).map(x => x.id);
    if (!same(sharedBefore, sharedAfter))
      changes.push({ section, itemId: null, field: 'order', kind: 'modified', before: sharedBefore, after: sharedAfter });
  }
  for (const section of ['scope', 'non_goals', 'edge_cases', 'dependencies', 'risks', 'success_metrics', 'open_questions'] as const) {
    const a = base[section], b = head[section];
    const lengths = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0));
    for (let i = a.length - 1; i >= 0; i--)
      for (let j = b.length - 1; j >= 0; j--)
        lengths[i][j] = same(a[i], b[j]) ? lengths[i + 1][j + 1] + 1 : Math.max(lengths[i + 1][j], lengths[i][j + 1]);
    let i = 0, j = 0;
    while (i < a.length || j < b.length) {
      if (i < a.length && j < b.length && same(a[i], b[j])) {
        i++;
        j++;
        continue;
      }
      if (j < b.length && (i === a.length || lengths[i][j + 1] >= lengths[i + 1][j]))
        changes.push({ section, itemId: null, field: section, kind: 'added', before: undefined, after: b[j++] });
      else
        changes.push({ section, itemId: null, field: section, kind: 'removed', before: a[i++], after: undefined });
    }
  }
  return changes;
}
