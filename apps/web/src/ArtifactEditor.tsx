import { useId, useRef } from "react";
import type { components } from "./api/schema";
type Artifact = components["schemas"]["Artifact"];
type EvidenceKind = components["schemas"]["Statement"]["kind"];
const evidenceKinds = [
  "user_provided",
  "recommendation",
  "assumption",
  "unknown",
] as const;
const sections = [
  "scope",
  "non_goals",
  "edge_cases",
  "dependencies",
  "risks",
  "success_metrics",
] as const;
const names = {
  scope: "Scope",
  non_goals: "Non-goal",
  edge_cases: "Edge case",
  dependencies: "Dependency",
  risks: "Risk",
  success_metrics: "Success metric",
};
export function ArtifactEditor({
  value,
  onChange,
  disabled,
}: {
  value: Artifact;
  onChange: (value: Artifact, removal?: boolean) => void;
  disabled: boolean;
}) {
  const editorId = useId();
  const root = useRef<HTMLDivElement>(null);
  const field = (
    label: string,
    text: string,
    change: (text: string) => void,
  ) => (
    <div key={label}>
      <label htmlFor={`${editorId}-${label.replaceAll(" ", "-")}`}>{label}</label>
      <textarea
        id={`${editorId}-${label.replaceAll(" ", "-")}`}
        value={text}
        maxLength={label === "Title" ? 200 : 16384}
        required
        disabled={disabled}
        onChange={(e) => change(e.target.value)}
        rows={label === "Title" ? 1 : 3}
      />
    </div>
  );
  const evidence = (
    label: string,
    kind: EvidenceKind,
    change: (kind: EvidenceKind) => void,
    requirement = false,
  ) => {
    const options = evidenceKinds.filter(
      (kind) => !requirement || kind !== "unknown",
    );
    const selectable = options.some((option) => option === kind);
    const id = `${editorId}-evidence-${label.replaceAll(" ", "-")}`;
    return (
      <div>
        <label htmlFor={id}>Evidence type for {label}</label>
        <select
          id={id}
          value={selectable ? kind : ""}
          required
          disabled={disabled}
          onChange={(e) => change(e.target.value as EvidenceKind)}
        >
          {!selectable && (
            <option value="" disabled>Choose evidence type</option>
          )}
          {options.map((option) => (
            <option key={option} value={option}>
              {option.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </div>
    );
  };
  return (
    <div className="artifact" ref={root}>
      <nav className="actions" aria-label="Edit sections">
        <button type="button" className="secondary" onClick={() => root.current?.querySelectorAll('details.editor-section').forEach(item => { (item as HTMLDetailsElement).open = true; })}>Expand all sections</button>
        <button type="button" className="secondary" onClick={() => root.current?.querySelectorAll('details.editor-section').forEach(item => { (item as HTMLDetailsElement).open = false; })}>Collapse all sections</button>
      </nav>
      {field("Title", value.title, (title) => onChange({ ...value, title }))}
      {field("Purpose", value.purpose, (purpose) =>
        onChange({ ...value, purpose }),
      )}
      {sections.map((section) => (
        <details key={section} className="editor-section">
          <summary>{section.replaceAll("_", " ")} ({value[section].length})</summary>
          {value[section].length === 0 && (
            <p className="muted">None supplied.</p>
          )}
          {value[section].map((item, i) => (
            <div key={i}>
              {field(`${names[section]} ${i + 1}`, item.text, (text) =>
                onChange({
                  ...value,
                  [section]: value[section].map((s, j) =>
                    j === i ? { ...s, text } : s,
                  ),
                }),
              )}
              {evidence(`${names[section]} ${i + 1}`, item.kind, (kind) =>
                onChange({
                  ...value,
                  [section]: value[section].map((s, j) =>
                    j === i ? { ...s, kind } : s,
                  ),
                }),
              )}
              <p className="provenance">
                {item.kind} · Source IDs:{" "}
                {(item.source_ids ?? []).join(", ") || "none"}
              </p>
            </div>
          ))}
        </details>
      ))}
      <details className="editor-section">
        <summary>Requirements ({value.requirements.length})</summary>
        {value.requirements.map((item, i) => (
          <div key={item.id}>
            <p>
              Requirement ID: <code>{item.id}</code>
            </p>
            {field(`Requirement ${i + 1}`, item.text, (text) =>
              onChange({
                ...value,
                requirements: value.requirements.map((s, j) =>
                  j === i ? { ...s, text } : s,
                ),
              }),
            )}
            {evidence(`Requirement ${i + 1}`, item.kind, (kind) =>
              onChange({
                ...value,
                requirements: value.requirements.map((s, j) =>
                  j === i ? { ...s, kind } : s,
                ),
              }),
              true,
            )}
            <p className="provenance">
              {item.kind} · Source IDs:{" "}
              {(item.source_ids ?? []).join(", ") || "none"}
            </p>
          </div>
        ))}
      </details>
      <details className="editor-section">
        <summary>User stories &amp; acceptance criteria ({value.stories.length})</summary>
        {value.stories.map((item, i) => (
          <div key={item.id}>
            <p>
              Story ID: <code>{item.id}</code>
            </p>
            {field(`Story ${i + 1}`, item.text, (text) =>
              onChange({
                ...value,
                stories: value.stories.map((s, j) =>
                  j === i ? { ...s, text } : s,
                ),
              }),
            )}
            {evidence(`Story ${i + 1}`, item.kind, (kind) =>
              onChange({
                ...value,
                stories: value.stories.map((s, j) =>
                  j === i ? { ...s, kind } : s,
                ),
              }),
            )}
            <p className="provenance">
              {item.kind} · Requirements: {item.requirement_ids.join(", ")} ·
              Source IDs: {(item.source_ids ?? []).join(", ") || "none"}
            </p>
            {item.acceptance_criteria.map((criterion, k) => (
              <div key={k}>
                {field(
                  `Acceptance criterion ${i + 1}.${k + 1}`,
                  criterion,
                  (text) =>
                    onChange({
                      ...value,
                      stories: value.stories.map((s, j) =>
                        j === i
                          ? {
                              ...s,
                              acceptance_criteria: s.acceptance_criteria.map(
                                (c, n) => (n === k ? text : c),
                              ),
                            }
                          : s,
                      ),
                    }),
                )}
                <button
                  type="button"
                  disabled={disabled || item.acceptance_criteria.length <= 1}
                  onClick={() => onChange({
                    ...value,
                    stories: value.stories.map((s, j) =>
                      j === i ? {
                        ...s,
                        acceptance_criteria: s.acceptance_criteria.filter(
                          (_, n) => n !== k,
                        ),
                      } : s,
                    ),
                  }, true)}
                >
                  Remove acceptance criterion {i + 1}.{k + 1}
                </button>
              </div>
            ))}
            <button
              type="button"
              disabled={disabled || item.acceptance_criteria.length >= 30}
              onClick={() => onChange({
                ...value,
                stories: value.stories.map((s, j) =>
                  j === i ? {
                    ...s,
                    acceptance_criteria: [...s.acceptance_criteria, ""],
                  } : s,
                ),
              })}
            >
              Add acceptance criterion to story {i + 1}
            </button>
          </div>
        ))}
      </details>
      <details className="editor-section">
        <summary>Open questions ({value.open_questions.length})</summary>
        {value.open_questions.length === 0 && (
          <p className="muted">None supplied.</p>
        )}
        {value.open_questions.map((q, i) => (
          <div key={i}>
            {field(`Open question ${i + 1}`, q, (text) =>
              onChange({
                ...value,
                open_questions: value.open_questions.map((s, j) =>
                  j === i ? text : s,
                ),
              }),
            )}
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChange({
                ...value,
                open_questions: value.open_questions.filter((_, j) => j !== i),
              }, true)}
            >
              Remove open question {i + 1}
            </button>
          </div>
        ))}
        <button
          type="button"
          disabled={disabled || value.open_questions.length >= 100}
          onClick={() => onChange({
            ...value,
            open_questions: [...value.open_questions, ""],
          })}
        >
          Add open question
        </button>
      </details>
    </div>
  );
}
