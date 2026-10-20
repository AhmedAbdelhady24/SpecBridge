import { useState } from 'react';
export function ChatComposer({ answer, onAnswer, onSave, onRequest, onPending, disabled, canAnswer, pending }: {
  answer: string; onAnswer: (text: string) => void; onSave: () => void;
  onRequest: (text: string) => Promise<boolean>; onPending: (pending: boolean) => void;
  disabled: boolean; canAnswer: boolean; pending: boolean;
}) {
  const [intent, setIntent] = useState<'answer' | 'request'>('answer');
  const [message, setMessage] = useState('');
  return <div className="chat-composer">
    <div className="composer-intent" aria-label="Message intent">
      <button type="button" className="secondary" aria-pressed={intent === 'answer'} onClick={() => setIntent('answer')}>Answer question</button>
      <button type="button" className="secondary" aria-pressed={intent === 'request'} onClick={() => setIntent('request')}>Request a change</button>
    </div>
    {intent === 'answer' ? <>
      <label>Your answer<textarea aria-label="Your answer" rows={3} maxLength={16384} value={answer} disabled={disabled || !canAnswer} placeholder="Reply to the selected question…" onChange={e => onAnswer(e.target.value)} /></label>
      <p className="muted">{pending ? 'Not saved yet.' : 'Saved answers remain separate from the specification.'}</p>
      <button type="button" disabled={disabled || !canAnswer || !answer.trim()} onClick={onSave}>Save answer</button>
    </> : <>
      <label>Message<textarea aria-label="Message" rows={3} maxLength={16384} value={message} disabled={disabled} placeholder="Describe the change you want reviewed…" onChange={e => { setMessage(e.target.value); onPending(!!e.target.value.trim()); }} /></label>
      <p className="muted">Records a change request. Preview and save a revision to apply changes; no AI call is made.</p>
      <p className="muted annotation-tip">💡 Tip: You can also click <strong>💬 Request change</strong> directly on any requirement or story in the draft to annotate that specific line.</p>
      <button type="button" disabled={disabled || !message.trim()} onClick={() => void onRequest(message).then(saved => { if (saved) { setMessage(''); onPending(false); } })}>Send change request</button>
      {message && <button type="button" className="secondary" disabled={disabled} onClick={() => { setMessage(''); onPending(false); }}>Discard message</button>}
    </>}
  </div>;
}
