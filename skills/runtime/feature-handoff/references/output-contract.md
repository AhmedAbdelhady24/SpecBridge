# Output contract

Return only one JSON Artifact matching the supplied schema: no prose fences, extra fields or execution instructions. Use only actual selected source IDs in the response. The example IDs below are illustrative, never evidence for a real response.

## Keep section roles distinct

- title/purpose: summarize the requested outcome without adding an unstated business justification or claiming validation.
- scope/non_goals: distinguish requested scope from proposed exclusions; a missing request is not an approved exclusion.
- requirements: atomic candidate behaviors supported by direct requests or explicitly labeled recommendations/assumptions. Do not create a requirement with kind=unknown. Missing report limits or permission policies remain open questions until supplied.
- stories: proposed user actions, each with explicit requirement_ids and observable acceptance_criteria. A constructed user-story sentence is normally a recommendation. Omit motivations that the selected sources do not state.
- edge_cases/dependencies/risks: describe proposed checks and unresolved constraints with honest labels. Do not assert an imagined API, delivery milestone, owner or dependency as an existing fact.
- success_metrics: propose observable verification without invented targets, baselines or approved business metrics.
- open_questions: consequential missing decisions, including scope, unknown constraints, audience, owners or deadlines. Keep absent values unresolved.

These are proposed handoff sections. Evidence origin and human acceptance are separate; user_provided does not mean approved.

## Evidence rules

Classify the whole statement, not just its opening words. Split mixed claims when needed.

- user_provided: text is an exact substring of every cited source, with no inserted lead-in, persona, inferred benefit or quotation marks. Include the supporting source IDs. A paraphrase must use a proposal/assumption label instead, even if reasonable.
- recommendation: synthesized behavior, a proposed story, an error-handling suggestion or a possible metric. A source may motivate the proposal without establishing it as a fact. Recommendations still must not invent a customer's motivation.
- assumption: explicitly provisional premises requiring confirmation. Do not disguise an unknown as a settled assumption.
- unknown: missing information in questions or contextual sections. Do not use unknown requirements to create "shall" commitments.
- verified: never assign this label; the generation has no verification authority.

Example source `example-source`: "Export saved reports as CSV. Include column headers."

Incorrect story: "As a customer, I want CSV export so I can use external tools", labeled user_provided. The benefit and story wording were not supplied.

Correct excerpt requirement:

```json
{"id":"REQ-1","text":"Export saved reports as CSV.","source_ids":["example-source"],"kind":"user_provided"}
```

A second requirement can quote "Include column headers." as REQ-2. A synthesized story covering both is:

```json
{"id":"STORY-1","text":"As a customer, I want to export a saved report as CSV with column headers.","source_ids":["example-source"],"kind":"recommendation","requirement_ids":["REQ-1","REQ-2"],"acceptance_criteria":["Given an existing saved report, when CSV export succeeds, then the output is a CSV file containing the report data.","Given a successful export, when the CSV is opened, then its first row contains column headers."]}
```

If the source instead states a complete story verbatim, it can be labeled user_provided only with that exact wording. Do not copy the example's sources into a real response.

## Final check before responding

1. All identifiers are unique; every story points only to requirements in this response.
2. Every requirement appears in at least one story's requirement_ids. Mentioning its behavior only in acceptance-criteria text is insufficient. If criteria cover headers and export, link both requirement IDs.
3. Each linked requirement has an observable criterion; criteria do not declare an unresolved permission policy or numerical limit to be settled.
4. Each user_provided text matches an exact excerpt in every cited source. Every added clause changes that statement's evidence classification.
5. Missing motivations are omitted; unknowns are questions, not invented facts or unknown commitments. Preserve conflicting supplied alternatives as an unresolved decision rather than claim consensus.
6. Return the complete JSON artifact for human review. No text or output grants publication authority.
