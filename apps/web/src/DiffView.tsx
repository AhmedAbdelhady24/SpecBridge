import { diffArtifacts } from './artifactDiff';
import type { components } from './api/schema';
type Artifact = components['schemas']['Artifact'];
const text = (value: unknown) => typeof value === 'string' ? value : JSON.stringify(value, null, 2);
export function DiffView({ base, head }: {
  base: Artifact;
  head: Artifact;
}) {
  const changes = diffArtifacts(base, head);
  return <div className="document-diff" aria-label="Document differences">{changes.length ? <><p>{changes.length} changes. Additions and removals are proposals until saved.</p>
    {changes.map((c, i) => <section key={i} className={`diff-${c.kind}`}><h4>{c.section.replaceAll('_', ' ')} · {c.field.replaceAll('_', ' ')}
      {c.itemId && <small> · {c.itemId}</small>}</h4>
      {c.before !== undefined && <div className="diff-before"><strong>− Before</strong>
        <pre>{text(c.before)}</pre></div>}
      {c.after !== undefined && <div className="diff-after"><strong>+ After</strong>
        <pre>{text(c.after)}</pre></div>}</section>)}</> : <p>No document differences.</p>}</div>;
}
