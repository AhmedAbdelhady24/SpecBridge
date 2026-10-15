import { useId } from "react";
import type { components } from "./api/schema";
type Artifact = components["schemas"]["Artifact"];
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
  onChange: (value: Artifact) => void;
  disabled: boolean;
}) {
  const editorId = useId();
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
  return (
    <div className="artifact">
      {field("Title", value.title, (title) => onChange({ ...value, title }))}
      {field("Purpose", value.purpose, (purpose) =>
        onChange({ ...value, purpose }),
      )}
      {sections.map((section) => (
        <section key={section}>
          <h3>{section.replaceAll("_", " ")}</h3>
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
              <p className="provenance">
                {item.kind} · Source IDs:{" "}
                {(item.source_ids ?? []).join(", ") || "none"}
              </p>
            </div>
          ))}
        </section>
      ))}
      <section>
        <h3>Requirements</h3>
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
            <p className="provenance">
              {item.kind} · Source IDs:{" "}
              {(item.source_ids ?? []).join(", ") || "none"}
            </p>
          </div>
        ))}
      </section>
      <section>
        <h3>User stories & acceptance criteria</h3>
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
            <p className="provenance">
              {item.kind} · Requirements: {item.requirement_ids.join(", ")} ·
              Source IDs: {(item.source_ids ?? []).join(", ") || "none"}
            </p>
            {item.acceptance_criteria.map((criterion, k) =>
              field(
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
              ),
            )}
          </div>
        ))}
      </section>
      <section>
        <h3>Open questions</h3>
        {value.open_questions.length === 0 && (
          <p className="muted">None supplied.</p>
        )}
        {value.open_questions.map((q, i) =>
          field(`Open question ${i + 1}`, q, (text) =>
            onChange({
              ...value,
              open_questions: value.open_questions.map((s, j) =>
                j === i ? text : s,
              ),
            }),
          ),
        )}
      </section>
    </div>
  );
}
