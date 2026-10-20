import type { components } from "./api/schema";
import { PackagePreview } from "./PackagePreview";
import { GitCollaboration } from "./GitCollaboration";

type Schema = components["schemas"];

export interface ReviewExportPanelProps {
  revision: Schema["Revision"] | undefined;
  candidate: Schema["Candidate"] | undefined;
  dirty: boolean;
  disabled: boolean;
  notes: string;
  setNotes: (value: string) => void;
  reviewStatus: string;
  reviewed: boolean;
  token: string;
  project: string;
  onRecordReview: (disposition: "reviewed" | "rejected") => Promise<void>;
  onPreparePackage: () => Promise<void>;
  onApprovePackage: () => Promise<void>;
  onDownloadPackage: () => Promise<void>;
  onAuthError: () => void;
}

const NOTE_SUGGESTIONS = [
  "Ready for dev",
  "Reviewed & verified",
  "Accepted with known limitations",
  "Changes requested",
];

export function ReviewExportPanel({
  revision,
  candidate,
  dirty,
  disabled,
  notes,
  setNotes,
  reviewStatus,
  reviewed,
  token,
  project,
  onRecordReview,
  onPreparePackage,
  onApprovePackage,
  onDownloadPackage,
  onAuthError,
}: ReviewExportPanelProps) {
  if (!revision) {
    return null;
  }

  const isStep1Done = reviewed;
  const isStep2Done = Boolean(candidate);
  const isStep3Done = Boolean(candidate?.approved);

  const step1State = isStep1Done ? "completed" : "active";
  const step2State = isStep2Done ? "completed" : reviewed ? "active" : "locked";
  const step3State = isStep3Done ? "completed" : candidate ? "active" : "locked";
  const step4State = isStep3Done ? "active ready" : "locked";

  const overallProgressText = !reviewed
    ? "Step 1 of 4: In Progress"
    : !candidate
    ? "Step 2 of 4: In Progress"
    : !candidate.approved
    ? "Step 3 of 4: In Progress"
    : "Step 4 of 4: Ready for Handoff";

  const handleApplySuggestion = (suggestion: string) => {
    if (disabled || !revision || dirty) return;
    if (!notes.trim()) {
      setNotes(suggestion);
    } else if (!notes.includes(suggestion)) {
      setNotes(`${notes.trim()} — ${suggestion}`);
    }
  };

  return (
    <section className="panel review-export-panel" aria-labelledby="package-heading">
      <p className="step">03 / REVIEW & PACKAGE</p>
      <h2 id="package-heading" tabIndex={-1}>
        Review & export
      </h2>

      {dirty && (
        <p className="unsaved-notice">
          Review and package controls are unavailable until you save or discard
          your unsaved draft edits.
        </p>
      )}

      <p className="panel-intro">
        Record your review, inspect the exact handoff package, then approve its digest.
      </p>

      {/* Stepper Progress Bar & Badge */}
      <div className="export-stepper-header" aria-label="Review and export stages">
        <div className="export-stepper-top">
          <span className="export-stepper-title">Guided Handoff Workflow</span>
          <span className="export-overall-badge">{overallProgressText}</span>
        </div>
        <div className="export-stepper-track" role="list">
          <div
            className={`export-track-step ${step1State}`}
            role="listitem"
            title="Step 1: Record Human Review"
          >
            <span className="track-step-circle">{isStep1Done ? "✓" : "1"}</span>
            <span className="track-step-label">1. Review</span>
          </div>
          <div className={`export-track-line ${isStep1Done ? "filled" : ""}`} />
          <div
            className={`export-track-step ${step2State}`}
            role="listitem"
            title="Step 2: Prepare Handoff Package"
          >
            <span className="track-step-circle">{isStep2Done ? "✓" : "2"}</span>
            <span className="track-step-label">2. Package</span>
          </div>
          <div className={`export-track-line ${isStep2Done ? "filled" : ""}`} />
          <div
            className={`export-track-step ${step3State}`}
            role="listitem"
            title="Step 3: Inspect & Approve Package"
          >
            <span className="track-step-circle">{isStep3Done ? "✓" : "3"}</span>
            <span className="track-step-label">3. Approve</span>
          </div>
          <div className={`export-track-line ${isStep3Done ? "filled" : ""}`} />
          <div
            className={`export-track-step ${step4State}`}
            role="listitem"
            title="Step 4: Developer Handoff"
          >
            <span className="track-step-circle">{isStep3Done ? "✓" : "4"}</span>
            <span className="track-step-label">4. Handoff</span>
          </div>
        </div>
      </div>

      <div className="handoff-steps-container">
        {/* Step 1: Record Human Review */}
        <section
          className={`handoff-step-card ${step1State}`}
          aria-labelledby="step-1-heading"
        >
          <div className="step-card-header">
            <div className="step-title-group">
              <span className="step-tag">Step 1</span>
              <h3 id="step-1-heading">Record Human Review</h3>
            </div>
            <span className={`step-badge ${isStep1Done ? "completed" : "in-progress"}`}>
              {isStep1Done ? "Completed" : "In Progress"}
            </span>
          </div>
          <p className="step-card-desc">
            Examine the generated draft alongside your review. Add comments, log
            decisions or concerns, and record your formal disposition.
          </p>

          <label>
            Review notes
            <textarea
              aria-label="Review notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              maxLength={16384}
              disabled={disabled || !revision || dirty}
              rows={3}
              placeholder="Record conflicts, decisions, or remaining uncertainty."
            />
          </label>

          <div
            className="note-chips-group"
            role="group"
            aria-label="Quick note suggestions"
          >
            <span className="note-chips-label">Quick suggestions:</span>
            <div className="note-chips-list">
              {NOTE_SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="chip-btn"
                  disabled={disabled || !revision || dirty}
                  onClick={() => handleApplySuggestion(suggestion)}
                >
                  + {suggestion}
                </button>
              ))}
            </div>
          </div>

          <div className="actions">
            <button
              disabled={disabled || !revision || dirty}
              onClick={() => void onRecordReview("reviewed")}
            >
              Record review
            </button>
            <button
              className="secondary"
              disabled={disabled || !revision || dirty}
              onClick={() => void onRecordReview("rejected")}
            >
              Reject revision
            </button>
          </div>

          <p role="status">{reviewStatus}</p>

          {dirty && (
            <p className="step-hint">
              Save or discard your unsaved draft edits before recording a review.
            </p>
          )}
        </section>

        {/* Step 2: Prepare Handoff Package */}
        <section
          className={`handoff-step-card ${step2State}`}
          aria-labelledby="step-2-heading"
        >
          <div className="step-card-header">
            <div className="step-title-group">
              <span className="step-tag">Step 2</span>
              <h3 id="step-2-heading">Prepare Handoff Package</h3>
            </div>
            <span
              className={`step-badge ${
                isStep2Done ? "completed" : reviewed ? "in-progress" : "locked"
              }`}
            >
              {isStep2Done ? "Completed" : reviewed ? "In Progress" : "Locked"}
            </span>
          </div>
          <p className="step-card-desc">
            Assemble an immutable handoff package from the current
            reviewed specification with verifiable digests.
          </p>

          {!reviewed && (
            <div className="step-waiting-box">
              Step 1 must be completed before building the package.
            </div>
          )}

          {candidate && (
            <div className="step-candidate-summary">
              <span className="step-summary-label">Handoff package digest:</span>{" "}
              <code>{candidate.digest.slice(0, 24)}…</code>
            </div>
          )}

          <div className="actions">
            <button
              className="secondary"
              disabled={disabled || !revision || !reviewed || dirty}
              onClick={() => void onPreparePackage()}
            >
              Prepare package
            </button>
          </div>

          {(!reviewed || dirty) && (
            <p className="step-hint">
              {dirty
                ? "Save or discard unsaved draft edits to prepare the package."
                : "Step 1 must be completed before building the package."}
            </p>
          )}
        </section>

        {/* Step 3: Inspect & Approve Package */}
        <section
          className={`handoff-step-card ${step3State}`}
          aria-labelledby="step-3-heading"
        >
          <div className="step-card-header">
            <div className="step-title-group">
              <span className="step-tag">Step 3</span>
              <h3 id="step-3-heading">Inspect & Approve Package</h3>
            </div>
            <span
              className={`step-badge ${
                isStep3Done ? "completed" : candidate ? "in-progress" : "locked"
              }`}
            >
              {isStep3Done ? "Completed" : candidate ? "In Progress" : "Locked"}
            </span>
          </div>
          <p className="step-card-desc">
            Inspect the exact contents of the documentation files and package
            manifest, then formally approve the handoff package for engineering.
          </p>

          {!candidate ? (
            <div className="step-waiting-box">
              Prepare a handoff package in Step 2 to inspect and approve its contents.
            </div>
          ) : (
            <PackagePreview
              token={token}
              project={project}
              candidate={candidate}
            />
          )}

          <div className="actions">
            <button
              disabled={
                disabled ||
                !candidate ||
                !reviewed ||
                candidate.approved ||
                dirty
              }
              onClick={() => void onApprovePackage()}
            >
              Approve this package
            </button>
          </div>

          {(!candidate || !reviewed || candidate?.approved || dirty) && (
            <p className="step-hint">
              {dirty
                ? "Save or discard unsaved draft edits before approving."
                : !reviewed
                ? "Step 1 must be completed before package approval."
                : !candidate
                ? "Step 2 must be completed before inspecting and approving the handoff package."
                : candidate.approved
                ? "Handoff package is approved and locked for engineering handoff."
                : ""}
            </p>
          )}
        </section>

        {/* Step 4: Developer Handoff */}
        <section
          className={`handoff-step-card ${step4State}`}
          aria-labelledby="step-4-heading"
        >
          <div className="step-card-header">
            <div className="step-title-group">
              <span className="step-tag">Step 4</span>
              <h3 id="step-4-heading">Developer Handoff</h3>
            </div>
            <span className={`step-badge ${isStep3Done ? "ready" : "locked"}`}>
              {isStep3Done ? "Ready" : "Locked"}
            </span>
          </div>
          <p className="step-card-desc">
            Export the final approved static documentation site as a zip archive
            or sync changes directly into your Git target repository.
          </p>

          {!isStep3Done && (
            <div className="step-waiting-box">
              Approve the handoff package in Step 3 before downloading or publishing to Git.
            </div>
          )}

          <div className="actions">
            <button
              className="secondary"
              disabled={disabled || !candidate?.approved || dirty}
              onClick={() => void onDownloadPackage()}
            >
              Download package
            </button>
          </div>

          {(!candidate?.approved || dirty) && (
            <p className="step-hint">
              {dirty
                ? "Save or discard unsaved draft edits before downloading."
                : "Step 3 must be completed before downloading or publishing to Git."}
            </p>
          )}

          <GitCollaboration
            token={token}
            project={project}
            candidate={candidate}
            disabled={disabled}
            onAuthError={onAuthError}
          />
        </section>
      </div>
    </section>
  );
}
