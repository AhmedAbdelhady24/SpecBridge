import type { components } from './api/schema';
type S = components['schemas'];
export type Amendment = {
  text: string;
  target: string;
  story: string;
  criteria: string;
};
export function DecisionQueue({ questions, selected, onSelect, answer, onAnswer, amendment, onAmendment, artifact, disabled, onSave, onPreview, onStatus, onReopen, history, onHistory, pending }: {
  questions: S['QuestionView'][];
  selected?: S['QuestionView'];
  onSelect: (id: string) => void;
  answer: string;
  onAnswer: (text: string) => void;
  amendment: Amendment;
  onAmendment: (value: Amendment) => void;
  artifact: S['Artifact'];
  disabled: boolean;
  onSave: () => void;
  onPreview: () => void;
  onStatus: (status: 'dismissed' | 'unanswered', reason: string) => void;
  onReopen: () => void;
  history: S['AnswerVersion'][];
  onHistory: () => void;
  pending: boolean;
}) {
  return <section aria-label="Questions and decisions"><h3>Questions & decisions</h3>
    <p>Save your answer first. Preview an amendment, then save a revision to incorporate it.</p>
    {!questions.length && <p>No questions recorded for this feature.</p>}
    {selected && <div className="decision-card"><h4>{selected.text}</h4>
      <p className="evidence-badge">{selected.status === 'answered' ? 'Answer saved' : selected.status === 'unresolved' ? 'Unanswered' : selected.status}
        {selected.resolution_revision_id ? ' · linked to a saved revision' : ''}</p>
      {!selected.in_current_draft && <p>This question is in decision history, outside the current draft.</p>}
      {selected.status === 'resolved' ? <><p>{selected.latest_answer?.text}</p>
        <button type="button" disabled={disabled} onClick={onReopen}>Preview reopening this question</button></> : <>
        <label>Your answer<textarea aria-label="Your answer" rows={4} maxLength={16384} value={answer} disabled={disabled || selected.status === 'dismissed'} onChange={e => onAnswer(e.target.value)} /></label>
        <p className="muted">{pending ? 'Not saved yet.' : 'Saved answers remain separate from the specification.'}</p>
        <button type="button" disabled={disabled || !answer.trim() || selected.status === 'dismissed'} onClick={onSave}>Save answer</button>
        {selected.latest_answer && selected.status === 'answered' && selected.in_current_draft && <form onSubmit={e => { e.preventDefault(); onPreview(); }}>
          <label>Amendment target<select aria-label="Amendment target" value={amendment.target} disabled={disabled} onChange={e => onAmendment({ ...amendment, target: e.target.value })}><option value="scope">Append to scope</option>
            <option value="_new">New requirement and linked story</option>
            {artifact.requirements.map((r, i) => <option key={r.id} value={r.id}>Requirement {i + 1}: {r.text.slice(0, 65)}</option>)}
            {artifact.stories.map((s, i) => <option key={s.id} value={s.id}>Story {i + 1}: {s.text.slice(0, 65)}</option>)}</select></label>
          <label>Amendment text<textarea aria-label="Amendment text" required maxLength={16384} rows={3} disabled={disabled} value={amendment.text} onChange={e => onAmendment({ ...amendment, text: e.target.value })} /></label>
          {amendment.target === '_new' && <><label>New story<textarea aria-label="New story" required maxLength={16384} value={amendment.story} onChange={e => onAmendment({ ...amendment, story: e.target.value })} /></label>
            <label>Acceptance criteria (one per line)<textarea aria-label="Acceptance criteria (one per line)" required maxLength={16384} value={amendment.criteria} onChange={e => onAmendment({ ...amendment, criteria: e.target.value })} /></label></>}
          <p className="muted">Use your own wording. This action makes no AI call. Preview another target to amend several sections.</p>
          <button disabled={disabled || pending}>Preview amendment</button>
        </form>}
        <details><summary>Question options</summary>
          <label>Reason<input id={`reason-${selected.id}`} maxLength={16384} /></label>
          <button type="button" className="secondary" disabled={disabled} onClick={() => {
            const input = document.getElementById(`reason-${selected.id}`) as HTMLInputElement;
            if (input.value.trim())
              onStatus(selected.status === 'dismissed' ? 'unanswered' : 'dismissed', input.value);
            else {
              input.setCustomValidity('Explain this status change');
              input.reportValidity();
              input.setCustomValidity('');
            }
          }}>{selected.status === 'dismissed' ? 'Reopen question' : 'Dismiss question'}</button></details>
      </>}
      <details><summary onClick={onHistory}>Answer history</summary>
        {history.length ? history.map(a => <div key={a.version}><strong>Answer version {a.version}</strong>
          <p>{a.text}</p>
          <small>{new Date(a.created_at).toLocaleString()}</small></div>) : <p>No saved answers loaded.</p>}</details>
    </div>}
    <ol className="question-list">{questions.map((q, i) => <li key={q.id}><button type="button" className="secondary" aria-current={selected?.id === q.id ? 'true' : undefined} onClick={() => onSelect(q.id)}>{i + 1}. {q.text}</button>
      <small>{q.status === 'unresolved' ? 'Unanswered' : q.status}
        {!q.in_current_draft ? ' · history' : ''}</small></li>)}</ol>
  </section>;
}
