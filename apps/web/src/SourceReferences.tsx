import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import type { components } from './api/schema';
import { ApiError, request } from './api/client';
import { evidenceLabel } from './labels';
import { exactPassage, sourceExcerpt } from './referenceText';
type Source = components['schemas']['Source'];
const Sources = createContext<((id: string) => Promise<Source>) | null>(null);
export function ReferenceProvider({ token, project, onAuthError, children }: {
  token: string; project: string; onAuthError: () => void; children: ReactNode;
}) {
  const cache = useRef(new Map<string, Promise<Source>>());
  const auth = useRef(onAuthError); auth.current = onAuthError;
  const load = useCallback((id: string) => {
    const key = project + '/' + id;
    let result = cache.current.get(key);
    if (!result) {
      result = request<Source>(token, `/projects/${encodeURIComponent(project)}/sources/${encodeURIComponent(id)}`).catch(error => {
        cache.current.delete(key);
        if (error instanceof ApiError && error.status === 401) auth.current();
        throw error;
      });
      cache.current.set(key, result);
    }
    return result;
  }, [token, project]);
  return <Sources.Provider value={load}>{children}</Sources.Provider>;
}
function SourceQuote({ id, claim }: { id: string; claim: string }) {
  const load = useContext(Sources);
  const [source, setSource] = useState<Source>();
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  const full = useRef<HTMLQuoteElement>(null);
  useEffect(() => {
    let active = true;
    setSource(undefined); setFailed(false);
    if (load) load(id).then(value => { if (active) setSource(value); }).catch(() => { if (active) setFailed(true); });
    else setFailed(true);
    return () => { active = false; };
  }, [load, id, retry]);
  const match = source ? exactPassage(source.text, claim) : null;
  return <section className="source-quote">
    {!source ? failed ? <><p role="alert">Source unavailable. The original reference is retained.</p><button type="button" className="secondary" onClick={() => setRetry(n => n + 1)}>Retry source</button></> : <p role="status">Loading original source…</p> : <>
      <p className="muted">{source.knowledge_ref ? 'Project context snapshot' : 'Original source'} · {evidenceLabel(source.kind)}</p>
      <blockquote>{sourceExcerpt(source.text, match)}</blockquote>
      <p className="muted">{match ? 'Exact matching wording is highlighted below. Review whether it supports this claim.' : 'No exact supporting passage was recorded. Review the original source.'}</p>
      <details onToggle={event => {
        if (event.currentTarget.open) { full.current?.focus({ preventScroll: true }); full.current?.querySelector('mark')?.scrollIntoView({ block: 'nearest' }); }
      }}><summary>View full original source</summary>
        <blockquote ref={full} tabIndex={-1}>{match ? <>{source.text.slice(0, match.start)}<mark>{source.text.slice(match.start, match.end)}</mark>{source.text.slice(match.end)}</> : source.text}</blockquote>
      </details>
    </>}
    <details className="technical-reference"><summary>Technical reference</summary><code>{id}</code></details>
  </section>;
}
export function SourceReferences({ ids, claim }: { ids: string[]; claim: string }) {
  const [open, setOpen] = useState(false);
  return <details className="item-provenance" onToggle={event => setOpen(event.currentTarget.open)}>
    <summary>Source references</summary>
    {open && (ids.length ? [...new Set(ids)].map(id => <SourceQuote key={id} id={id} claim={claim} />) : <p>No original source linked.</p>)}
  </details>;
}
export function revealReference(id: string) {
  const element = document.getElementById(`read-${id}`);
  if (!element) return;
  let parent = element.closest('details');
  while (parent) { parent.open = true; parent = parent.parentElement?.closest('details') || null; }
  document.querySelectorAll('.reference-highlight').forEach(node => node.classList.remove('reference-highlight'));
  element.classList.add('reference-highlight');
  element.focus({ preventScroll: true });
  element.scrollIntoView({ block: 'center', behavior: 'instant' });
}
