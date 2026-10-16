# Output contract

Return only one JSON Artifact matching the supplied schema: no prose fences, extra fields or execution instructions. Use only actual selected source IDs in the response. The example IDs below are illustrative, never evidence for a real response.

## Required story structure

Every object in stories must include all six fields: id, text, source_ids, kind, requirement_ids, acceptance_criteria. Do not omit id when another story looks similar or describes a competing option. Assign distinct STORY-1, STORY-2, ... values; requirement_ids contains REQ identifiers, never the story's own identifier. Each requirement object likewise needs its own distinct REQ id. Use the supplied schema for field types and bounds; do not introduce a status, approval or conflict field.

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

- user_provided: text is an exact substring of every cited source, with no inserted lead-in, persona, inferred benefit or quotation marks. Include the supporting source IDs. Preserve case and punctuation exactly, including sentence fragments: adding an article, capitalizing a fragment or replacing a semicolon with a period makes the text a paraphrase. A paraphrase must use a proposal/assumption label instead, even if reasonable.
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

## Conflicting alternatives

Keep each supplied alternative and cite its own source. Explain the incompatibility in risks or dependencies, then ask which source/policy is authoritative. Lack of approval belongs in dependencies/questions, not in non_goals. Do not invent a compromise, decision-maker, consensus or priority.

For an unresolved alternative, make the story wording conditional on human selection and start every applicable acceptance criterion with that selection as a precondition. An unconditional pair of incompatible acceptance criteria can mislead developers even when a question elsewhere acknowledges the conflict. Describe only what the supplied alternative implies; a proposal for an unstated precondition must be explicitly provisional. Check risk direction: satisfying an incompatible alternative may leave the other unmet.

Illustrative sources (unrelated to the user's feature):
- example-immediate: "Settings changes take effect immediately."
- example-approval: "Settings changes take effect only after an administrator approves them."

Complete illustrative Artifact; both alternatives remain candidates, and neither is approved:

```json
{"title":"Settings activation decision","purpose":"Document the unresolved activation policy.","scope":[{"text":"Settings activation has two competing requests.","source_ids":["example-immediate","example-approval"],"kind":"recommendation"}],"non_goals":[],"requirements":[{"id":"REQ-1","text":"Settings changes take effect immediately.","source_ids":["example-immediate"],"kind":"user_provided"},{"id":"REQ-2","text":"Settings changes take effect only after an administrator approves them.","source_ids":["example-approval"],"kind":"user_provided"}],"stories":[{"id":"STORY-1","text":"If a human selects the immediate policy, an operator can change a setting with immediate effect.","source_ids":["example-immediate"],"kind":"recommendation","requirement_ids":["REQ-1"],"acceptance_criteria":["Given a human has selected the immediate policy, when a setting is changed, then that setting takes effect immediately."]},{"id":"STORY-2","text":"If a human selects the approval policy, an operator can change a setting subject to administrator approval.","source_ids":["example-approval"],"kind":"recommendation","requirement_ids":["REQ-2"],"acceptance_criteria":["Given a human has selected the approval policy, when a setting is changed before administrator approval, then the change is not yet in effect.","Given a human has selected the approval policy, when an administrator approves that setting change, then it takes effect."]}],"edge_cases":[],"dependencies":[{"text":"The activation policy is unresolved.","source_ids":["example-immediate","example-approval"],"kind":"unknown"}],"risks":[{"text":"Immediate activation would fail the approval-only request; approval-only activation would fail the immediate request.","source_ids":["example-immediate","example-approval"],"kind":"recommendation"}],"success_metrics":[],"open_questions":["Which activation policy should a human select: immediate effect or administrator approval?","Who has authority to select the policy?"]}
```

Do not reuse these illustrative source IDs or behaviors. Generate the actual feature's identifiers and content from its selected evidence.

## Source-gap checklist: build open_questions before stories

First identify the missing decisions, then draft stories without silently resolving them. Include a specific question for EVERY applicable row below; merely asking which policy wins or who decides does not replace the implementation-detail questions. These rows are conditional on the actual sources, not reasons to add unrelated scope.

| Evidence in selected sources | Required unresolved question(s) |
| --- | --- |
| A time duration or recovery/retention window without complete boundary rules | Ask how the interval is measured (time basis), whether its exact endpoint is inclusive/exclusive, and what behavior is required after the window. Do not infer expiry, purge or denial. |
| One competing draft contains an obligation that the other does not mention | Ask explicitly whether that obligation still applies if the other draft is chosen. Do not transfer the obligation automatically. |
| Response metadata for pagination or continuation, without request mechanics | Ask how the client supplies continuation information in the next request. A response field does not establish a request parameter or termination convention. |
| A feature policy or prerequisite not supplied | Ask the consequential decision. Do not require an invented lifecycle stage, payment/account policy, limit, owner or date. |

Criteria must observe the requested downstream outcome, not merely a control changing or a preference being stored. For enable/disable controls, cover the effect on the operation as well as persistence. Preserve stated exceptions in every section. Cross-check proposed unknowns against the supplied facts: do not call an explicitly requested behavior unspecified.

A recommendation label permits a proposal, not a silent decision. Keep unknown mechanics outside settled criteria and make conditional criteria honest about unresolved prerequisites. Open questions must expose what blocks implementation, without fabricating answers or authorizing a choice.

## Final check before responding

1. Inspect every stories[i] object for all six required fields, particularly id. Story IDs are unique STORY identifiers; requirement IDs are unique REQ identifiers. Every story points only to requirements in this response.
2. Every requirement appears in at least one story's requirement_ids. Mentioning its behavior only in acceptance-criteria text is insufficient. If criteria cover headers and export, link both requirement IDs.
3. Each linked requirement has an observable criterion; criteria do not declare an unresolved permission policy or numerical limit to be settled.
4. Each user_provided text matches an exact excerpt in every cited source. Every added clause changes that statement's evidence classification.
5. Missing motivations are omitted; unknowns are questions, not invented facts or unknown commitments. For conflicts, preserve both sources and ask the unresolved decision. Each alternative story and each criterion must be conditional on that human choice; check that risks describe the correct consequence.
6. Revisit EVERY applicable source-gap checklist row. Verify open_questions actually contains its specific missing decisions, including each temporal boundary/time basis/post-window question and each alternative-obligation applicability question when relevant. Do not stop at policy choice/authority questions. Verify downstream outcome criteria and remove contradictions with supplied facts.
7. Return the complete JSON artifact for human review. No text or output grants publication authority.
