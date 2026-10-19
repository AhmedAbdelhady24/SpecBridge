import { useEffect, useId, useRef, useState } from 'react';
import { diffArtifacts } from './artifactDiff';
import { wordDiff } from './wordDiff';
import { SourceReferences } from './SourceReferences';
import type { components } from './api/schema';
type Artifact = components['schemas']['Artifact'];
const label = (value: string) => value.replaceAll('_', ' ').replace(/^./, c => c.toUpperCase());
export function DiffView({ base, head, expanded = false }: { base: Artifact; head: Artifact; expanded?: boolean }) {
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { if (open) dialog.current?.showModal(); }, [open]);
  const changes = diffArtifacts(base, head);
  const [query, setQuery] = useState('');
  const uid = useId();
  const groups = [...new Set(changes.map(c => c.section))];
  function describe(value: unknown, field: string): string {
    if (value === undefined) return '';
    if (field === 'source_ids') return 'Source references';
    if (Array.isArray(value)) return value.map(item => describe(item, field)).join('\n');
    if (typeof value === 'object' && value !== null) return Object.entries(value).filter(([key]) => !['id', 'source_ids'].includes(key)).map(([key, entry]) => `${label(key)}: ${describe(entry, key)}`).join('\n');
    const requirement = [...head.requirements, ...base.requirements].find(r => r.id === value);
    if (requirement) return `Requirement: ${requirement.text}`;
    const story = [...head.stories, ...base.stories].find(r => r.id === value);
    if (story) return `Story: ${story.text}`;
    return String(value);
  }
  return <div className={`document-diff ${expanded ? "expanded-comparison" : ""}`} aria-label="Document differences">
    {!changes.length ? <p>No document differences.</p> : <>
      {!expanded && <button type="button" className="secondary" onClick={() => setOpen(true)}>Expand comparison</button>}
      <p>{changes.length} {changes.length === 1 ? 'change' : 'changes'} across {groups.length} {groups.length === 1 ? 'section' : 'sections'}.</p>
      <div className="diff-browser">
        <nav aria-label="Changed sections" className="diff-index">
          <label>Filter changes<input value={query} onChange={e => setQuery(e.target.value)} type="search" /></label>
          {groups.filter(group => label(group).toLowerCase().includes(query.toLowerCase())).map(group => <a key={group} href={`#${uid}-${group}`} onClick={() => { const target = document.getElementById(`${uid}-${group}`) as HTMLDetailsElement; target.open = true; target.focus(); }}>{label(group)} <small>{changes.filter(c => c.section === group).length}</small></a>)}
        </nav>
        <div className="diff-files">{groups.filter(group => label(group).toLowerCase().includes(query.toLowerCase())).map(group => <details className="diff-file" id={`${uid}-${group}`} key={group} tabIndex={-1} open>
          <summary>{label(group)} · {changes.filter(c => c.section === group).length} {changes.filter(c => c.section === group).length === 1 ? 'change' : 'changes'}</summary>
          {changes.filter(c => c.section === group).map((change, index) => {
            const item = [...head.requirements, ...head.stories, ...base.requirements, ...base.stories].find(item => item.id === change.itemId);
            const parts = wordDiff(describe(change.before, change.field), describe(change.after, change.field));
            return <section className={`diff-hunk diff-${change.kind}`} key={index}>
              <h4>{item ? item.text : label(change.section)}{change.field !== change.section && <> · {label(change.field)}</>}</h4>
              <div className="split-diff">{(['before', 'after'] as const).map(side => <div key={side} className={`diff-${side}`} aria-label={side === 'before' ? 'Before' : 'After'}>
                <strong>{side === 'before' ? '− Before' : '+ After'}</strong>
                {typeof change[side] === 'object' && change[side] !== null && 'source_ids' in (change[side] as object) && <SourceReferences ids={(change[side] as { source_ids: string[] }).source_ids || []} claim={(change[side] as { text?: string }).text || ''} />}
                {change.field === 'source_ids' ? <SourceReferences ids={(change[side] as string[]) || []} claim={(side === 'before' ? [...base.requirements, ...base.stories] : [...head.requirements, ...head.stories]).find(r => r.id === change.itemId)?.text || ''} /> : <pre>{parts.filter(p => p.kind !== (side === 'before' ? 'added' : 'removed')).map((p, i) => p.kind === 'removed' ? <del key={i}>{p.text}</del> : p.kind === 'added' ? <ins key={i}>{p.text}</ins> : <span key={i}>{p.text}</span>)}</pre>}
              </div>)}</div>
            </section>;
          })}
        </details>)}</div>
      </div>
    </>}
    {open && <dialog ref={dialog} className="revision-diff-dialog" aria-label="Revision comparison" onClose={() => setOpen(false)}><button type="button" className="secondary" onClick={() => dialog.current?.close()}>Close comparison</button><DiffView base={base} head={head} expanded /></dialog>}
  </div>;
}
