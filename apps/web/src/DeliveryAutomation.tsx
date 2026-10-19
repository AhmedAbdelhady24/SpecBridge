import { useState } from 'react';
import type { components } from './api/schema';
import { ApiError, request } from './api/client';

type S = components['schemas'];

export function DeliveryAutomation({
  token,
  project,
  artifact,
  disabled,
  onAuthError,
}: {
  token: string;
  project: string;
  artifact?: S['Artifact'];
  disabled: boolean;
  onAuthError: () => void;
}) {
  // 1. Meeting actions extraction state
  const [meetingText, setMeetingText] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('Product Alignment Sync');
  const [extractedResult, setExtractedResult] = useState<S['MeetingActionsResult'] | null>(null);

  // 2. Prioritization state
  const [prioMethod, setPrioMethod] = useState<'rice' | 'weighted_criteria'>('rice');
  const [prioResult, setPrioResult] = useState<S['PrioritizationResult'] | null>(null);

  // 3. Jira Sync state
  const [jiraUrl, setJiraUrl] = useState('https://baskhealth.atlassian.net');
  const [jiraKey, setJiraKey] = useState('BASK');
  const [jiraPreview, setJiraPreview] = useState<S['DeliverySyncPreview'] | null>(null);
  const [jiraReceipt, setJiraReceipt] = useState<S['DeliverySyncReceipt'] | null>(null);
  const [jiraConfirmed, setJiraConfirmed] = useState(false);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const base = `/projects/${encodeURIComponent(project)}`;

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

  // --- Meeting Actions ---
  async function extractActions() {
    if (!meetingText.trim()) {
      setError('Provide meeting notes or transcript text before extracting action items.');
      return;
    }
    await act(async () => {
      // First save transcript as a source so we have a reliable source_id
      const source = await request<S['Source']>(token, `${base}/sources`, {
        text: meetingText.trim(),
      });
      const res = await request<S['MeetingActionsResult']>(token, `${base}/delivery/meetings/extract`, {
        text: meetingText.trim(),
        source_id: source.id,
        meeting_title: meetingTitle.trim() || 'Team Sync',
      });
      setExtractedResult(res);
      const actionCount = (res.actions ?? []).length;
      setNotice(`Extracted ${actionCount} action items from "${res.meeting_title}".`);
    });
  }

  // --- Prioritization ---
  async function runPrioritization() {
    // Gather candidate items from extracted actions or current artifact requirements
    const itemsToRank: Record<string, unknown>[] = [];
    const extractedActions = extractedResult?.actions ?? [];

    if (extractedActions.length) {
      extractedActions.forEach((a, i) => {
        itemsToRank.push({
          id: a.id,
          title: a.description,
          reach: (i + 1) * 100,
          impact: 2.0,
          confidence: 0.8,
          effort: (i + 1) * 2,
        });
      });
    } else if (artifact?.requirements.length) {
      artifact.requirements.forEach((r, i) => {
        itemsToRank.push({
          id: r.id,
          title: r.text.slice(0, 80),
          reach: 500,
          impact: 3.0,
          confidence: 0.9,
          effort: (i % 2 === 0) ? (i + 1) * 2 : null, // alternate missing effort to test unranked items
        });
      });
    } else {
      setError('No items available to prioritize. Extract meeting actions or open a feature draft first.');
      return;
    }

    await act(async () => {
      const res = await request<S['PrioritizationResult']>(token, `${base}/delivery/prioritize`, {
        method: prioMethod,
        items: itemsToRank,
      });
      setPrioResult(res);
      const rankedCount = (res.ranked_items ?? []).length;
      const unrankedCount = (res.unranked_items ?? []).length;
      setNotice(`Calculated priority for ${rankedCount} items (${unrankedCount} unranked due to missing metrics).`);
    });
  }

  // --- Jira Sync ---
  async function previewJira() {
    const items: Record<string, unknown>[] = [];
    const extractedActions = extractedResult?.actions ?? [];
    if (artifact?.requirements.length) {
      artifact.requirements.forEach((r) => {
        items.push({
          summary: r.text.slice(0, 100),
          description: r.text,
          issue_type: 'Story',
        });
      });
    } else if (extractedActions.length) {
      extractedActions.forEach((a) => {
        items.push({
          summary: a.description.slice(0, 100),
          description: `${a.description}\n\nQuote: "${a.source_quote}"`,
          issue_type: 'Task',
        });
      });
    } else {
      setError('No draft requirements or extracted actions available to sync to Jira.');
      return;
    }

    await act(async () => {
      const preview = await request<S['DeliverySyncPreview']>(token, `${base}/delivery/jira/preview`, {
        target: {
          instance_url: jiraUrl.trim(),
          project_key: jiraKey.trim(),
        },
        items,
      });
      setJiraPreview(preview);
      setJiraReceipt(null);
      setJiraConfirmed(false);
      setNotice('Jira sync preview generated.');
    });
  }

  async function syncJira() {
    if (!jiraPreview) return;
    if (!jiraConfirmed) {
      setError('Confirmation of the Jira sync changeset digest is required before execution.');
      return;
    }
    await act(async () => {
      const res = await request<S['DeliverySyncReceipt']>(token, `${base}/delivery/jira/sync`, {
        preview: jiraPreview,
        approval_digest: jiraPreview.changeset_digest,
      });
      setJiraReceipt(res);
      const createdCount = (res.created_issues ?? []).length;
      setNotice(`Successfully synced ${createdCount} issues to Jira.`);
    });
  }

  const isLocked = disabled || busy;
  const actionsList = extractedResult?.actions ?? [];
  const rankedList = prioResult?.ranked_items ?? [];
  const unrankedList = prioResult?.unranked_items ?? [];
  const jiraItemsToCreate = jiraPreview?.items_to_create ?? [];
  const jiraCreatedIssues = jiraReceipt?.created_issues ?? [];

  return (
    <section className="delivery-panel" aria-labelledby="delivery-heading">
      <p className="step">DELIVERY AUTOMATION</p>
      <h3 id="delivery-heading">Backlog intake, prioritization & Jira sync</h3>
      <p>
        Extract verifiable action items from discussions, rank backlog items with deterministic formulas,
        and preview/sync issues to tracking systems with human approval.
      </p>

      {error && <div role="alert" className="error">{error}</div>}
      {notice && <p role="status" className="notice">{notice}</p>}

      {/* 1. Meeting actions */}
      <details open className="delivery-section">
        <summary>Meeting to action items</summary>
        <div className="section-body">
          <label>
            Meeting title
            <input
              type="text"
              value={meetingTitle}
              onChange={(e) => setMeetingTitle(e.target.value)}
              disabled={isLocked}
            />
          </label>
          <label>
            Meeting transcript or notes
            <textarea
              rows={4}
              value={meetingText}
              onChange={(e) => setMeetingText(e.target.value)}
              placeholder="Paste notes, transcripts, or summaries with action items and owners..."
              disabled={isLocked}
            />
          </label>
          <button type="button" disabled={isLocked || !meetingText.trim()} onClick={extractActions}>
            Extract action items
          </button>

          {extractedResult && (
            <div className="actions-table-wrapper">
              <h4>Extracted items ({actionsList.length})</h4>
              <p className="muted">
                Unassigned items: <strong>{extractedResult.unassigned_count}</strong>.
                Each item preserves verbatim quotation for audit traceability.
              </p>
              <table className="actions-table">
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Source quote</th>
                    <th>Owner</th>
                    <th>Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {actionsList.map((actItem) => (
                    <tr key={actItem.id}>
                      <td>{actItem.description}</td>
                      <td><em>"{actItem.source_quote}"</em></td>
                      <td>{actItem.owner ? <strong>{actItem.owner}</strong> : <span className="muted">None</span>}</td>
                      <td>{actItem.deadline || <span className="muted">None</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </details>

      {/* 2. Prioritization */}
      <details open className="delivery-section">
        <summary>Deterministic prioritization</summary>
        <div className="section-body">
          <label>
            Method
            <select
              aria-label="Prioritization method"
              value={prioMethod}
              disabled={isLocked}
              onChange={(e) => setPrioMethod(e.target.value as 'rice' | 'weighted_criteria')}
            >
              <option value="rice">RICE (Reach × Impact × Confidence / Effort)</option>
              <option value="weighted_criteria">Weighted criteria</option>
            </select>
          </label>
          <p className="muted">
            Missing metrics are strictly flagged and preserved as unranked without arbitrary defaults.
          </p>
          <button type="button" className="secondary" disabled={isLocked} onClick={runPrioritization}>
            Calculate priority ranking
          </button>

          {prioResult && (
            <div className="priority-results">
              <h4>Ranked items ({rankedList.length})</h4>
              <ol className="ranked-list">
                {rankedList.map((item) => (
                  <li key={item.item_id}>
                    <strong>#{item.rank} {item.title}</strong> — Score: <code>{item.score?.toFixed(1)}</code>
                  </li>
                ))}
              </ol>

              {unrankedList.length > 0 && (
                <div className="unranked-box">
                  <h5>Unranked items (missing metrics)</h5>
                  <p className="muted">These items cannot be deterministically scored until missing values are provided:</p>
                  <ul>
                    {unrankedList.map((item) => (
                      <li key={item.item_id}>
                        {item.title} — <em>Missing: {(item.missing_metrics ?? []).join(', ')}</em>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </details>

      {/* 3. Jira Sync */}
      <details className="delivery-section">
        <summary>Jira integration (Mock adapter)</summary>
        <div className="section-body">
          <div className="grid-2">
            <label>
              Jira URL
              <input
                type="text"
                value={jiraUrl}
                onChange={(e) => setJiraUrl(e.target.value)}
                disabled={isLocked}
              />
            </label>
            <label>
              Project key
              <input
                type="text"
                value={jiraKey}
                onChange={(e) => setJiraKey(e.target.value)}
                disabled={isLocked}
              />
            </label>
          </div>
          <button type="button" className="secondary" disabled={isLocked} onClick={previewJira}>
            Preview Jira sync
          </button>

          {jiraPreview && (
            <div className="jira-preview-box">
              <h4>Jira sync preview</h4>
              <p>Items to create: <strong>{jiraItemsToCreate.length}</strong></p>
              <p>Changeset digest: <code>{jiraPreview.changeset_digest}</code></p>

              <div className="approval-boundary">
                <label className="check">
                  <input
                    type="checkbox"
                    checked={jiraConfirmed}
                    onChange={(e) => setJiraConfirmed(e.target.checked)}
                    disabled={isLocked}
                  />
                  I confirm syncing {jiraItemsToCreate.length} issues to {jiraKey} with digest <code>{jiraPreview.changeset_digest.slice(0, 16)}…</code>
                </label>
              </div>

              <button type="button" disabled={isLocked || !jiraConfirmed} onClick={syncJira}>
                Sync issues to Jira
              </button>
            </div>
          )}

          {jiraReceipt && (
            <aside className="publish-receipt" role="status">
              <h4>Jira sync receipt</h4>
              <p>Status: <strong>{jiraReceipt.status}</strong></p>
              <p>Created issues ({jiraCreatedIssues.length}):</p>
              <ul>
                {jiraCreatedIssues.map((iss, i) => (
                  <li key={i}>
                    <code>{String(iss.key || `ISSUE-${i + 1}`)}</code> — {String(iss.summary || '')}
                  </li>
                ))}
              </ul>
            </aside>
          )}
        </div>
      </details>
    </section>
  );
}
