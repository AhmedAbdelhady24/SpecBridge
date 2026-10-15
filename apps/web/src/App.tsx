import { useState } from "react";
import type { components } from "./api/schema";
import { ApiError, request } from "./api/client";
import { ArtifactEditor } from "./ArtifactEditor";
type Schema = components["schemas"];
export default function App() {
  const [token, setToken] = useState("");
  const [config, setConfig] = useState<Schema["ProviderInfo"]>();
  const [projects, setProjects] = useState<Schema["Project"][]>([]);
  const [project, setProject] = useState("");
  const [name, setName] = useState("");
  const [idea, setIdea] = useState("");
  const [ack, setAck] = useState(false);
  const [retry, setRetry] = useState(false);
  const [runs, setRuns] = useState<Schema["Run"][]>([]);
  const [selectedRun, setSelectedRun] = useState("");
  const [selectedSources, setSelectedSources] = useState<Schema["Source"][]>([]);
  const [run, setRun] = useState<Schema["Run"]>();
  const [revision, setRevision] = useState<Schema["Revision"]>();
  const [artifact, setArtifact] = useState<Schema["Artifact"]>();
  const [candidate, setCandidate] = useState<Schema["Candidate"]>();
  const [notes, setNotes] = useState("");
  const [reviewed, setReviewed] = useState(false);
  const [reviewStatus, setReviewStatus] = useState("");
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const base = `/projects/${project}`;
  const api = <T,>(
    path: string,
    body?: unknown,
    blob = false,
    method?: string,
  ) => request<T>(token, path, body, blob, method);
  async function act(operation: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setConfig(undefined);
        setToken("");
      }
      setError(
        e instanceof Error ? e.message : "The request could not be completed.",
      );
    } finally {
      setBusy(false);
    }
  }
  function clearRevision() {
    setRevision(undefined);
    setArtifact(undefined);
    setCandidate(undefined);
    setReviewed(false);
    setReviewStatus("");
    setDirty(false);
    setNotes("");
  }
  async function loadRevision(id: string) {
    const value = await api<Schema["Revision"]>(`${base}/revisions/${id}`);
    clearRevision();
    setRevision(value);
    setArtifact(value.artifact);
  }
  async function chooseProject(id: string) {
    setProject(id);
    setRun(undefined);
    setRuns([]);
    setSelectedRun("");
    setSelectedSources([]);
    clearRevision();
    if (id) setRuns(await api<Schema["Run"][]>(`/projects/${id}/runs`));
  }
  async function progress(initial: Schema["Run"], retryAcknowledged = false) {
    let current = initial;
    try {
      for (
        let i = 0;
        i < 6 && current.status !== "review" && current.status !== "published";
        i++
      ) {
        current = await api<Schema["Run"]>(
          `${base}/runs/${initial.id}/advance`,
          { retry_acknowledged: i === 0 && retryAcknowledged },
        );
        setRun(current);
      }
    } catch (e) {
      try {
        current = await api<Schema["Run"]>(`${base}/runs/${initial.id}`);
        setRun(current);
      } catch {
        /* Preserve last durable state when recovery read also fails. */
      }
      throw e;
    } finally {
      setRetry(false);
    }
    setRuns(await api<Schema["Run"][]>(`${base}/runs`));
    if (current.revision_id) await loadRevision(current.revision_id);
  }
  async function generate() {
    const source = await api<Schema["Source"]>(`${base}/sources`, {
      text: idea,
    });
    const skills = await api<Schema["SkillMetadata"][]>(
      `/skills?intent=${encodeURIComponent("feature handoff")}`,
    );
    if (!skills.length) throw new Error("No runtime skill is available.");
    const created = await api<Schema["Run"]>(`${base}/runs`, {
      source_ids: [source.id],
      skill_id: skills[0].name,
      intent: "feature handoff",
      acknowledged_destination: config!.destination,
    });
    clearRevision();
    setRun(created);
    setSelectedSources([source]);
    setRuns((current) => [...current, created]);
    setSelectedRun(created.id);
    await progress(created);
  }
  async function review(disposition: "reviewed" | "rejected") {
    await api(`${base}/revisions/${revision!.id}/reviews`, {
      disposition,
      notes,
    });
    setReviewed(disposition === "reviewed");
    setCandidate(undefined);
    setReviewStatus(
      disposition === "reviewed"
        ? "Review recorded for this revision."
        : "Revision rejected. Edit and save a new revision to continue.",
    );
  }
  const disabled = busy || !config;
  return (
    <>
      <a className="skip" href="#workspace">
        Skip to workspace
      </a>
      <header>
        <a className="brand" href="/" aria-label="SpecBridge home">
          <span className="brand-mark" aria-hidden="true">
            S/B
          </span>{" "}
          SpecBridge
        </a>
        <span className="local">● Local workspace</span>
      </header>
      <main id="workspace">
        <div className="intro">
          <p className="eyebrow">IDEA → REQUIREMENTS → HANDOFF</p>
          <h1>Make the next step clear.</h1>
          <p>
            Shape a feature, inspect the evidence, and hand developers a
            reviewed specification.
          </p>
        </div>
        {error && (
          <div role="alert" className="error">
            {error}
          </div>
        )}
        <div role="status" aria-live="polite">
          {busy ? "Working… Your progress is saved after each stage." : notice}
        </div>
        {!config ? (
          <section className="panel session">
            <p className="step">01 / LOCAL SESSION</p>
            <h2>Connect your workspace</h2>
            <p>
              The API session token stays in this tab’s memory. Enter it again
              after refreshing.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void act(async () => {
                  const value = await api<Schema["ProviderInfo"]>("/config");
                  const list = await api<Schema["Project"][]>("/projects");
                  setConfig(value);
                  setProjects(list);
                });
              }}
            >
              <label>
                Session token
                <input
                  type="password"
                  autoComplete="off"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                />
              </label>
              <button disabled={busy || !token}>Connect</button>
            </form>
          </section>
        ) : (
          <>
            {config.provider === "fixture" && (
              <aside className="demo">
                <strong>DEMO · Fixture provider</strong>
                <span>
                  This is deterministic test output, not AI generation or
                  factual validation.
                </span>
              </aside>
            )}
            <div className="workspace-grid">
              <aside className="intake panel">
                <p className="step">01 / START WITH CONTEXT</p>
                <h2>Feature workspace</h2>
                <fieldset disabled={disabled}>
                  <legend>Project</legend>
                  <label>
                    Existing project
                    <select
                      value={project}
                      onChange={(e) =>
                        void act(() => chooseProject(e.target.value))
                      }
                    >
                      <option value="">Choose a project</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      void act(async () => {
                        const created = await api<Schema["Project"]>(
                          "/projects",
                          { name },
                        );
                        setProjects([...projects, created]);
                        setName("");
                        await chooseProject(created.id);
                      });
                    }}
                  >
                    <label>
                      Project name
                      <input
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        maxLength={200}
                        required
                      />
                    </label>
                    <button className="secondary" disabled={!name.trim()}>
                      Create project
                    </button>
                  </form>
                </fieldset>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void act(generate);
                  }}
                >
                  <fieldset disabled={disabled || !project}>
                    <legend>New feature</legend>
                    <label>
                      Feature idea
                      <textarea
                        value={idea}
                        onChange={(e) => setIdea(e.target.value)}
                        maxLength={32768}
                        rows={6}
                        required
                        placeholder="What should someone be able to do, and why?"
                      />
                    </label>
                    <div className="destination">
                      <strong>Generation destination</strong>
                      <dl>
                        <dt>Provider</dt>
                        <dd>{config.provider}</dd>
                        <dt>Model</dt>
                        <dd>{config.model}</dd>
                        <dt>Destination</dt>
                        <dd>{config.destination}</dd>
                      </dl>
                    </div>
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={ack}
                        onChange={(e) => setAck(e.target.checked)}
                      />
                      I acknowledge generation uses this destination
                    </label>
                    <button disabled={!ack || !idea.trim()}>
                      Generate draft
                    </button>
                  </fieldset>
                </form>
                {project && (
                  <fieldset disabled={disabled}>
                    <legend>Resume saved work</legend>
                    <label>
                      Existing run
                      <select
                        value={selectedRun}
                        onChange={(e) => setSelectedRun(e.target.value)}
                      >
                        <option value="">Choose a run</option>
                        {runs.map((r) => (
                          <option key={r.id} value={r.id}>
                            {r.id.slice(0, 8)} · {r.stage} · {r.status}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      className="secondary"
                      disabled={!selectedRun}
                      onClick={() =>
                        void act(async () => {
                          clearRevision();
                          setSelectedSources([]);
                          const saved = await api<Schema["Run"]>(
                            `${base}/runs/${selectedRun}`,
                          );
                          setRun(saved);
                          setSelectedSources(
                            await Promise.all(saved.source_ids.map(id =>
                              api<Schema["Source"]>(`${base}/sources/${id}`)
                            )),
                          );
                          if (saved.revision_id)
                            await loadRevision(saved.revision_id);
                        })
                      }
                    >
                      Open run
                    </button>
                  </fieldset>
                )}
              </aside>
              <div className="review-column">
                <section className="panel">
                  <p className="step">02 / INSPECT & REFINE</p>
                  <h2>Draft review</h2>
                  {!run ? (
                    <div className="empty">
                      <span aria-hidden="true">↗</span>
                      <h3>A clear handoff starts with an idea.</h3>
                      <p>
                        Select a project and generate your first draft. You’ll
                        review every section before approving a package.
                      </p>
                    </div>
                  ) : (
                    <>
                      <p>
                        Current stage: <strong>{run.stage}</strong> ·{" "}
                        {run.status} · Attempts: {run.attempts}
                      </p>
                      <ol aria-label="Stage history" className="history">
                        {(run.history ?? []).map((stage, i) => (
                          <li key={`${stage}-${i}`}>{stage}</li>
                        ))}
                      </ol>
                      <details className="source-evidence">
                        <summary>Selected source evidence</summary>
                        {selectedSources.map(source => (
                          <section key={source.id}>
                            <p>Source ID: <code>{source.id}</code> · {source.kind}</p>
                            <pre>{source.text}</pre>
                          </section>
                        ))}
                        {selectedSources.length === 0 && (
                          <p>Source evidence has not loaded.</p>
                        )}
                      </details>
                      {run.error && (
                        <p className="error" role="alert">
                          Stage error: {run.error}
                        </p>
                      )}
                      {!["review", "published"].includes(run.status) && (
                        <div>
                          <label className="check">
                            <input
                              type="checkbox"
                              checked={retry}
                              onChange={(e) => setRetry(e.target.checked)}
                              disabled={disabled}
                            />
                            I acknowledge this retry may repeat a billable
                            provider call
                          </label>
                          <button
                            disabled={disabled || !retry}
                            onClick={() => void act(() => progress(run, true))}
                          >
                            Retry stage
                          </button>
                        </div>
                      )}
                    </>
                  )}
                  {revision && artifact && (
                    <>
                      <div className="revision-line">
                        <strong>Revision {revision.number}</strong>
                        <code>{revision.digest}</code>
                      </div>
                      <p className="muted">
                        Generated claims require human judgment. Source
                        references do not verify facts.
                      </p>
                      <section>
                        <h3>Findings</h3>
                        {revision.findings?.length ? (
                          <ul>
                            {revision.findings.map((f, i) => (
                              <li key={i}>
                                {f.severity}: {f.message} ({f.code})
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p>
                            No structural findings recorded. This is not factual
                            validation.
                          </p>
                        )}
                      </section>
                      <ArtifactEditor
                        value={artifact}
                        disabled={disabled}
                        onChange={(value) => {
                          setArtifact(value);
                          setDirty(true);
                          setCandidate(undefined);
                          setReviewed(false);
                          setReviewStatus("");
                        }}
                      />
                      <button
                        disabled={disabled || !dirty}
                        onClick={() =>
                          void act(async () => {
                            const saved = await api<Schema["Revision"]>(
                              `${base}/revisions/${revision.id}/edits`,
                              { expected_digest: revision.digest, artifact },
                            );
                            clearRevision();
                            setRevision(saved);
                            setArtifact(saved.artifact);
                            setNotice(
                              "New revision saved. Review and approve it again.",
                            );
                          })
                        }
                      >
                        Save revision
                      </button>
                      <details>
                        <summary>Revision provenance</summary>
                        <dl>
                          {Object.entries(revision.provenance ?? {}).map(
                            ([key, value]) => (
                              <div key={key}>
                                <dt>{key}</dt>
                                <dd>{value}</dd>
                              </div>
                            ),
                          )}
                        </dl>
                      </details>
                    </>
                  )}
                </section>
                <section className="panel">
                  <p className="step">03 / REVIEW & PACKAGE</p>
                  <h2>A deliberate handoff</h2>
                  <p>
                    Record your review, inspect the exact package, then approve
                    its digest.
                  </p>
                  <label>
                    Review notes
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      maxLength={16384}
                      disabled={disabled || !revision || dirty}
                      rows={3}
                      placeholder="Record conflicts, decisions, or remaining uncertainty."
                    />
                  </label>
                  <div className="actions">
                    <button
                      disabled={disabled || !revision || dirty}
                      onClick={() => void act(() => review("reviewed"))}
                    >
                      Record review
                    </button>
                    <button
                      className="secondary"
                      disabled={disabled || !revision || dirty}
                      onClick={() => void act(() => review("rejected"))}
                    >
                      Reject revision
                    </button>
                  </div>
                  <p role="status">{reviewStatus}</p>
                  <button
                    className="secondary"
                    disabled={disabled || !revision || !reviewed || dirty}
                    onClick={() =>
                      void act(async () =>
                        setCandidate(
                          await api<Schema["Candidate"]>(
                            `${base}/revisions/${revision!.id}/candidates`,
                            undefined,
                            false,
                            "POST",
                          ),
                        ),
                      )
                    }
                  >
                    Prepare package
                  </button>
                  {candidate && (
                    <div className="manifest">
                      <h3>Exact package preview</h3>
                      <p>
                        Package digest: <code>{candidate.digest}</code>
                      </p>
                      <p>
                        Template digest:{" "}
                        <code>{candidate.template_digest}</code>
                      </p>
                      <ul aria-label="File manifest">
                        {Object.entries(candidate.manifest).map(
                          ([path, hash]) => (
                            <li key={path}>
                              <strong>{path}</strong>
                              <code>{hash}</code>
                            </li>
                          ),
                        )}
                      </ul>
                    </div>
                  )}
                  <div className="actions export-actions">
                    <button
                      disabled={
                        disabled ||
                        !candidate ||
                        !reviewed ||
                        candidate.approved ||
                        dirty
                      }
                      onClick={() =>
                        void act(async () => {
                          const approved = await api<Schema["Candidate"]>(
                            `${base}/candidates/${candidate!.id}/approve`,
                            { digest: candidate!.digest },
                          );
                          setCandidate(approved);
                          setNotice("This exact package is approved.");
                        })
                      }
                    >
                      Approve this package
                    </button>
                    <button
                      className="secondary"
                      disabled={disabled || !candidate?.approved || dirty}
                      onClick={() =>
                        void act(async () => {
                          try {
                            const blob = await api<Blob>(
                              `${base}/candidates/${candidate!.id}/download`,
                              undefined,
                              true,
                            );
                            const url = URL.createObjectURL(blob);
                            const link = document.createElement("a");
                            link.href = url;
                            link.download = "specbridge-handoff.zip";
                            link.click();
                            setTimeout(() => URL.revokeObjectURL(url), 1000);
                            setNotice("Approved package downloaded.");
                          } catch (e) {
                            if (e instanceof ApiError && e.status === 409) {
                              setCandidate(undefined);
                              setReviewed(false);
                              setReviewStatus(
                                "Package changed or became stale. Reopen the run, review, and prepare it again.",
                              );
                            }
                            throw e;
                          }
                        })
                      }
                    >
                      Download package
                    </button>
                  </div>
                </section>
              </div>
            </div>
          </>
        )}
      </main>
      <footer>
        SpecBridge{" "}
        <span>
          Local decisions. Traceable requirements. Independent documentation.
        </span>
      </footer>
    </>
  );
}
