import { useEffect, useState } from 'react';
import type { components } from './api/schema';
import { ApiError, request } from './api/client';
import { CustomSelect } from './CustomSelect';

type S = components['schemas'];

export function GitCollaboration({
  token,
  project,
  candidate,
  disabled,
  onAuthError,
}: {
  token: string;
  project: string;
  candidate?: S['Candidate'];
  disabled: boolean;
  onAuthError: () => void;
}) {
  const [targetType, setTargetType] = useState<'local' | 'github_mock'>('local');
  const [repoPath, setRepoPath] = useState('');
  const [remoteUrl, setRemoteUrl] = useState('');
  const [baseBranch, setBaseBranch] = useState('main');
  const [docsPath, setDocsPath] = useState('docs');
  const [savedTarget, setSavedTarget] = useState<S['GitTarget'] | null>(null);

  const [preview, setPreview] = useState<S['GitPublishPreview'] | null>(null);
  const [receipt, setReceipt] = useState<S['GitPublishReceipt'] | null>(null);
  const [audits, setAudits] = useState<Record<string, unknown>[]>([]);

  const [commitMessage, setCommitMessage] = useState('');
  const [createPr, setCreatePr] = useState(false);
  const [prTitle, setPrTitle] = useState('');
  const [prBody, setPrBody] = useState('');
  const [confirmedApproval, setConfirmedApproval] = useState(false);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const base = `/projects/${encodeURIComponent(project)}`;

  useEffect(() => {
    let active = true;
    request<S['GitTarget']>(token, `${base}/git/targets`)
      .then((t) => {
        if (!active) return;
        setSavedTarget(t);
        setTargetType(t.target_type as 'local' | 'github_mock');
        setRepoPath(t.repo_path || '');
        setRemoteUrl(t.remote_url || '');
        setBaseBranch(t.base_branch || 'main');
        setDocsPath(t.docs_path || 'docs');
      })
      .catch((e) => {
        if (active && e instanceof ApiError && e.status === 401) onAuthError();
      });

    request<Record<string, unknown>[]>(token, `${base}/git/audits`)
      .then((a) => {
        if (active) setAudits(a);
      })
      .catch(() => {});

    return () => {
      active = false;
    };
  }, [token, base, onAuthError]);

  async function act(operation: () => Promise<void>) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await operation();
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) onAuthError();
      setError(e instanceof Error ? e.message : 'Operation failed');
    } finally {
      setBusy(false);
    }
  }

  async function saveTarget() {
    await act(async () => {
      const saved = await request<S['GitTarget']>(token, `${base}/git/targets`, {
        target_type: targetType,
        repo_path: repoPath.trim() || null,
        remote_url: remoteUrl.trim() || null,
        base_branch: baseBranch.trim() || 'main',
        docs_path: docsPath.trim() || 'docs',
      });
      setSavedTarget(saved);
      setPreview(null);
      setNotice('Git destination target configured.');
    });
  }

  async function generatePreview() {
    if (!candidate || !candidate.approved) {
      setError('An approved package candidate is required before generating a Git preview.');
      return;
    }
    await act(async () => {
      const res = await request<S['GitPublishPreview']>(token, `${base}/git/preview`, {
        candidate_id: candidate.id,
        proposed_branch: undefined,
      });
      setPreview(res);
      setCommitMessage(res.commit_message || '');
      setPrTitle(res.pr_title || '');
      setPrBody(res.pr_body || '');
      setConfirmedApproval(false);
      setReceipt(null);
      setNotice('Three-way comparison generated against base snapshot.');
    });
  }

  async function publishChangeset() {
    if (!preview || !candidate) return;
    if (!confirmedApproval) {
      setError('Explicit confirmation of the changeset digest is required before publishing.');
      return;
    }
    await act(async () => {
      const res = await request<S['GitPublishReceipt']>(token, `${base}/git/publish`, {
        candidate_id: candidate.id,
        approval_digest: preview.changeset_digest,
        proposed_branch: preview.proposed_branch,
        commit_message: commitMessage.trim() || preview.commit_message,
        pr_title: createPr ? (prTitle.trim() || preview.pr_title) : null,
        pr_body: createPr ? (prBody.trim() || preview.pr_body) : null,
      });
      setReceipt(res);
      setNotice('Changeset successfully published to Git target.');
      const updatedAudits = await request<Record<string, unknown>[]>(token, `${base}/git/audits`);
      setAudits(updatedAudits);
    });
  }

  const isLocked = disabled || busy;

  return (
    <section className="git-collaboration panel" aria-labelledby="git-collab-heading">
      <p className="step">GIT COLLABORATION</p>
      <h3 id="git-collab-heading">Git target & three-way sync</h3>
      <p>
        Publish approved documentation directly to a Git repository. Three-way comparison detects
        authored changes, updates managed documentation files, and leaves unmanaged code untouched.
      </p>

      {error && <div role="alert" className="error">{error}</div>}
      {notice && <p role="status" className="notice">{notice}</p>}

      <details open={!savedTarget}>
        <summary>Git destination settings {savedTarget ? '· Configured' : '· Action required'}</summary>
        <div className="target-form">
          <label>
            Destination type
            <CustomSelect
              aria-label="Destination type"
              value={targetType}
              disabled={isLocked}
              onChange={(val) => setTargetType(val as 'local' | 'github_mock')}
              options={[
                { value: "local", label: "Local repository path" },
                { value: "github_mock", label: "GitHub repository (mock adapter)" },
              ]}
            />
          </label>

          {targetType === 'local' ? (
            <label>
              Local repository directory path
              <input
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="/absolute/path/to/repo"
                disabled={isLocked}
                required
              />
            </label>
          ) : (
            <label>
              Remote GitHub URL
              <input
                type="text"
                value={remoteUrl}
                onChange={(e) => setRemoteUrl(e.target.value)}
                placeholder="https://github.com/org/docs-repo.git"
                disabled={isLocked}
                required
              />
            </label>
          )}

          <div className="grid-2">
            <label>
              Base branch
              <input
                type="text"
                value={baseBranch}
                onChange={(e) => setBaseBranch(e.target.value)}
                disabled={isLocked}
              />
            </label>
            <label>
              Docs subfolder
              <input
                type="text"
                value={docsPath}
                onChange={(e) => setDocsPath(e.target.value)}
                disabled={isLocked}
              />
            </label>
          </div>

          <button type="button" className="secondary" disabled={isLocked} onClick={saveTarget}>
            Save Git target
          </button>
        </div>
      </details>

      <div className="actions">
        <button
          type="button"
          disabled={isLocked || !candidate?.approved || !savedTarget}
          onClick={generatePreview}
        >
          Preview Git changeset
        </button>
      </div>

      {!candidate?.approved && (
        <p className="muted">Approve the package candidate above to enable Git changeset preview.</p>
      )}

      {preview && (
        <div className="git-preview-result">
          <h4>Three-way changeset preview</h4>
          <dl className="preview-meta">
            <div>
              <dt>Target branch</dt>
              <dd><code>{preview.proposed_branch}</code></dd>
            </div>
            <div>
              <dt>Changeset digest</dt>
              <dd><code>{preview.changeset_digest}</code></dd>
            </div>
            <div>
              <dt>Merge status</dt>
              <dd>
                {preview.diff.has_conflicts ? (
                  <span className="badge-warning">Conflicts detected</span>
                ) : (
                  <span className="badge-clean">Clean three-way merge</span>
                )}
              </dd>
            </div>
          </dl>

          <div className="changeset-files">
            <h5>File changes ({(preview.diff.changes ?? []).length})</h5>
            <table className="file-changes-table">
              <thead>
                <tr>
                  <th>Path</th>
                  <th>Status</th>
                  <th>Conflict</th>
                </tr>
              </thead>
              <tbody>
                {(preview.diff.changes ?? []).map((change) => (
                  <tr key={change.path}>
                    <td><code>{change.path}</code></td>
                    <td>
                      <span className={`status-badge status-${change.status}`}>
                        {change.status}
                      </span>
                    </td>
                    <td>
                      {change.status === 'conflict' || change.conflict_reason ? (
                        <strong className="conflict-text">Conflict</strong>
                      ) : (
                        'No'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="publish-controls">
            <h5>Publish to repository</h5>
            <label>
              Commit message
              <input
                type="text"
                value={commitMessage}
                onChange={(e) => setCommitMessage(e.target.value)}
                disabled={isLocked || preview.diff.has_conflicts}
              />
            </label>

            <label className="check">
              <input
                type="checkbox"
                checked={createPr}
                onChange={(e) => setCreatePr(e.target.checked)}
                disabled={isLocked || preview.diff.has_conflicts}
              />
              Create pull request
            </label>

            {createPr && (
              <div className="pr-fields">
                <label>
                  PR title
                  <input
                    type="text"
                    value={prTitle}
                    onChange={(e) => setPrTitle(e.target.value)}
                    disabled={isLocked}
                  />
                </label>
                <label>
                  PR description
                  <textarea
                    rows={3}
                    value={prBody}
                    onChange={(e) => setPrBody(e.target.value)}
                    disabled={isLocked}
                  />
                </label>
              </div>
            )}

            <div className="approval-boundary">
              <label className="check">
                <input
                  type="checkbox"
                  checked={confirmedApproval}
                  onChange={(e) => setConfirmedApproval(e.target.checked)}
                  disabled={isLocked || preview.diff.has_conflicts}
                />
                I approve publishing changeset <code>{preview.changeset_digest.slice(0, 16)}…</code>
              </label>
            </div>

            <button
              type="button"
              disabled={isLocked || !confirmedApproval || preview.diff.has_conflicts}
              onClick={publishChangeset}
            >
              Publish to Git
            </button>
          </div>
        </div>
      )}

      {receipt && (
        <aside className="publish-receipt" role="status">
          <h4>Git publish receipt</h4>
          <p>Status: <strong>{receipt.status}</strong></p>
          <p>Commit SHA: <code>{receipt.commit_sha}</code></p>
          <p>Branch: <code>{receipt.branch_name}</code></p>
          {receipt.pr_url && (
            <p>
              Pull request: <a href={receipt.pr_url} target="_blank" rel="noopener noreferrer">{receipt.pr_url}</a>
            </p>
          )}
        </aside>
      )}

      {audits.length > 0 && (
        <details className="git-audits">
          <summary>Git publish audit log ({audits.length})</summary>
          <ul className="audit-list">
            {audits.map((a, i) => (
              <li key={i}>
                <small>{String(a.timestamp || '')}</small> · {String(a.action || 'publish')} ·{' '}
                Commit: <code>{String(a.commit_sha || a.id || '').slice(0, 10)}</code>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
