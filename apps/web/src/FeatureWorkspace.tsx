import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import type { components } from './api/schema';
import { request, ApiError } from './api/client';
import { WorkspaceShell, type WorkspaceTask } from './WorkspaceShell';
import { ReferenceProvider } from './SourceReferences';
import { DecisionQueue, type Amendment } from './DecisionQueue';
import { ArtifactWorkspace } from './ArtifactWorkspace';
import { ArtifactPreview } from './ArtifactPreview';
import { DiffView } from './DiffView';
import { RevisionTimeline } from './RevisionTimeline';
import { ReviewPanel } from './ReviewPanel';
type S = components['schemas'];
export function FeatureWorkspace({ token, project, run, revision, disabled, onDirty, onSaved, onAuthError, review, reviewRequest }: {
  onAuthError: () => void;
  token: string;
  project: string;
  run: string;
  revision: S['Revision'];
  disabled: boolean;
  onDirty: (value: boolean) => void;
  onSaved: (revision: S['Revision']) => Promise<void>;
  review: ReactNode;
  reviewRequest: number;
}) {
  const [pendingChat, setPendingChat] = useState(false);
  const [chatRequests, setChatRequests] = useState<S["RequestView"][]>([]);
  const [requestRefresh, setRequestRefresh] = useState(0);
  const [pendingRequest, setPendingRequest] = useState(false);
  const [task, setTask] = useState<WorkspaceTask>('questions');
  const [pane, setPane] = useState<'task' | 'draft'>('draft');
  useEffect(() => {
    if (reviewRequest) {
      setTask('review');
      setPane('task');
    }
  }, [reviewRequest]);
  useLayoutEffect(() => {
    if (reviewRequest && task === 'review' && pane === 'task')
      document.getElementById('package-heading')?.focus();
  }, [reviewRequest, task, pane]);
  const [value, setValue] = useState(revision.artifact);
  const [questions, setQuestions] = useState<S['QuestionView'][]>([]);
  const [selected, setSelected] = useState('');
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [amendments, setAmendments] = useState<Record<string, Amendment>>({});
  const [questionChanges, setQuestionChanges] = useState<S['QuestionChange'][]>([]);
  const [requestChanges, setRequestChanges] = useState<S['RequestChange'][]>([]);
  const [answerHistory, setAnswerHistory] = useState<Record<string, S['AnswerVersion'][]>>({});
  const [recoverable, setRecoverable] = useState<S['WorkingCopy'] | null>(null);
  const [workingVersion, setWorkingVersion] = useState(0);
  const [featureNumber, setFeatureNumber] = useState<number | null>(null);
  const [summary, setSummary] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showSaved, setShowSaved] = useState(false);
  const [inspectStale, setInspectStale] = useState(false);
  const [confirmReconcile, setConfirmReconcile] = useState(false);
  const commitKey = useRef<string | undefined>(undefined);
  const [commitAttempt, setCommitAttempt] = useState<{
    key: string;
    version: number;
  }>();
  const base = `/projects/${project}`;
  const url = `${base}/runs/${run}`;
  const docDirty = JSON.stringify(value) !== JSON.stringify(revision.artifact);
  const initializedRevision = useRef('');
  const [pendingAmendments, setPendingAmendments] = useState<Record<string, boolean>>({});
  const pendingAmendment = Object.values(pendingAmendments).some(Boolean);
  const pendingAnswers = questions.some(q => answers[q.id] !== undefined && answers[q.id] !== (q.latest_answer?.text || ''));
  useEffect(() => onDirty(docDirty || pendingChat || pendingAmendment || pendingAnswers || pendingRequest || requestChanges.length > 0), [docDirty, pendingChat, pendingAmendment, pendingAnswers, pendingRequest, requestChanges.length, onDirty]);
  useEffect(() => {
    if (initializedRevision.current === revision.id) return;
    let active = true;
    setLoading(true);
    setError('');
    Promise.all([request<S['QuestionView'][]>(token, url + '/questions'), request<S['WorkingCopy'] | null>(token, url + '/working-copy'), request<S['FeatureRevision'][]>(token, url + '/history'), request<S['RequestView'][]>(token, url + '/change-requests')]).then(([qs, copy, history, requests]) => {
      if (active) {
        initializedRevision.current = revision.id;
        setMessage('');
        setQuestions(qs);
        setChatRequests(requests);
        setSelected(qs.find(q => q.in_current_draft)?.id || qs[0]?.id || '');
        setValue(revision.artifact);
        setRecoverable(copy);
        setWorkingVersion(0);
        setQuestionChanges([]);
        setRequestChanges([]);
        setFeatureNumber(history.find(h => h.revision_id === revision.id)?.feature_number ?? null);
        setAnswers({});
        setAmendments({});
        setPendingAmendments({});
        setShowSaved(false);
        setSummary('');
        setCommitAttempt(undefined);
        commitKey.current = undefined;
      }
    }).catch(e => {
      if (active)
        { if (e instanceof ApiError && e.status === 401) onAuthError(); setError(e.message); }
    }).finally(() => {
      if (active)
        setLoading(false);
    });
    return () => { active = false; };
  }, [token, url, revision.id, revision.artifact]);
  async function act<T>(op: () => Promise<T>) {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      await op();
    }
    catch (e) {
      if (e instanceof ApiError && e.status === 401) onAuthError();
      setError(e instanceof ApiError && e.code === 'invalid_input' ? 'Check story links, evidence and explicit question changes. Resolve duplicated questions separately from other question-list edits.' : e instanceof Error ? e.message : 'The operation failed. Your local work is retained.');
    }
    finally {
      setBusy(false);
    }
  }
  async function reloadQuestions() { setQuestions(await request(token, url + '/questions')); }
  const q = questions.find(item => item.id === selected);
  const answer = q ? (answers[q.id] ?? q.latest_answer?.text ?? '') : '';
  const amendment: Amendment = q ? (amendments[q.id] ?? { text: q.latest_answer?.text || '', target: 'scope', story: '', criteria: '' }) : { text: '', target: 'scope', story: '', criteria: '' };
  const locked = disabled || busy || loading;
  const editLocked = locked || !!recoverable || !!commitAttempt;
  function change(next: S['Artifact']) { setValue(next); setShowSaved(false); setMessage(''); }
  function preview() {
    if (!q?.latest_answer || !q.in_current_draft || q.current_index === null || q.current_index === undefined)
      throw new Error('Select an answered current question.');
    const next = structuredClone(value);
    const statement = { text: amendment.text, source_ids: [q.latest_answer.source_id], kind: amendment.text === q.latest_answer.text ? 'user_provided' as const : 'recommendation' as const };
    let targetId = amendment.target;
    if (amendment.target === 'scope')
      next.scope.push(statement);
    else if (amendment.target === '_new') {
      const id = `REQ-${crypto.randomUUID()}`;
      const criteria = amendment.criteria.split('\n').map(s => s.trim()).filter(Boolean);
      if (!amendment.story.trim() || !criteria.length || criteria.length > 30)
        throw new Error('Supply a story and 1–30 acceptance criteria.');
      next.requirements.push({ ...statement, id });
      next.stories.push({ id: `STORY-${crypto.randomUUID()}`, text: amendment.story, kind: 'recommendation', source_ids: [q.latest_answer.source_id], requirement_ids: [id], acceptance_criteria: criteria });
      targetId = id;
    }
    else if (next.requirements.some(r => r.id === amendment.target))
      next.requirements = next.requirements.map(r => r.id === amendment.target ? { ...r, ...statement } : r);
    else if (next.stories.some(s => s.id === amendment.target))
      next.stories = next.stories.map(s => s.id === amendment.target ? { ...s, ...statement } : s);
    else
      throw new Error('Choose an existing target or append a new scope item.');
    const existing = questionChanges.find(c => c.question_id === q.id);
    if (!existing) {
      const earlier = questionChanges.filter(c => c.action === 'resolve' && (questions.find(item => item.id === c.question_id)?.current_index ?? Infinity) < q.current_index!).length;
      const index = q.current_index - earlier;
      if (next.open_questions[index] !== q.text)
        throw new Error('Question order changed. Discard the amendment and reconcile before resolving.');
      next.open_questions.splice(index, 1);
    }
    setQuestionChanges([...questionChanges.filter(c => c.question_id !== q.id), { question_id: q.id, expected_question_version: q.version, answer_version: q.latest_answer.version, action: 'resolve', targets: [...new Set([...(existing?.targets || []), targetId])] }]);
    setPendingAmendments(current => ({ ...current, [q.id]: false }));
    change(next);
    setMessage('Amendment is visible in the working preview only. Save a revision to incorporate it.');
    const target = document.getElementById(`read-${amendment.target}`);
    const disclosure = target?.closest('details');
    if (disclosure)
      disclosure.open = true;
  }
  async function persist() {
    if (pendingAmendment)
      throw new Error('Preview or discard your unpreviewed amendment text before saving.');
    if (pendingAnswers)
      throw new Error('Save or restore your pending answers first.');
    const saved = await request<S['WorkingCopy']>(token, url + '/working-copy', { expected_version: workingVersion, base_revision_id: revision.id, base_digest: revision.digest, artifact: value, question_changes: questionChanges, request_changes: requestChanges, change_summary: summary }, false, 'PUT');
    setWorkingVersion(saved.version);
    setMessage('Working preview saved privately. It is not a revision.');
    return saved;
  }
  async function saveRevision() {
    const copy = await persist();
    const key = commitKey.current || crypto.randomUUID();
    commitKey.current = key;
    setCommitAttempt({ key, version: copy.version });
    let receipt: S['CommitReceipt'];
    try {
      receipt = await request<S['CommitReceipt']>(token, url + '/commits', { working_copy_version: copy.version, idempotency_key: key });
    }
    catch (e) {
      if (e instanceof ApiError && [409, 422].includes(e.status)) {
        setCommitAttempt(undefined);
        commitKey.current = undefined;
      }
      throw e;
    }
    await onSaved(await request<S['Revision']>(token, `${base}/revisions/${receipt.revision_id}`));
    setCommitAttempt(undefined);
    commitKey.current = undefined;
  }
  function resume(copy: S['WorkingCopy']) { change(copy.artifact); setQuestionChanges(copy.question_changes || []); setRequestChanges(copy.request_changes || []); setSummary(copy.change_summary || ''); setWorkingVersion(copy.version); setRecoverable(null); setInspectStale(false); }
  async function discard() {
    if (workingVersion)
      await request(token, url + '/working-copy', { expected_version: workingVersion }, false, 'DELETE');
    setValue(revision.artifact);
    setQuestionChanges([]);
    setRequestChanges([]);
    setWorkingVersion(0);
    setShowSaved(false);
    setAmendments({});
    setPendingAmendments({});
    setMessage('Amendments discarded. Saved answers are retained.');
  }
  const selectedPending = !!q && answers[q.id] !== undefined && answers[q.id] !== (q.latest_answer?.text || '');
  return <ReferenceProvider token={token} project={project} onAuthError={onAuthError}><div className="feature-review">
    {error && <p role="alert" className="error">{error}</p>}
    <p role="status">{loading ? 'Loading saved feature…' : busy ? 'Saving or loading your work…' : message}</p>
    {pendingAmendment && <aside className="unsaved-notice"><p>Amendment form changes have not been previewed.</p><button type="button" disabled={locked} className="secondary" onClick={() => { setAmendments({}); setPendingAmendments({}); }}>Discard unpreviewed amendment text</button></aside>}
    {recoverable && <aside className="recovery-banner"><strong>A saved working preview is available.</strong>
      {recoverable.base_revision_id === revision.id ? <button type="button" disabled={locked} onClick={() => resume(recoverable)}>Resume working preview</button> : <><p>The saved preview uses an older revision. Inspect differences before reconciling.</p>
        <button type="button" onClick={() => setInspectStale(true)}>Inspect saved differences</button>
        {inspectStale && <><DiffView base={revision.artifact} head={recoverable.artifact} />
          <label className="check"><input type="checkbox" checked={confirmReconcile} onChange={e => setConfirmReconcile(e.target.checked)} />I compared the saved preview with the current revision</label>
          <button type="button" disabled={!confirmReconcile || locked} onClick={() => resume(recoverable)}>Reconcile preview onto current revision</button></>}</>}
      <button type="button" className="secondary" disabled={locked} onClick={() => void act(async () => { await request(token, url + '/working-copy', { expected_version: recoverable.version }, false, 'DELETE'); setRecoverable(null); setMessage('Saved preview discarded. Answers are retained.'); })}>Discard saved preview</button></aside>}
    {commitAttempt && <aside className="unsaved-notice"><p>The revision save was not confirmed. Resolve this attempt before editing or saving different work.</p>
      <button type="button" disabled={locked} onClick={() => void act(async () => { const receipt = await request<S['CommitReceipt']>(token, url + '/commits', { working_copy_version: commitAttempt.version, idempotency_key: commitAttempt.key }); await onSaved(await request(token, `${base}/revisions/${receipt.revision_id}`)); setCommitAttempt(undefined); commitKey.current = undefined; })}>Check or retry this revision save</button>
      <button type="button" className="secondary" disabled={locked} onClick={() => { setCommitAttempt(undefined); commitKey.current = undefined; setMessage('Attempt released. Compare current saved state before changing your preview.'); }}>Keep preview for reconciliation</button></aside>}
    <WorkspaceShell pane={pane} onPane={setPane} task={task} onTask={setTask} tasks={<>
      <div className="conversation-task" hidden={task !== 'questions'}><DecisionQueue messages={chatRequests} onPending={setPendingChat} onRequest={async text => { let saved = false; await act(async () => { const recorded = await request<S['RequestView']>(token, url + '/change-requests', { base_revision_id: revision.id, text, target_ids: [] }); setChatRequests(current => [recorded, ...current]); setRequestRefresh(n => n + 1); setMessage('Change request recorded. The draft is unchanged.'); saved = true; }); return saved; }} questions={questions} selected={q} onSelect={id => { setSelected(id); }} answer={answer} onAnswer={text => {
        if (q)
          setAnswers({ ...answers, [q.id]: text });
        setMessage('');
      }} amendment={amendment} onAmendment={next => {
        if (q) {
          setAmendments({ ...amendments, [q.id]: next });
          setPendingAmendments(current => ({ ...current, [q.id]: true }));
        }
      }} artifact={value} disabled={editLocked} pending={selectedPending} onSave={() => void act(async () => {
        if (!q)
          return;
        await request(token, url + `/questions/${q.id}/answers`, { expected_version: q.version, text: answer });
        await reloadQuestions();
        setMessage('Answer saved. The draft is unchanged.');
      })} onPreview={() => void act(async () => preview())} onStatus={(status, reason) => void act(async () => {
        if (q) {
          await request(token, url + `/questions/${q.id}/status`, { expected_version: q.version, status, reason });
          await reloadQuestions();
        }
      })} onReopen={() => void act(async () => {
        if (!q?.latest_answer)
          throw new Error('This decision has no saved answer to reopen.');
        if (questionChanges.some(c => c.question_id === q.id))
          throw new Error('This question already has a pending amendment.');
        change({ ...value, open_questions: [...value.open_questions, q.text] });
        setQuestionChanges([...questionChanges, { question_id: q.id, expected_question_version: q.version, answer_version: q.latest_answer.version, action: 'reopen', targets: ['scope'] }]);
        setMessage('Question reopening is in the preview only. Save a revision to apply it.');
      })} history={answerHistory[selected] || []} onHistory={() => void act(async () => {
        if (q) {
          const history = await request<S['AnswerVersion'][]>(token, url + `/questions/${q.id}/answers`);
          setAnswerHistory(current => ({ ...current, [q.id]: history }));
        }
      })} />
        {pendingAnswers && <button type="button" className="secondary" disabled={locked} onClick={() => setAnswers({})}>Restore saved answers</button>}</div>
      <div hidden={task !== 'changes'}><RevisionTimeline onRequests={setChatRequests} refresh={requestRefresh} onAuthError={onAuthError} token={token} project={project} run={run} revision={revision} onPending={setPendingRequest} selectedRequests={requestChanges} onRequestSelection={setRequestChanges} disabled={editLocked} /></div>
      <div hidden={task !== 'review'}><ReviewPanel>{review}</ReviewPanel></div>
    </>} document={<>
      <div className="revision-line"><strong>{featureNumber ? `Revision ${featureNumber}` : `Legacy revision ${revision.number}`}</strong>
        <span className="evidence-badge">{docDirty && !showSaved ? 'Working preview' : 'Saved draft'}</span></div>
      {docDirty && <><p className="unsaved-notice">Proposed amendments. The saved specification has not changed.</p>
        <div className="actions"><button type="button" className="secondary" aria-pressed={showSaved} onClick={() => setShowSaved(!showSaved)}>{showSaved ? 'Return to working preview' : 'View saved draft'}</button>
          <button type="button" className="secondary" disabled={editLocked} onClick={() => void act(persist)}>Save working preview</button></div>
        <label>Change summary<input maxLength={2000} value={summary} disabled={editLocked} onChange={e => setSummary(e.target.value)} /></label>
        <details><summary>Working changes</summary>
          <DiffView base={revision.artifact} head={value} /></details></>}
      {showSaved ? <ArtifactPreview value={revision.artifact} /> : <ArtifactWorkspace revision={revision} original={docDirty ? revision.artifact : undefined} value={value} disabled={editLocked} dirty={docDirty} onChange={change} onSave={() => void act(saveRevision)} onDiscard={() => void act(discard)} />}
      <details><summary>Validation & technical details</summary>
        <p>Structural checks do not verify facts. Review all claims before approval.</p>
        {(revision.findings || []).map((f, i) => <p key={i}>{f.message}</p>)}
        <p>Legacy reference: {revision.number}</p>
        <p>Artifact digest: <code>{revision.digest}</code></p>
        <dl>{Object.entries(revision.provenance || {}).map(([k, v]) => <div key={k}><dt>{k.replaceAll('_', ' ')}</dt>
          <dd>{v}</dd></div>)}</dl></details>
    </>} />
  </div></ReferenceProvider>;
}
