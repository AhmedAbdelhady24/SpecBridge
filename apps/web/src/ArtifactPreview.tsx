import type { components } from "./api/schema";
type Artifact = components["schemas"]["Artifact"];
type Statement = components["schemas"]["Statement"];

function Evidence({ item }: { item: Statement }) {
  return (
    <>
      <span className="evidence-badge">{item.kind.replaceAll("_", " ")}</span>
      <details className="item-provenance">
        <summary>Source references</summary>
        <p>{(item.source_ids ?? []).join(", ") || "No source supplied"}</p>
      </details>
    </>
  );
}

export function ArtifactPreview({ value }: { value: Artifact }) {
  const sections = [
    ["scope", "Scope"],
    ["non_goals", "Non-goals"],
    ["edge_cases", "Edge cases"],
    ["dependencies", "Dependencies"],
    ["risks", "Risks"],
    ["success_metrics", "Proposed success metrics"],
  ] as const;
  return (
    <article className="artifact-preview" aria-label="Readable draft">
      <h3>{value.title}</h3>
      <p>{value.purpose}</p>
      <p className="review-caveat">Human review required</p>
      <nav aria-label="Document sections" className="document-outline">
        <a href="#preview-scope">Scope</a>
        <a href="#preview-requirements">Requirements</a>
        <a href="#preview-stories">Stories and criteria</a>
        <a href="#preview-questions">Open questions</a>
      </nav>
      {sections.map(([key, title]) => (
        <details
          className="document-section"
          key={key}
          id={`preview-${key}`}
          open={key === "scope"}
        >
          <summary>
            {title} ({value[key].length})
          </summary>
          {!value[key].length && <p>None supplied.</p>}
          {value[key].map((item, i) => (
            <div className="statement" key={i}>
              <p>{item.text}</p>
              <Evidence item={item} />
            </div>
          ))}
        </details>
      ))}
      <details className="document-section" id="preview-requirements" open>
        <summary>Requirements ({value.requirements.length})</summary>
        {value.requirements.map((item) => (
          <section className="statement" key={item.id} id={`read-${item.id}`}>
            <h4>{item.text}</h4>
            <code>{item.id}</code>
            <div className="evidence-line">
              <Evidence item={item} />
            </div>
            <p>
              Stories:{" "}
              {value.stories
                .filter((story) => story.requirement_ids.includes(item.id))
                .map((story) => (
                  <a key={story.id} href={`#read-${story.id}`}>
                    {story.id}{" "}
                  </a>
                ))}
            </p>
          </section>
        ))}
      </details>
      <details className="document-section" id="preview-stories" open>
        <summary>
          User stories and acceptance criteria ({value.stories.length})
        </summary>
        {value.stories.map((story) => (
          <section className="statement" key={story.id} id={`read-${story.id}`}>
            <h4>{story.text}</h4>
            <code>{story.id}</code>
            <div className="evidence-line">
              <Evidence item={story} />
            </div>
            <p>
              Requirements:{" "}
              {story.requirement_ids.map((id) => (
                <a key={id} href={`#read-${id}`}>
                  {id}{" "}
                </a>
              ))}
            </p>
            <ul>
              {story.acceptance_criteria.map((criterion, i) => (
                <li key={i}>{criterion}</li>
              ))}
            </ul>
          </section>
        ))}
      </details>
      <details className="document-section" id="preview-questions" open>
        <summary>Open questions ({value.open_questions.length})</summary>
        {value.open_questions.length ? (
          <ul>
            {value.open_questions.map((question, i) => (
              <li key={i}>{question}</li>
            ))}
          </ul>
        ) : (
          <p>None supplied.</p>
        )}
      </details>
    </article>
  );
}
