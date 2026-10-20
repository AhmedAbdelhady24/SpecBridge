import { useRef, useState, type FormEvent } from "react";
import type { components } from "./api/schema";
import { ArtifactEditor } from "./ArtifactEditor";
import { ArtifactPreview } from "./ArtifactPreview";
type Artifact = components["schemas"]["Artifact"];
type Revision = components["schemas"]["Revision"];
type RequestView = components["schemas"]["RequestView"];

export function ArtifactWorkspace({
  revision,
  value,
  disabled,
  dirty,
  onChange,
  onSave,
  onDiscard,
  original,
  requests,
  onRequestChange,
}: {
  revision: Revision;
  value: Artifact;
  disabled: boolean;
  dirty: boolean;
  onChange: (value: Artifact) => void;
  onSave: () => void;
  onDiscard?: () => void;
  original?: Artifact;
  requests?: RequestView[];
  onRequestChange?: (targetId: string, text: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [section, setSection] = useState<string>();
  const [undo, setUndo] = useState<{
    value: Artifact;
    revisionId: string;
  }>();
  const form = useRef<HTMLFormElement>(null);
  function change(next: Artifact, removal = false) {
    setUndo(removal ? { value, revisionId: revision.id } : undefined);
    onChange(next);
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    onSave();
  }
  return (<>
    <div className="draft-mode actions" aria-label="Draft display mode">
      <button type="button" className={editing ? "secondary" : ""} aria-pressed={!editing} disabled={disabled} onClick={() => setEditing(false)}>
        Read draft
      </button>
      <button type="button" className={editing ? "" : "secondary"} aria-pressed={editing} disabled={disabled} onClick={() => { setSection(undefined); setEditing(true); }}>
        Edit draft
      </button>
    </div>
    {dirty && (<p className="unsaved-notice" role="status">
      Unsaved edits to revision {revision.number}. Save or discard your
      edits before recording a review or preparing a package.
    </p>)}
    <form id="artifact-edit-form" ref={form} onSubmit={submit}>
      {editing && !section ? (
        <ArtifactEditor value={value} disabled={disabled} onChange={change} section={section} />
      ) : (
        <ArtifactPreview
          value={value}
          original={original}
          requests={requests}
          onRequestChange={onRequestChange}
          onEditSection={disabled ? undefined : next => { setSection(next); setEditing(true); }}
          renderSectionEditor={editing ? key => key === section ? <ArtifactEditor value={value} disabled={disabled} onChange={change} section={section} /> : null : undefined}
        />
      )}
    </form>
    {(editing || dirty) && (<div className="edit-action-bar" role="region" aria-label="Revision actions">
      <span>
        {dirty ? "Unsaved changes" : `Editing revision ${revision.number}`}
      </span>
      <div className="actions">
        <button type="button" disabled={disabled || !dirty} onClick={() => {
          // Reveal the first invalid control before native validation tries to focus it.
          const invalid = form.current?.querySelector('input:invalid, textarea:invalid, select:invalid');
          let section = invalid?.closest('details');
          while (section) {
            section.open = true;
            section = section.parentElement?.closest('details');
          }
          if (form.current?.reportValidity())
            onSave();
        }}>
          Save revision
        </button>
        <button type="button" className="secondary" disabled={disabled || !dirty} onClick={() => {
          if (onDiscard)
            onDiscard();
          else
            onChange(revision.artifact);
          setUndo(undefined);
        }}>
          Discard changes
        </button>
        {undo?.revisionId === revision.id && (<button type="button" className="secondary" disabled={disabled} onClick={() => {
          onChange(undo.value);
          setUndo(undefined);
        }}>
          Undo removal
        </button>)}
      </div>
    </div>)}
  </>);
}
