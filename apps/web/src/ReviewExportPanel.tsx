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

  return (
    <section className="panel" aria-labelledby="package-heading">
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
      <p>
        Record your review, inspect the exact package, then approve its digest.
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
      <button
        className="secondary"
        disabled={disabled || !revision || !reviewed || dirty}
        onClick={() => void onPreparePackage()}
      >
        Prepare package
      </button>
      {candidate && (
        <PackagePreview
          token={token}
          project={project}
          candidate={candidate}
        />
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
          onClick={() => void onApprovePackage()}
        >
          Approve this package
        </button>
        <button
          className="secondary"
          disabled={disabled || !candidate?.approved || dirty}
          onClick={() => void onDownloadPackage()}
        >
          Download package
        </button>
      </div>
      <GitCollaboration
        token={token}
        project={project}
        candidate={candidate}
        disabled={disabled}
        onAuthError={onAuthError}
      />
    </section>
  );
}
