import { useEffect, useState } from "react";
import type { components } from "./api/schema";
import { request } from "./api/client";

type S = components["schemas"];
type Input = S["KnowledgeInput"];
const empty: Input = { entity_type: "goal", title: "", text: "", kind: "user_provided", source_ids: [], archived: false };

export function KnowledgePanel({ token, project, disabled, onSelect }: {
  token: string; project: string; disabled: boolean; onSelect: (source: S["Source"]) => void;
}) {
  const [entries, setEntries] = useState<S["KnowledgeEntry"][]>([]);
  const [selected, setSelected] = useState<S["KnowledgeEntry"]>();
  const [draft, setDraft] = useState<Input>(empty);
  const [evidence, setEvidence] = useState("");
  const [query, setQuery] = useState("");
  const [archived, setArchived] = useState(false);
  const [context, setContext] = useState<S["ContextItem"][]>([]);
  const [history, setHistory] = useState<S["KnowledgeEntry"][]>([]);
  const [revisions, setRevisions] = useState<S["RevisionSummary"][]>([]);
  const [savedRevision, setSavedRevision] = useState<S["Revision"]>();
  const [note, setNote] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [working, setWorking] = useState(false);
  const base = `/projects/${project}`;
  const api = <T,>(path: string, body?: unknown) => request<T>(token, base + path, body);
  useEffect(() => {
    let active = true;
    request<S["KnowledgeEntry"][]>(token, `/projects/${project}/knowledge`).then(v => { if (active) setEntries(v); }).catch(e => { if (active) setError(e instanceof Error ? e.message : "Cannot load knowledge"); });
    return () => { active = false; };
  }, [token, project]);
  async function act(operation: () => Promise<void>) {
    setWorking(true); setError(""); setNotice("");
    try { await operation(); } catch (e) { setError(e instanceof Error ? e.message : "Request failed"); } finally { setWorking(false); }
  }
  function edit(entry: S["KnowledgeEntry"]) {
    setSelected(entry);
    setDraft({ entity_type: entry.entity_type, title: entry.title, text: entry.text, kind: entry.kind === "verified" ? "user_provided" : entry.kind, source_ids: entry.source_ids, archived: entry.archived });
    setEvidence(entry.source_ids.join(", ")); setNote(""); setConfirm(false); setHistory([]);
  }
  function changeDraft(change: Partial<Input>) {
    setDraft(current => ({ ...current, ...change }));
    setConfirm(false);
  }
  const unsaved = selected !== undefined && (
    draft.title !== selected.title || draft.text !== selected.text ||
    draft.entity_type !== selected.entity_type || draft.archived !== selected.archived ||
    draft.kind !== (selected.kind === "verified" ? "user_provided" : selected.kind)
  );
  const sourceIds = () => evidence.split(",").map(s => s.trim()).filter(Boolean);
  const reload = async () => setEntries(await api<S["KnowledgeEntry"][]>(`/knowledge?query=${encodeURIComponent(query)}&include_archived=${archived}`));
  async function save() {
    const body = { ...draft, source_ids: sourceIds() };
    const value = await api<S["KnowledgeEntry"]>(selected ? `/knowledge/${selected.id}/edits` : "/knowledge", selected ? { expected_digest: selected.digest, entry: body } : body);
    edit(value); await reload(); setNotice("Knowledge version saved.");
  }
  async function selectContext(item: S["ContextItem"]) {
    const source = item.resource_type === "knowledge"
      ? await api<S["Source"]>(`/knowledge/${item.id}/sources`, { version: item.version, expected_digest: item.digest })
      : await api<S["Source"]>(`/sources/${item.id}`);
    onSelect(source); setNotice("Exact context snapshot selected for the next generation.");
  }
  return <details className="panel knowledge-panel">
    <summary>Project knowledge</summary>
    <p>Save project context with evidence labels. Selecting context captures an exact version; it does not approve a draft.</p>
    {error && <div role="alert" className="error">{error}</div>}
    <div role="status" aria-live="polite">{working ? "Saving or loading…" : notice}</div>
    <fieldset disabled={disabled || working}>
      <legend>Knowledge record</legend>
      {selected && <p>Current classification: {selected.kind}</p>}
      <form onSubmit={e => { e.preventDefault(); void act(save); }}>
        <label htmlFor="knowledge-type">Knowledge type</label><select id="knowledge-type" value={draft.entity_type} onChange={e => changeDraft({ entity_type: e.target.value as Input["entity_type"] })}>
          {(["goal", "stakeholder", "decision", "risk", "dependency", "api_reference", "conversation"] as const).map(t => <option key={t} value={t}>{t.replaceAll("_", " ")}</option>)}
        </select>
        <label>Knowledge title<input required maxLength={200} value={draft.title} onChange={e => changeDraft({ title: e.target.value })} /></label>
        <label htmlFor="knowledge-text">Knowledge text</label><textarea id="knowledge-text" required maxLength={16384} rows={4} value={draft.text} onChange={e => changeDraft({ text: e.target.value })} />
        <label htmlFor="knowledge-kind">Evidence kind</label><select id="knowledge-kind" value={draft.kind} onChange={e => changeDraft({ kind: e.target.value as Input["kind"] })}>
          {(["user_provided", "recommendation", "assumption", "unknown"] as const).map(t => <option key={t} value={t}>{t.replaceAll("_", " ")}</option>)}
        </select>
        <label>Evidence source IDs<input value={evidence} onChange={e => { setEvidence(e.target.value); setConfirm(false); }} placeholder="Comma-separated source IDs from this project" /></label>
        <label className="check"><input type="checkbox" checked={draft.archived} onChange={e => changeDraft({ archived: e.target.checked })} />Archive entry</label>
        <button disabled={!draft.title.trim() || !draft.text.trim()}>Save knowledge</button>{" "}
        <button type="button" className="secondary" onClick={() => { setSelected(undefined); setDraft(empty); setEvidence(""); setHistory([]); setNote(""); setConfirm(false); }}>New entry</button>
      </form>
      {selected && <div>
        <p>Human verification records your judgment against original source evidence. It does not approve an artifact. Saving an edit removes prior verification.</p>
        {unsaved && <p>Save the edited record before recording verification.</p>}
        <label htmlFor="verification-note">Verification note</label><textarea id="verification-note" rows={2} value={note} onChange={e => { setNote(e.target.value); setConfirm(false); }} />
        <label className="check"><input type="checkbox" checked={confirm} onChange={e => setConfirm(e.target.checked)} />I confirm this knowledge against the cited original evidence</label>
        <button type="button" className="secondary" disabled={unsaved || !confirm || !note.trim() || !sourceIds().length} onClick={() => void act(async () => {
          if (unsaved) throw new Error("Save the edited record before verifying it.");
          const value = await api<S["KnowledgeEntry"]>(`/knowledge/${selected.id}/verify`, { expected_digest: selected.digest, source_ids: sourceIds(), note, confirm: true });
          edit(value); await reload(); setNotice("Human verification recorded for this version.");
        })}>Record human verification</button>
      </div>}
      <form onSubmit={e => { e.preventDefault(); void act(async () => { await reload(); setContext(await api<S["ContextItem"][]>(`/context?query=${encodeURIComponent(query)}`)); }); }}>
        <label>Context search<input maxLength={200} value={query} onChange={e => setQuery(e.target.value)} /></label>
        <label className="check"><input type="checkbox" checked={archived} onChange={e => setArchived(e.target.checked)} />Include archived records in the list</label>
        <button className="secondary">Search context</button>
      </form>
      <h3>Current records</h3>
      {!entries.length && <p>No matching records. Save a record or search by its title or content.</p>}
      {entries.map(entry => <article key={entry.id}>
        <h4>{entry.title}</h4><p>{entry.entity_type.replaceAll("_", " ")} · {entry.kind} · version {entry.version}{entry.archived ? " · archived" : ""}</p>
        <p>{entry.text}</p><p>Sources: {entry.source_ids.join(", ") || "No supporting source linked"}</p>
        <button type="button" className="secondary" onClick={() => edit(entry)}>Edit {entry.title}</button>{" "}
        <button type="button" className="secondary" onClick={() => void act(async () => setHistory(await api<S["KnowledgeEntry"][]>(`/knowledge/${entry.id}/history`)))}>History {entry.title}</button>
      </article>)}
      {!!history.length && <section aria-label="Knowledge version history"><h3>Knowledge version history</h3>{history.map(v => <article key={v.version}><h4>Version {v.version} · {v.kind}</h4><p>{v.text}</p>{v.verification_note && <p>Verification: {v.verification_note}</p>}</article>)}</section>}
      {!!context.length && <section aria-label="Context results"><h3>Context results</h3>{context.map(item => <article key={`${item.resource_type}:${item.id}`}>
        <h4>{item.title}</h4><p>{item.kind}{item.version ? ` · version ${item.version}` : ""}</p><p>{item.text}</p><p>Reference: {item.id}</p>
        <button type="button" className="secondary" onClick={() => void act(() => selectContext(item))}>Select context: {item.title}</button>
      </article>)}</section>}
      <h3>Artifact revisions</h3>
      <button type="button" className="secondary" onClick={() => void act(async () => setRevisions(await api<S["RevisionSummary"][]>("/revisions")))}>Load artifact history</button>
      {revisions.map(r => <div key={r.id}><button type="button" className="secondary" onClick={() => void act(async () => setSavedRevision(await api<S["Revision"]>(`/revisions/${r.id}`)))}>View revision {r.number}: {r.title}</button></div>)}
      {savedRevision && <section aria-label="Saved artifact revision"><h3>Saved revision {savedRevision.number}</h3><h4>{savedRevision.artifact.title}</h4><p>{savedRevision.artifact.purpose}</p>
        {savedRevision.artifact.stories.map(s => <article key={s.id}><p>{s.text}</p><p>Requirements: {s.requirement_ids.join(", ")}</p><ul>{s.acceptance_criteria.map((c, i) => <li key={i}>{c}</li>)}</ul></article>)}
        <h4>Open questions</h4><ul>{savedRevision.artifact.open_questions.map((q, i) => <li key={i}>{q}</li>)}</ul>
      </section>}
    </fieldset>
  </details>;
}
