import { SourceReferences, revealReference } from "./SourceReferences";
import { evidenceLabel } from "./labels";
import { useState, type ReactNode } from "react";
import type { components } from "./api/schema";

type Artifact = components["schemas"]["Artifact"];
type Statement = components["schemas"]["Statement"];
type RequestView = components["schemas"]["RequestView"];

function Evidence({ item }: {
  item: Statement;
}) {
  return (<>
    <span className="evidence-badge">{evidenceLabel(item.kind)}</span>
    <SourceReferences ids={item.source_ids ?? []} claim={item.text} />
  </>);
}

function ClauseAnnotations({ requests }: { requests: RequestView[] }) {
  if (!requests.length) return null;
  return (
    <div className="clause-annotations">
      {requests.map((r) => (
        <div key={r.id} className="clause-annotation-card">
          <div className="annotation-header">
            <span className="annotation-tag">💬 Change requested</span>
            <span className={`status-pill status-${r.status}`}>{r.status}</span>
          </div>
          <p className="annotation-text">{r.text}</p>
        </div>
      ))}
    </div>
  );
}

function InlineAnnotationComposer({
  targetLabel,
  onSubmit,
  onCancel,
}: {
  targetLabel: string;
  onSubmit: (text: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  return (
    <div className="inline-annotation-composer">
      <label>
        Request change on: <strong>{targetLabel}</strong>
        <textarea
          rows={2}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe what needs to be changed or clarified..."
          disabled={submitting}
          autoFocus
        />
      </label>
      <div className="actions">
        <button
          type="button"
          disabled={!text.trim() || submitting}
          onClick={async () => {
            setSubmitting(true);
            try {
              await onSubmit(text.trim());
              setText("");
              onCancel();
            } finally {
              setSubmitting(false);
            }
          }}
        >
          {submitting ? "Logging…" : "Log change request"}
        </button>
        <button type="button" className="secondary" disabled={submitting} onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  );
}

export function ArtifactPreview({
  value,
  onEditSection,
  renderSectionEditor,
  original,
  requests = [],
  onRequestChange,
}: {
  value: Artifact;
  onEditSection?: (section: string) => void;
  renderSectionEditor?: (section: string) => ReactNode;
  original?: Artifact;
  requests?: RequestView[];
  onRequestChange?: (targetId: string, text: string) => Promise<void>;
}) {
  const [activeTarget, setActiveTarget] = useState<string | null>(null);

  const sections = [
    ["scope", "Scope"],
    ["non_goals", "Non-goals"],
    ["edge_cases", "Edge cases"],
    ["dependencies", "Dependencies"],
    ["risks", "Risks"],
    ["success_metrics", "Proposed success metrics"],
  ] as const;

  return (<article className="artifact-preview" aria-label="Readable draft">
    {renderSectionEditor?.("overview") ?? <><h3>{value.title}</h3>
      <p>{value.purpose}</p>
      {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection("overview")}>Edit overview</button>}
    </>}
    <p className="review-caveat">Human review required</p>
    <nav aria-label="Document sections" className="document-outline">
      <a href="#preview-scope">Scope</a>
      <a href="#preview-requirements">Requirements</a>
      <a href="#preview-stories">Stories and criteria</a>
      <a href="#preview-questions">Open questions</a>
    </nav>
    {sections.map(([key, title]) => {
      const sectionRequests = requests.filter((r) => r.target_ids?.includes(key));
      return (
        <details className="document-section" key={key} id={`preview-${key}`} open={key === "scope"}>
          <summary>
            {title} ({value[key].length})
          </summary>
          {renderSectionEditor?.(key) ?? <>
            <div className="section-actions-bar">
              {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection(key)}>Edit {title.toLowerCase()}</button>}
              {onRequestChange && (
                <button
                  type="button"
                  className="text-link annotate-trigger"
                  onClick={() => setActiveTarget(activeTarget === key ? null : key)}
                >
                  💬 Request change on {title.toLowerCase()}
                </button>
              )}
            </div>
            {activeTarget === key && onRequestChange && (
              <InlineAnnotationComposer
                targetLabel={title}
                onSubmit={(text) => onRequestChange(key, text)}
                onCancel={() => setActiveTarget(null)}
              />
            )}
            <ClauseAnnotations requests={sectionRequests} />
            {!value[key].length && <p>None supplied.</p>}
            {value[key].map((item, i) => (<div className="statement" key={i}>
              <p>{item.text}</p>
              <Evidence item={item} />
            </div>))}
          </>}
        </details>
      );
    })}
    <details className="document-section" id="preview-requirements" open>
      <summary>Requirements ({value.requirements.length})</summary>
      {renderSectionEditor?.("requirements") ?? <>
        {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection("requirements")}>Edit requirements</button>}
        {value.requirements.map((item, reqIndex) => {
          const reqRequests = requests.filter((r) => r.target_ids?.includes(item.id));
          return (
            <section
              className={original && JSON.stringify(original.requirements.find(r => r.id === item.id)) !== JSON.stringify(item) ? "statement amendment-highlight" : "statement"}
              key={item.id}
              id={`read-${item.id}`}
              tabIndex={-1}
            >
              {original && original.requirements.find(r => r.id === item.id)?.text !== item.text && <p className="diff-before"><strong>Before: </strong>
                <del>{original.requirements.find(r => r.id === item.id)?.text || "New requirement"}</del></p>}
              <h4>Requirement {reqIndex + 1}: {item.text}</h4>
              <details className="technical-reference"><summary>Technical reference</summary><code>{item.id}</code></details>
              <div className="evidence-line">
                <Evidence item={item} />
              </div>
              <p>
                Stories:{" "}
                {value.stories
                  .filter((story) => story.requirement_ids.includes(item.id))
                  .map((story) => (<a key={story.id} href={`#read-${story.id}`} onClick={() => revealReference(story.id)}>
                    Story {value.stories.indexOf(story) + 1}: {story.text}
                    {" "}
                  </a>))}
              </p>
              <ClauseAnnotations requests={reqRequests} />
              {onRequestChange && (
                <div className="clause-annotate-action">
                  <button
                    type="button"
                    className="text-link annotate-trigger"
                    onClick={() => setActiveTarget(activeTarget === item.id ? null : item.id)}
                  >
                    💬 Request change on Requirement {reqIndex + 1}
                  </button>
                  {activeTarget === item.id && (
                    <InlineAnnotationComposer
                      targetLabel={`Requirement ${reqIndex + 1}: ${item.text.slice(0, 60)}…`}
                      onSubmit={(text) => onRequestChange(item.id, text)}
                      onCancel={() => setActiveTarget(null)}
                    />
                  )}
                </div>
              )}
            </section>
          );
        })}
      </>}
    </details>
    <details className="document-section" id="preview-stories" open>
      <summary>
        User stories and acceptance criteria ({value.stories.length})
      </summary>
      {renderSectionEditor?.("stories") ?? <>
        {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection("stories")}>Edit stories and criteria</button>}
        {value.stories.map((story, storyIndex) => {
          const storyRequests = requests.filter((r) => r.target_ids?.includes(story.id));
          return (
            <section
              className={original && JSON.stringify(original.stories.find(s => s.id === story.id)) !== JSON.stringify(story) ? "statement amendment-highlight" : "statement"}
              key={story.id}
              id={`read-${story.id}`}
              tabIndex={-1}
            >
              <h4>Story {storyIndex + 1}: {story.text}</h4>
              <details className="technical-reference"><summary>Technical reference</summary><code>{story.id}</code></details>
              <div className="evidence-line">
                <Evidence item={story} />
              </div>
              <p>
                Requirements:{" "}
                {story.requirement_ids.map((id) => (<a key={id} href={`#read-${id}`} onClick={() => revealReference(id)}>
                  Requirement {value.requirements.findIndex(r => r.id === id) + 1}: {value.requirements.find(r => r.id === id)?.text || "Unavailable requirement"}
                  {" "}
                </a>))}
              </p>
              <ul>
                {story.acceptance_criteria.map((criterion, i) => (<li key={i}>{criterion}</li>))}
              </ul>
              <ClauseAnnotations requests={storyRequests} />
              {onRequestChange && (
                <div className="clause-annotate-action">
                  <button
                    type="button"
                    className="text-link annotate-trigger"
                    onClick={() => setActiveTarget(activeTarget === story.id ? null : story.id)}
                  >
                    💬 Request change on Story {storyIndex + 1}
                  </button>
                  {activeTarget === story.id && (
                    <InlineAnnotationComposer
                      targetLabel={`Story ${storyIndex + 1}: ${story.text.slice(0, 60)}…`}
                      onSubmit={(text) => onRequestChange(story.id, text)}
                      onCancel={() => setActiveTarget(null)}
                    />
                  )}
                </div>
              )}
            </section>
          );
        })}
      </>}
    </details>
    <details className="document-section" id="preview-questions" open>
      <summary>Open questions ({value.open_questions.length})</summary>
      {renderSectionEditor?.("open_questions") ?? <>
        {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection("open_questions")}>Edit question list</button>}
        {value.open_questions.length ? (<ul>
          {value.open_questions.map((question, i) => (<li key={i} id={`read-question-${i}`} tabIndex={-1}>{question}</li>))}
        </ul>) : (<p>None supplied.</p>)}
      </>}
    </details>
  </article>);
}
