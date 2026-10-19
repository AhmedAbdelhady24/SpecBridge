import { SourceReferences, revealReference } from "./SourceReferences";
import { evidenceLabel } from "./labels";
import type { ReactNode } from "react";
import type { components } from "./api/schema";
type Artifact = components["schemas"]["Artifact"];
type Statement = components["schemas"]["Statement"];
function Evidence({ item }: {
  item: Statement;
}) {
  return (<>
    <span className="evidence-badge">{evidenceLabel(item.kind)}</span>
    <SourceReferences ids={item.source_ids ?? []} claim={item.text} />
  </>);
}
export function ArtifactPreview({ value, onEditSection, renderSectionEditor, original }: {
  value: Artifact;
  onEditSection?: (section: string) => void;
  renderSectionEditor?: (section: string) => ReactNode;
  original?: Artifact;
}) {
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
    {sections.map(([key, title]) => (<details className="document-section" key={key} id={`preview-${key}`} open={key === "scope"}>
      <summary>
        {title} ({value[key].length})
      </summary>
      {renderSectionEditor?.(key) ?? <>
        {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection(key)}>Edit {title.toLowerCase()}</button>}
        {!value[key].length && <p>None supplied.</p>}
        {value[key].map((item, i) => (<div className="statement" key={i}>
          <p>{item.text}</p>
          <Evidence item={item} />
        </div>))}
      </>}
    </details>))}
    <details className="document-section" id="preview-requirements" open>
      <summary>Requirements ({value.requirements.length})</summary>
      {renderSectionEditor?.("requirements") ?? <>
        {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection("requirements")}>Edit requirements</button>}
        {value.requirements.map((item) => (<section className={original && JSON.stringify(original.requirements.find(r => r.id === item.id)) !== JSON.stringify(item) ? "statement amendment-highlight" : "statement"} key={item.id} id={`read-${item.id}`} tabIndex={-1}>
          {original && original.requirements.find(r => r.id === item.id)?.text !== item.text && <p className="diff-before"><strong>Before: </strong>
            <del>{original.requirements.find(r => r.id === item.id)?.text || "New requirement"}</del></p>}
          <h4>{item.text}</h4>
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
        </section>))}
      </>}
    </details>
    <details className="document-section" id="preview-stories" open>
      <summary>
        User stories and acceptance criteria ({value.stories.length})
      </summary>
      {renderSectionEditor?.("stories") ?? <>
        {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection("stories")}>Edit stories and criteria</button>}
        {value.stories.map((story) => (<section className={original && JSON.stringify(original.stories.find(s => s.id === story.id)) !== JSON.stringify(story) ? "statement amendment-highlight" : "statement"} key={story.id} id={`read-${story.id}`} tabIndex={-1}>
          <h4>{story.text}</h4>
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
        </section>))}
      </>}
    </details>
    <details className="document-section" id="preview-questions" open>
      <summary>Open questions ({value.open_questions.length})</summary>
      {renderSectionEditor?.("open_questions") ?? <>
        {onEditSection && <button type="button" className="secondary" onClick={() => onEditSection("open_questions")}>Edit question list</button>}
        {value.open_questions.length ? (<ul>
          {value.open_questions.map((question, i) => (<li key={i}>{question}</li>))}
        </ul>) : (<p>None supplied.</p>)}
      </>}
    </details>
  </article>);
}
