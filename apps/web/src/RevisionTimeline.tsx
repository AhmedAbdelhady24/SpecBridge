import { useEffect, useState } from 'react';
import type { components } from './api/schema';
import { ApiError, request } from './api/client';
import { DiffView } from './DiffView';
type S = components['schemas'];
export function RevisionTimeline({ token, project, run, revision, onAuthError, selectedRequests, onRequestSelection, disabled, onPending }: {
  onAuthError: () => void;
  token: string;
  project: string;
  run: string;
  revision: S['Revision'];
  selectedRequests: S['RequestChange'][];
  onRequestSelection: (value: S['RequestChange'][]) => void;
  disabled: boolean;
  onPending: (value: boolean) => void;
}) {
  const [entries, setEntries] = useState<S['FeatureRevision'][]>([]);
  const [requests, setRequests] = useState<S['RequestView'][]>([]);
  const [moreRequests, setMoreRequests] = useState(false);
  const [requestHistory, setRequestHistory] = useState<Record<string, S['RequestView'][]>>({});
  const [target, setTarget] = useState('');
  const [comparison, setComparison] = useState<S['RevisionComparison']>();
  const [base, setBase] = useState('');
  const [head, setHead] = useState('');
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [working, setWorking] = useState(false);
  const url = `/projects/${project}/runs/${run}`;
  useEffect(() => onPending(!!text.trim()), [text, onPending]);
  useEffect(() => {
    let active = true;
    Promise.all([request<S['FeatureRevision'][]>(token, url + '/history'), request<S['RequestView'][]>(token, url + '/change-requests')]).then(([h, r]) => {
      if (active) {
        setEntries(h);
        setRequests(r);
        setMoreRequests(r.length === 20);
        setHead(h[0]?.revision_id || '');
        setBase(h[0]?.parent_revision_id || h[0]?.revision_id || '');
      }
    }).catch(e => {
      if (active)
        { if (e instanceof ApiError && e.status === 401) onAuthError(); setError(e.message); }
    });
    return () => { active = false; };
  }, [token, url, revision.id]);
  async function act(op: () => Promise<void>) {
    setWorking(true);
    setError('');
    try {
      await op();
    }
    catch (e) {
      if (e instanceof ApiError && e.status === 401) onAuthError();
      setError(e instanceof Error ? e.message : 'Cannot load history');
    }
    finally {
      setWorking(false);
    }
  }
  return <section aria-label="Feature revision history"><h3>Changes & requests</h3>
    {error && <p role="alert" className="error">{error}</p>}
    <form onSubmit={e => { e.preventDefault(); void act(async () => { await request(token, url + '/change-requests', { base_revision_id: revision.id, text, target_ids: target ? [target] : [] }); setRequests(await request(token, url + '/change-requests')); setText(''); }); }}><label>Requested change<textarea aria-label="Requested change" required rows={3} maxLength={16384} value={text} onChange={e => setText(e.target.value)} disabled={disabled || working} /></label>
      <label>Target (optional)<select aria-label="Request target" value={target} onChange={e => setTarget(e.target.value)}><option value="">Whole draft</option>
        {revision.artifact.requirements.map((item, i) => <option key={item.id} value={item.id}>Requirement {i + 1}</option>)}
        {revision.artifact.stories.map((item, i) => <option key={item.id} value={item.id}>Story {i + 1}</option>)}</select></label>
      <button disabled={disabled || working || !text.trim()}>Record requested change</button></form>
    {requests.map(r => <article key={r.id} className="request-card"><p>{r.text}</p>
      <small>{r.status}
        {r.resolution_revision_id ? ' · linked to saved revision' : ''}</small>
      {r.status === 'open' && <label className="check"><input type="checkbox" checked={selectedRequests.some(s => s.request_id === r.id)} disabled={disabled} onChange={e => onRequestSelection(e.target.checked ? [...selectedRequests, { request_id: r.id, expected_version: r.version }] : selectedRequests.filter(s => s.request_id !== r.id))} />Address in next revision</label>}
      <details><summary onClick={() => void act(async () => setRequestHistory(h => ({ ...h, [r.id]: [] })))}>Request details</summary>
        <button type="button" disabled={working} className="secondary" onClick={() => void act(async () => setRequestHistory({ ...requestHistory, [r.id]: await request(token, url + `/change-requests/${r.id}/history`) }))}>Load request history</button>
        {requestHistory[r.id]?.map(event => <p key={event.version}>Version {event.version} · {event.status}
          {event.dismissal_reason ? ` · ${event.dismissal_reason}` : ''}</p>)}
        {(requestHistory[r.id]?.length || 0) >= 20 && <button type="button" className="secondary" disabled={working} onClick={() => void act(async () => setRequestHistory({ ...requestHistory, [r.id]: [...requestHistory[r.id], ...await request<S['RequestView'][]>(token, url + `/change-requests/${r.id}/history?before=${requestHistory[r.id].at(-1)!.version}`)] }))}>Load older request events</button>}
        <label>Reason for status change<input id={`request-reason-${r.id}`} maxLength={16384} /></label>
        <button type="button" className="secondary" disabled={disabled || working} onClick={() => void act(async () => {
          const reason = (document.getElementById(`request-reason-${r.id}`) as HTMLInputElement).value;
          if (!reason.trim())
            throw new Error('Supply a reason for this status change.');
          await request(token, url + `/change-requests/${r.id}/status`, { expected_version: r.version, status: r.status !== 'open' ? 'unanswered' : 'dismissed', reason });
          setRequests(await request(token, url + '/change-requests'));
        })}>{r.status !== 'open' ? 'Reopen requested change' : 'Dismiss requested change'}</button></details></article>)}
    {moreRequests && <button type="button" className="secondary" disabled={working} onClick={() => void act(async () => { const older = await request<S['RequestView'][]>(token, url + `/change-requests?before=${requests.at(-1)!.id}`); setRequests([...requests, ...older]); setMoreRequests(older.length === 20); })}>Load older requested changes</button>}
    <h4>Saved revisions</h4>
    <ol className="revision-timeline">{entries.map(r => <li key={r.revision_id}><strong>{r.feature_number ? `Revision ${r.feature_number}` : `Legacy revision ${r.legacy_number}`}</strong>
      <p>{r.change_summary || 'No change summary recorded.'}</p>
      <small>{r.created_at ? new Date(r.created_at).toLocaleString() : 'Creation time not recorded'}
        {r.parent_revision_id ? '' : ' · parent not recorded'}</small></li>)}</ol>
    {entries.length >= 20 && <button type="button" className="secondary" disabled={working} onClick={() => void act(async () => setEntries([...entries, ...await request<S['FeatureRevision'][]>(token, url + `/history?before=${entries.at(-1)!.legacy_number}`)]))}>Load older revisions</button>}
    {!!entries.length && <form onSubmit={e => { e.preventDefault(); void act(async () => setComparison(await request(token, url + `/compare?base=${encodeURIComponent(base)}&head=${encodeURIComponent(head)}`))); }}><label>Compare from<select aria-label="Compare from" value={base} onChange={e => setBase(e.target.value)}>{entries.map(r => <option value={r.revision_id} key={r.revision_id}>{r.feature_number ? `Revision ${r.feature_number}` : `Legacy ${r.legacy_number}`}</option>)}</select></label>
      <label>Compare to<select aria-label="Compare to" value={head} onChange={e => setHead(e.target.value)}>{entries.map(r => <option value={r.revision_id} key={r.revision_id}>{r.feature_number ? `Revision ${r.feature_number}` : `Legacy ${r.legacy_number}`}</option>)}</select></label>
      <button className="secondary" disabled={working || !base || !head}>Compare revisions</button></form>}
    {comparison && <><p>Historical comparison · read only</p>
      <DiffView base={comparison.base.artifact} head={comparison.head.artifact} />
      <details><summary>Decisions recorded with these revisions</summary>
        {([['Before', comparison.base_decisions], ['After', comparison.head_decisions]] as const).map(([label, snapshot]) => <section key={label}><h4>{label}</h4>
          {snapshot ? <>{(snapshot.questions || []).map(q => <div key={q.id}><strong>{q.text}</strong>
            <p>{q.latest_answer?.text || 'No answer recorded'}</p>
            <small>Resolution recorded in {q.resolution_revision_id}</small></div>)}
            {(snapshot.requests || []).map(r => <p key={r.id}>Addressed request: {r.text}</p>)}
            {!(snapshot.questions || []).length && !(snapshot.requests || []).length && <p>No incorporated decisions recorded.</p>}</> : <p>Decision history was not recorded for this revision.</p>}</section>)}</details></>}
  </section>;
}
